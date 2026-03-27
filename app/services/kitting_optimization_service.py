# -*- coding: utf-8 -*-
"""
齐套率优化服务层
实现催货、替代料推荐、安全库存预警、改进建议的业务逻辑
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, case, desc, func, or_
from sqlalchemy.orm import Session

from app.models.inventory_tracking import MaterialStock, MaterialTransaction
from app.models.kitting_optimization import ExpediteRecord, MaterialAlternative
from app.models.material import (
    BomItem,
    Material,
    MaterialCategory,
    MaterialShortage,
    MaterialSupplier,
)
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)


class KittingOptimizationService:
    """齐套率优化服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 1. 缺料自动催货 ====================

    def detect_high_risk_shortages(
        self, project_id: Optional[int] = None
    ) -> List[MaterialShortage]:
        """自动识别高风险缺料（影响装配/调试的关键物料）"""
        query = self.db.query(MaterialShortage).filter(
            MaterialShortage.status.in_(["OPEN", "IN_PROGRESS"]),
        )
        if project_id:
            query = query.filter(MaterialShortage.project_id == project_id)

        # 优先级：关键物料 + 需求日期临近
        shortages = query.all()
        high_risk = []
        today = date.today()

        for s in shortages:
            material = self.db.query(Material).get(s.material_id)
            if not material:
                continue

            is_high_risk = False
            # 关键物料缺料
            if material.is_key_material:
                is_high_risk = True
            # 需求日期在 7 天内
            if s.required_date and (s.required_date - today).days <= 7:
                is_high_risk = True
            # 严重缺料（缺料比例超过 50%）
            if s.required_qty and s.shortage_qty:
                shortage_ratio = float(s.shortage_qty) / float(s.required_qty)
                if shortage_ratio > 0.5:
                    is_high_risk = True

            if is_high_risk:
                high_risk.append(s)

        return high_risk

    def create_expedite_records(
        self,
        targets: List[Dict[str, Any]],
        notify_methods: List[str],
        auto_high_risk: List[MaterialShortage],
        user_id: int,
    ) -> List[ExpediteRecord]:
        """批量创建催货记录"""
        records = []

        # 处理手动指定的催货目标
        for target in targets:
            material = self.db.query(Material).get(target["material_id"])
            if not material:
                continue

            record = self._build_expedite_record(
                material=material,
                shortage_id=target.get("shortage_id"),
                purchase_order_id=target.get("purchase_order_id"),
                urgency_level=target.get("urgency_level", "NORMAL"),
                notify_methods=notify_methods,
                remark=target.get("remark"),
                user_id=user_id,
                expedite_type="MANUAL",
            )
            if record:
                records.append(record)

        # 处理自动识别的高风险缺料
        for shortage in auto_high_risk:
            # 避免重复催货：检查近 3 天内是否已催过
            recent = (
                self.db.query(ExpediteRecord)
                .filter(
                    ExpediteRecord.material_id == shortage.material_id,
                    ExpediteRecord.shortage_id == shortage.id,
                    ExpediteRecord.created_at >= datetime.now() - timedelta(days=3),
                )
                .first()
            )
            if recent:
                continue

            material = self.db.query(Material).get(shortage.material_id)
            if not material:
                continue

            record = self._build_expedite_record(
                material=material,
                shortage_id=shortage.id,
                purchase_order_id=None,
                urgency_level="HIGH",
                notify_methods=notify_methods,
                remark=f"系统自动识别高风险缺料，缺料数量: {shortage.shortage_qty}",
                user_id=user_id,
                expedite_type="AUTO",
                project_id=shortage.project_id,
                shortage_qty=shortage.shortage_qty,
                required_date=shortage.required_date,
            )
            if record:
                records.append(record)

        # 批量保存
        for record in records:
            self.db.add(record)
        self.db.flush()

        # 生成通知内容（先存记录，后续对接消息系统）
        for record in records:
            record.notify_content = self._generate_notify_content(record)
            record.notify_status = "PENDING"
        self.db.commit()

        return records

    def _build_expedite_record(
        self,
        material: Material,
        shortage_id: Optional[int],
        purchase_order_id: Optional[int],
        urgency_level: str,
        notify_methods: List[str],
        remark: Optional[str],
        user_id: int,
        expedite_type: str = "MANUAL",
        project_id: Optional[int] = None,
        shortage_qty=None,
        required_date=None,
    ) -> Optional[ExpediteRecord]:
        """构建单条催货记录"""
        # 查找关联的采购订单和供应商
        supplier_id = material.default_supplier_id
        promised_date = None

        if purchase_order_id:
            po = self.db.query(PurchaseOrder).get(purchase_order_id)
            if po:
                supplier_id = po.supplier_id
                promised_date = po.promised_date
                if not project_id:
                    project_id = po.project_id
        elif not supplier_id:
            # 从物料供应商关系中找首选供应商
            ms = (
                self.db.query(MaterialSupplier)
                .filter(
                    MaterialSupplier.material_id == material.id,
                    MaterialSupplier.is_active == True,
                )
                .order_by(desc(MaterialSupplier.is_preferred))
                .first()
            )
            if ms:
                supplier_id = ms.supplier_id

        notify_method = "MULTI" if len(notify_methods) > 1 else notify_methods[0]

        return ExpediteRecord(
            material_id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            shortage_id=shortage_id,
            purchase_order_id=purchase_order_id,
            supplier_id=supplier_id,
            project_id=project_id,
            expedite_type=expedite_type,
            urgency_level=urgency_level,
            shortage_qty=shortage_qty,
            required_date=required_date,
            original_promised_date=promised_date,
            notify_method=notify_method,
            status="PENDING",
            created_by=user_id,
            remark=remark,
        )

    def _generate_notify_content(self, record: ExpediteRecord) -> str:
        """生成催货通知内容"""
        urgency_map = {
            "CRITICAL": "【紧急】",
            "HIGH": "【高优先级】",
            "NORMAL": "",
            "LOW": "",
        }
        prefix = urgency_map.get(record.urgency_level, "")

        lines = [
            f"{prefix}催货通知",
            f"物料编码: {record.material_code}",
            f"物料名称: {record.material_name}",
        ]
        if record.shortage_qty:
            lines.append(f"缺料数量: {record.shortage_qty}")
        if record.required_date:
            lines.append(f"需求日期: {record.required_date}")
        if record.original_promised_date:
            lines.append(f"原承诺交期: {record.original_promised_date}")
        lines.append("请尽快确认交期并安排发货，谢谢！")

        return "\n".join(lines)

    def get_expedite_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """催货效果统计"""
        query = self.db.query(ExpediteRecord)
        if start_date:
            query = query.filter(ExpediteRecord.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(ExpediteRecord.created_at <= datetime.combine(end_date, datetime.max.time()))

        total = query.count()
        resolved = query.filter(ExpediteRecord.status == "RESOLVED").count()

        # 催后准时率
        delivered = query.filter(ExpediteRecord.actual_delivery_date.isnot(None)).all()
        on_time_count = sum(1 for r in delivered if r.is_on_time)
        on_time_rate = (on_time_count / len(delivered) * 100) if delivered else 0

        # 平均响应天数
        responded = [
            r for r in query.filter(ExpediteRecord.response_at.isnot(None)).all()
            if r.created_at
        ]
        avg_response_days = None
        if responded:
            total_days = sum(
                (r.response_at - r.created_at).days for r in responded
            )
            avg_response_days = round(total_days / len(responded), 1)

        # 按紧急程度统计
        by_urgency = {}
        for level in ["CRITICAL", "HIGH", "NORMAL", "LOW"]:
            by_urgency[level] = query.filter(ExpediteRecord.urgency_level == level).count()

        # 按供应商统计 TOP10
        supplier_stats = (
            self.db.query(
                ExpediteRecord.supplier_id,
                func.count(ExpediteRecord.id).label("expedite_count"),
            )
            .filter(ExpediteRecord.supplier_id.isnot(None))
            .group_by(ExpediteRecord.supplier_id)
            .order_by(desc("expedite_count"))
            .limit(10)
            .all()
        )
        by_supplier = []
        for supplier_id, count in supplier_stats:
            vendor = self.db.query(Vendor).get(supplier_id)
            by_supplier.append({
                "supplier_id": supplier_id,
                "supplier_name": vendor.supplier_name if vendor else "未知",
                "expedite_count": count,
            })

        return {
            "total_expedited": total,
            "resolved_count": resolved,
            "on_time_count": on_time_count,
            "on_time_rate": round(on_time_rate, 1),
            "avg_response_days": avg_response_days,
            "by_urgency": by_urgency,
            "by_supplier": by_supplier,
        }

    # ==================== 2. 替代料推荐 ====================

    def get_alternatives(
        self,
        material_id: int,
        include_unverified: bool = True,
    ) -> Dict[str, Any]:
        """获取物料的替代料推荐（已登记 + 自动匹配）"""
        material = self.db.query(Material).get(material_id)
        if not material:
            return {"error": "物料不存在"}

        alternatives = []

        # 1. 已登记的替代料关系
        registered = (
            self.db.query(MaterialAlternative)
            .filter(
                MaterialAlternative.original_material_id == material_id,
                MaterialAlternative.is_active == True,
            )
            .order_by(desc(MaterialAlternative.match_score))
            .all()
        )
        registered_ids = set()
        for alt in registered:
            if not include_unverified and not alt.is_verified:
                continue
            alt_material = self.db.query(Material).get(alt.alternative_material_id)
            if not alt_material or not alt_material.is_active:
                continue
            registered_ids.add(alt.alternative_material_id)
            alternatives.append(
                self._build_alternative_response(material, alt_material, alt)
            )

        # 2. 基于规格参数自动匹配（同分类 + 相似规格）
        if material.category_id and material.specification:
            auto_matches = (
                self.db.query(Material)
                .filter(
                    Material.category_id == material.category_id,
                    Material.id != material_id,
                    Material.id.notin_(registered_ids),
                    Material.is_active == True,
                )
                .limit(20)
                .all()
            )
            for alt_mat in auto_matches:
                score = self._calculate_match_score(material, alt_mat)
                if score >= 40:  # 匹配度 >= 40% 才推荐
                    alternatives.append(
                        self._build_alternative_response(
                            material, alt_mat, None, auto_score=score
                        )
                    )

        # 按匹配度排序
        alternatives.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "original_material_id": material.id,
            "original_material_code": material.material_code,
            "original_material_name": material.material_name,
            "original_specification": material.specification,
            "alternatives": alternatives[:20],
            "total": len(alternatives[:20]),
        }

    def _build_alternative_response(
        self,
        original: Material,
        alt_material: Material,
        alt_record: Optional[MaterialAlternative],
        auto_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """构建替代料响应数据"""
        # 库存查询
        stock_sum = (
            self.db.query(func.sum(MaterialStock.available_quantity))
            .filter(MaterialStock.material_id == alt_material.id)
            .scalar()
        ) or 0

        total_stock = (
            self.db.query(func.sum(MaterialStock.quantity))
            .filter(MaterialStock.material_id == alt_material.id)
            .scalar()
        ) or 0

        # 供应商数量
        supplier_count = (
            self.db.query(MaterialSupplier)
            .filter(
                MaterialSupplier.material_id == alt_material.id,
                MaterialSupplier.is_active == True,
            )
            .count()
        )

        # 价格对比
        original_price = float(original.last_price or original.standard_price or 0)
        alt_price = float(alt_material.last_price or alt_material.standard_price or 0)
        price_diff_pct = None
        if original_price > 0:
            price_diff_pct = round((alt_price - original_price) / original_price * 100, 1)

        result = {
            "id": alt_record.id if alt_record else 0,
            "alternative_material_id": alt_material.id,
            "material_code": alt_material.material_code,
            "material_name": alt_material.material_name,
            "specification": alt_material.specification,
            "brand": alt_material.brand,
            "unit": alt_material.unit,
            "match_score": float(alt_record.match_score) if alt_record else (auto_score or 0),
            "match_reason": alt_record.match_reason if alt_record else "系统自动匹配(同分类+规格相似)",
            "is_verified": alt_record.is_verified if alt_record else False,
            "current_stock": float(total_stock),
            "available_stock": float(stock_sum),
            "original_price": original_price if original_price else None,
            "alternative_price": alt_price if alt_price else None,
            "price_diff_pct": price_diff_pct,
            "supplier_count": supplier_count,
            "lead_time_days": alt_material.lead_time_days,
            "ecn_no": alt_record.ecn_no if alt_record else None,
            "ecn_status": alt_record.ecn_status if alt_record else None,
        }
        return result

    def _calculate_match_score(self, original: Material, candidate: Material) -> float:
        """基于规格参数计算匹配度"""
        score = 0.0

        # 同分类 +20
        if original.category_id == candidate.category_id:
            score += 20

        # 规格相似度
        if original.specification and candidate.specification:
            orig_spec = original.specification.lower()
            cand_spec = candidate.specification.lower()
            # 简单包含关系
            if orig_spec == cand_spec:
                score += 40
            elif orig_spec in cand_spec or cand_spec in orig_spec:
                score += 25
            else:
                # 分词匹配
                orig_tokens = set(orig_spec.replace("/", " ").replace("-", " ").split())
                cand_tokens = set(cand_spec.replace("/", " ").replace("-", " ").split())
                if orig_tokens and cand_tokens:
                    overlap = len(orig_tokens & cand_tokens)
                    total = len(orig_tokens | cand_tokens)
                    score += (overlap / total) * 30 if total > 0 else 0

        # 同品牌 +15
        if original.brand and candidate.brand:
            if original.brand.lower() == candidate.brand.lower():
                score += 15

        # 同单位 +5
        if original.unit == candidate.unit:
            score += 5

        # 有库存 +10
        if candidate.current_stock and float(candidate.current_stock) > 0:
            score += 10

        # 价格在合理范围内(±30%) +10
        orig_price = float(original.last_price or original.standard_price or 0)
        cand_price = float(candidate.last_price or candidate.standard_price or 0)
        if orig_price > 0 and cand_price > 0:
            diff = abs(cand_price - orig_price) / orig_price
            if diff <= 0.3:
                score += 10

        return min(score, 100)

    # ==================== 3. 安全库存预警 ====================

    def get_safety_stock_alerts(
        self,
        alert_level: Optional[str] = None,
        category_id: Optional[int] = None,
        only_key_materials: bool = False,
    ) -> Dict[str, Any]:
        """获取安全库存预警列表"""
        query = self.db.query(Material).filter(
            Material.is_active == True,
            Material.safety_stock > 0,
        )
        if only_key_materials:
            query = query.filter(Material.is_key_material == True)
        if category_id:
            query = query.filter(Material.category_id == category_id)

        materials = query.all()
        alerts = []
        today = date.today()

        for mat in materials:
            current_stock = float(mat.current_stock or 0)
            safety_stock = float(mat.safety_stock or 0)

            if current_stock >= safety_stock:
                continue  # 库存充足，不预警

            gap = safety_stock - current_stock
            gap_pct = (gap / safety_stock * 100) if safety_stock > 0 else 0

            # 计算日均消耗（最近90天出库量）
            ninety_days_ago = datetime.now() - timedelta(days=90)
            consumption = (
                self.db.query(func.sum(MaterialTransaction.quantity))
                .filter(
                    MaterialTransaction.material_id == mat.id,
                    MaterialTransaction.transaction_type == "ISSUE",
                    MaterialTransaction.transaction_date >= ninety_days_ago,
                )
                .scalar()
            ) or 0
            avg_daily = float(consumption) / 90 if consumption else 0

            # 可供天数
            days_of_supply = None
            estimated_stockout = None
            if avg_daily > 0:
                days_of_supply = round(current_stock / avg_daily, 1)
                estimated_stockout = today + timedelta(days=int(days_of_supply))

            # 建议补货数量 = 安全库存 + 采购周期内消耗 - 当前库存
            lead_time = mat.lead_time_days or 0
            lt_consumption = avg_daily * lead_time
            suggested_reorder = max(safety_stock + lt_consumption - current_stock, 0)
            # 取最小订购量的整数倍
            moq = float(mat.min_order_qty or 1)
            if moq > 0 and suggested_reorder > 0:
                import math
                suggested_reorder = math.ceil(suggested_reorder / moq) * moq

            # 补货点 = 安全库存 + 采购周期内消耗
            reorder_point = safety_stock + lt_consumption

            # 高频缺料检查（近90天缺料次数）
            shortage_count = (
                self.db.query(MaterialShortage)
                .filter(
                    MaterialShortage.material_id == mat.id,
                    MaterialShortage.created_at >= ninety_days_ago,
                )
                .count()
            )

            # 预警级别
            if gap_pct >= 80 or (days_of_supply is not None and days_of_supply <= 3):
                level = "CRITICAL"
            elif gap_pct >= 50 or (days_of_supply is not None and days_of_supply <= 7):
                level = "WARNING"
            else:
                level = "INFO"

            if alert_level and level != alert_level:
                continue

            # 分类名称
            category_name = None
            if mat.category_id:
                cat = self.db.query(MaterialCategory).get(mat.category_id)
                if cat:
                    category_name = cat.category_name

            alerts.append({
                "material_id": mat.id,
                "material_code": mat.material_code,
                "material_name": mat.material_name,
                "specification": mat.specification,
                "category_name": category_name,
                "is_key_material": mat.is_key_material or False,
                "current_stock": current_stock,
                "safety_stock": safety_stock,
                "gap": round(gap, 2),
                "gap_pct": round(gap_pct, 1),
                "avg_daily_consumption": round(avg_daily, 4),
                "days_of_supply": days_of_supply,
                "lead_time_days": lead_time,
                "suggested_reorder_qty": round(suggested_reorder, 2),
                "reorder_point": round(reorder_point, 2),
                "estimated_stockout_date": estimated_stockout,
                "alert_level": level,
                "is_high_frequency_shortage": shortage_count >= 3,
                "shortage_count_90d": shortage_count,
            })

        # 按预警级别排序: CRITICAL > WARNING > INFO
        level_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        alerts.sort(key=lambda x: (level_order.get(x["alert_level"], 9), -x["gap_pct"]))

        critical_count = sum(1 for a in alerts if a["alert_level"] == "CRITICAL")
        warning_count = sum(1 for a in alerts if a["alert_level"] == "WARNING")

        return {
            "alerts": alerts,
            "total": len(alerts),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "summary": {
                "total_materials_monitored": len(materials),
                "below_safety_stock": len(alerts),
                "high_frequency_shortage_count": sum(
                    1 for a in alerts if a["is_high_frequency_shortage"]
                ),
            },
        }

    # ==================== 4. 齐套率改进建议 ====================

    def get_improvement_suggestions(
        self, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """生成齐套率改进建议"""
        return {
            "bottleneck_materials": self._get_bottleneck_materials(project_id),
            "supplier_analysis": self._get_supplier_delivery_analysis(),
            "pre_purchase_materials": self._get_pre_purchase_suggestions(),
            "common_stock_materials": self._get_common_stock_suggestions(),
            "improvement_target": self._get_improvement_target(project_id),
            "generated_at": datetime.now(),
        }

    def _get_bottleneck_materials(
        self, project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """瓶颈物料 TOP10（频繁缺料）"""
        query = self.db.query(
            MaterialShortage.material_id,
            MaterialShortage.material_code,
            MaterialShortage.material_name,
            func.count(MaterialShortage.id).label("shortage_count"),
            func.sum(MaterialShortage.shortage_qty).label("total_shortage_qty"),
            func.count(func.distinct(MaterialShortage.project_id)).label("affected_projects"),
        )
        if project_id:
            query = query.filter(MaterialShortage.project_id == project_id)

        # 最近 180 天
        cutoff = datetime.now() - timedelta(days=180)
        query = query.filter(MaterialShortage.created_at >= cutoff)

        results = (
            query.group_by(
                MaterialShortage.material_id,
                MaterialShortage.material_code,
                MaterialShortage.material_name,
            )
            .order_by(desc("shortage_count"))
            .limit(10)
            .all()
        )

        bottlenecks = []
        for r in results:
            # 计算平均延迟天数（从 required_date 到 actual_arrival_date）
            delays = (
                self.db.query(MaterialShortage)
                .filter(
                    MaterialShortage.material_id == r.material_id,
                    MaterialShortage.actual_arrival_date.isnot(None),
                    MaterialShortage.required_date.isnot(None),
                )
                .all()
            )
            avg_delay = None
            if delays:
                total_delay = sum(
                    max((d.actual_arrival_date - d.required_date).days, 0)
                    for d in delays
                )
                avg_delay = round(total_delay / len(delays), 1)

            # 生成建议
            suggestion = self._generate_bottleneck_suggestion(
                r.shortage_count, avg_delay, r.material_code
            )

            bottlenecks.append({
                "material_id": r.material_id,
                "material_code": r.material_code,
                "material_name": r.material_name,
                "shortage_count": r.shortage_count,
                "total_shortage_qty": float(r.total_shortage_qty or 0),
                "avg_delay_days": avg_delay,
                "affected_projects": r.affected_projects,
                "suggestion": suggestion,
            })

        return bottlenecks

    def _generate_bottleneck_suggestion(
        self, shortage_count: int, avg_delay: Optional[float], material_code: str
    ) -> str:
        """生成瓶颈物料改进建议"""
        suggestions = []
        if shortage_count >= 5:
            suggestions.append("建议设置更高的安全库存水位")
        if avg_delay and avg_delay > 7:
            suggestions.append("建议评估替代供应商或替代料")
        if shortage_count >= 3:
            suggestions.append("建议纳入提前采购清单")
        suggestions.append("建议与供应商签订框架协议确保供应")
        return "；".join(suggestions)

    def _get_supplier_delivery_analysis(self) -> List[Dict[str, Any]]:
        """供应商交期分析"""
        # 查询有收货记录的供应商
        six_months_ago = datetime.now() - timedelta(days=180)

        suppliers = (
            self.db.query(
                PurchaseOrder.supplier_id,
                func.count(PurchaseOrderItem.id).label("total_orders"),
            )
            .join(PurchaseOrderItem, PurchaseOrder.id == PurchaseOrderItem.order_id)
            .filter(
                PurchaseOrder.status.in_(["APPROVED", "COMPLETED", "CLOSED"]),
                PurchaseOrder.order_date >= six_months_ago.date(),
            )
            .group_by(PurchaseOrder.supplier_id)
            .all()
        )

        results = []
        for supplier_id, total_orders in suppliers:
            vendor = self.db.query(Vendor).get(supplier_id)
            if not vendor:
                continue

            # 查询该供应商的PO明细和收货情况
            po_items = (
                self.db.query(PurchaseOrderItem)
                .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
                .filter(
                    PurchaseOrder.supplier_id == supplier_id,
                    PurchaseOrder.order_date >= six_months_ago.date(),
                    PurchaseOrderItem.required_date.isnot(None),
                )
                .all()
            )

            on_time = 0
            delayed = 0
            delay_days_list = []

            for item in po_items:
                # 查找对应的收货记录
                receipt_item = (
                    self.db.query(GoodsReceiptItem)
                    .join(GoodsReceipt, GoodsReceipt.id == GoodsReceiptItem.receipt_id)
                    .filter(GoodsReceiptItem.order_item_id == item.id)
                    .first()
                )
                if receipt_item and receipt_item.receipt:
                    actual_date = receipt_item.receipt.receipt_date
                    if actual_date and item.required_date:
                        diff = (actual_date - item.required_date).days
                        if diff <= 0:
                            on_time += 1
                        else:
                            delayed += 1
                            delay_days_list.append(diff)

            evaluated = on_time + delayed
            if evaluated == 0:
                continue

            on_time_rate = round(on_time / evaluated * 100, 1)
            avg_delay = round(sum(delay_days_list) / len(delay_days_list), 1) if delay_days_list else 0
            max_delay = max(delay_days_list) if delay_days_list else 0

            # 风险等级
            if on_time_rate < 60:
                risk_level = "HIGH"
                suggestion = "建议与该供应商进行交期改善会议，或评估备选供应商"
            elif on_time_rate < 80:
                risk_level = "MEDIUM"
                suggestion = "建议加强订单跟踪，提前催货确认交期"
            else:
                risk_level = "LOW"
                suggestion = "交期表现良好，建议保持合作"

            results.append({
                "supplier_id": supplier_id,
                "supplier_name": vendor.supplier_name,
                "total_orders": evaluated,
                "on_time_count": on_time,
                "delayed_count": delayed,
                "on_time_rate": on_time_rate,
                "avg_delay_days": avg_delay,
                "max_delay_days": max_delay,
                "risk_level": risk_level,
                "suggestion": suggestion,
            })

        # 按准时率升序（最差的排前面）
        results.sort(key=lambda x: x["on_time_rate"])
        return results[:15]

    def _get_pre_purchase_suggestions(self) -> List[Dict[str, Any]]:
        """建议提前采购的物料"""
        # 选择：采购周期长(>14天) + 有消耗记录 + 非充足库存
        materials = (
            self.db.query(Material)
            .filter(
                Material.is_active == True,
                Material.lead_time_days > 14,
            )
            .all()
        )

        suggestions = []
        today = date.today()
        ninety_days_ago = datetime.now() - timedelta(days=90)

        for mat in materials:
            # 月均消耗
            consumption_90d = (
                self.db.query(func.sum(MaterialTransaction.quantity))
                .filter(
                    MaterialTransaction.material_id == mat.id,
                    MaterialTransaction.transaction_type == "ISSUE",
                    MaterialTransaction.transaction_date >= ninety_days_ago,
                )
                .scalar()
            ) or 0
            avg_monthly = float(consumption_90d) / 3 if consumption_90d else 0

            if avg_monthly <= 0:
                continue

            current_stock = float(mat.current_stock or 0)
            lead_time = mat.lead_time_days or 0
            safety = float(mat.safety_stock or 0)

            # 当前库存能支撑的天数
            daily_usage = avg_monthly / 30
            if daily_usage <= 0:
                continue
            days_cover = current_stock / daily_usage

            # 如果库存覆盖天数 < 采购周期 * 1.5，建议提前采购
            if days_cover < lead_time * 1.5:
                suggested_qty = max(
                    avg_monthly * 2 + safety - current_stock, 0
                )
                if suggested_qty <= 0:
                    continue

                # 建议下单日期：需求日期 - 采购周期
                order_deadline = today + timedelta(days=max(int(days_cover) - lead_time, 0))

                reason = f"采购周期{lead_time}天，当前库存仅覆盖{round(days_cover, 0)}天"
                if days_cover < lead_time:
                    reason += "（已不足采购周期，急需下单）"

                suggestions.append({
                    "material_id": mat.id,
                    "material_code": mat.material_code,
                    "material_name": mat.material_name,
                    "lead_time_days": lead_time,
                    "avg_monthly_usage": round(avg_monthly, 2),
                    "current_stock": current_stock,
                    "reason": reason,
                    "suggested_qty": round(suggested_qty, 2),
                    "suggested_order_date": order_deadline if order_deadline >= today else today,
                })

        # 按紧急程度排序（库存覆盖天数少的在前）
        suggestions.sort(key=lambda x: x["current_stock"])
        return suggestions[:20]

    def _get_common_stock_suggestions(self) -> List[Dict[str, Any]]:
        """建议备库的通用物料"""
        six_months_ago = datetime.now() - timedelta(days=180)

        # 查找近6个月使用频次高的物料
        usage_stats = (
            self.db.query(
                BomItem.material_id,
                func.count(func.distinct(BomItem.bom_id)).label("usage_frequency"),
                func.count(
                    func.distinct(
                        self.db.query(func.coalesce(
                            func.nullif(
                                self.db.query(func.literal(1)).correlate(BomItem).scalar_subquery(),
                                None
                            ),
                            None
                        ))
                    )
                ).label("dummy"),
            )
            .filter(BomItem.material_id.isnot(None))
            .group_by(BomItem.material_id)
            .having(func.count(func.distinct(BomItem.bom_id)) >= 3)
            .order_by(desc("usage_frequency"))
            .limit(30)
            .all()
        )

        # 简化查询：直接查BomItem的使用频率
        usage_query = (
            self.db.query(
                BomItem.material_id,
                func.count(func.distinct(BomItem.bom_id)).label("usage_freq"),
            )
            .filter(BomItem.material_id.isnot(None))
            .group_by(BomItem.material_id)
            .having(func.count(func.distinct(BomItem.bom_id)) >= 3)
            .order_by(desc("usage_freq"))
            .limit(30)
            .all()
        )

        results = []
        for material_id, usage_freq in usage_query:
            mat = self.db.query(Material).get(material_id)
            if not mat or not mat.is_active:
                continue

            current_stock = float(mat.current_stock or 0)
            safety_stock = float(mat.safety_stock or 0)

            # 覆盖项目数
            project_count = (
                self.db.query(func.count(func.distinct(
                    self.db.query(BomItem.bom_id)
                    .join(Material, Material.id == BomItem.material_id)
                    .filter(BomItem.material_id == material_id)
                    .correlate(BomItem)
                    .scalar_subquery()
                )))
                .scalar()
            ) or 0

            # 简化：用BOM数近似项目覆盖数
            project_coverage = usage_freq

            # 建议安全库存：月均消耗 * 2
            ninety_days_ago = datetime.now() - timedelta(days=90)
            consumption = (
                self.db.query(func.sum(MaterialTransaction.quantity))
                .filter(
                    MaterialTransaction.material_id == material_id,
                    MaterialTransaction.transaction_type == "ISSUE",
                    MaterialTransaction.transaction_date >= ninety_days_ago,
                )
                .scalar()
            ) or 0
            avg_monthly = float(consumption) / 3 if consumption else 0
            suggested_safety = max(round(avg_monthly * 2, 2), safety_stock)

            if current_stock >= suggested_safety and safety_stock > 0:
                continue  # 已有足够安全库存

            results.append({
                "material_id": material_id,
                "material_code": mat.material_code,
                "material_name": mat.material_name,
                "usage_frequency": usage_freq,
                "project_coverage": project_coverage,
                "current_stock": current_stock,
                "suggested_safety_stock": suggested_safety,
                "reason": f"该物料在{usage_freq}个BOM中使用，属于高频通用物料，建议建立安全库存",
            })

        return results[:15]

    def _get_improvement_target(
        self, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """齐套率改进目标及路径"""
        # 计算当前齐套率
        query = self.db.query(MaterialShortage)
        if project_id:
            query = query.filter(MaterialShortage.project_id == project_id)

        # 最近 30 天的缺料情况
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_shortages = query.filter(
            MaterialShortage.created_at >= thirty_days_ago
        ).count()

        # 总BOM物料行数（近30天活跃BOM）
        total_bom_items = (
            self.db.query(func.count(BomItem.id))
            .filter(BomItem.material_id.isnot(None))
            .scalar()
        ) or 1

        # 齐套率 = (总物料行 - 缺料行) / 总物料行 * 100
        current_rate = round(
            max((total_bom_items - recent_shortages) / total_bom_items * 100, 0), 1
        )
        target_rate = min(current_rate + 10, 98.0)  # 目标提升10个百分点，上限98%
        gap = round(target_rate - current_rate, 1)

        key_actions = []
        if gap > 0:
            key_actions.append(f"处理TOP10瓶颈物料缺料问题，预计提升齐套率{min(gap * 0.4, 5):.1f}%")
            key_actions.append("对高风险供应商启动交期改善计划")
            key_actions.append("建立长周期物料提前采购机制")
            key_actions.append("完善通用物料安全库存策略")
            key_actions.append("推进替代料验证，减少单一来源依赖")

        timeline = "3个月" if gap <= 5 else ("6个月" if gap <= 10 else "9-12个月")

        return {
            "current_rate": current_rate,
            "target_rate": target_rate,
            "gap": gap,
            "key_actions": key_actions,
            "estimated_timeline": timeline,
        }

# -*- coding: utf-8 -*-
"""
物料跟踪系统 - 业务服务层
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.production.material_tracking import (
    MaterialAlert,
    MaterialAlertRule,
    MaterialBatch,
    MaterialConsumption,
)
from app.models.production.work_order import WorkOrder
from app.models.project import Project
from app.utils.db_helpers import get_or_404, save_obj


class MaterialTrackingService:
    def __init__(self, db: Session):
        self.db = db

    # ================== 1. 实时库存查询 ==================
    def get_realtime_stock(
        self,
        material_id: Optional[int] = None,
        material_code: Optional[str] = None,
        category_id: Optional[int] = None,
        warehouse_location: Optional[str] = None,
        status: Optional[str] = None,
        low_stock_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """实时库存查询 - 支持多维度筛选"""
        from app.common.query_filters import apply_keyword_filter, apply_pagination

        query = self.db.query(Material).filter(Material.is_active == True)

        # 条件筛选
        if material_id:
            query = query.filter(Material.id == material_id)
        if material_code:
            query = apply_keyword_filter(
                query, Material, material_code, ["material_code"]
            )
        if category_id:
            query = query.filter(Material.category_id == category_id)

        # 低库存筛选
        if low_stock_only:
            query = query.filter(Material.current_stock < Material.safety_stock)

        total = query.count()
        offset = (page - 1) * page_size
        materials = apply_pagination(query, offset, page_size).all()

        # 构建返回数据
        stock_data = []
        for mat in materials:
            # 查询批次明细
            batch_query = self.db.query(MaterialBatch).filter(
                MaterialBatch.material_id == mat.id,
                MaterialBatch.status == 'ACTIVE'
            )

            if warehouse_location:
                batch_query = apply_keyword_filter(
                    batch_query, MaterialBatch, warehouse_location, ["warehouse_location"]
                )
            if status:
                batch_query = batch_query.filter(MaterialBatch.status == status)

            batches = batch_query.all()

            batch_list = [
                {
                    "batch_no": b.batch_no,
                    "current_qty": float(b.current_qty) if b.current_qty else 0,
                    "reserved_qty": float(b.reserved_qty) if b.reserved_qty else 0,
                    "available_qty": float(b.current_qty - b.reserved_qty) if b.current_qty and b.reserved_qty else 0,
                    "warehouse_location": b.warehouse_location,
                    "production_date": b.production_date.isoformat() if b.production_date else None,
                    "expire_date": b.expire_date.isoformat() if b.expire_date else None,
                    "quality_status": b.quality_status,
                }
                for b in batches
            ]

            # 计算可用库存 (总库存 - 预留)
            total_reserved = sum([float(b.reserved_qty or 0) for b in batches])
            available_stock = float(mat.current_stock or 0) - total_reserved

            stock_data.append({
                "material_id": mat.id,
                "material_code": mat.material_code,
                "material_name": mat.material_name,
                "specification": mat.specification,
                "unit": mat.unit,
                "current_stock": float(mat.current_stock) if mat.current_stock else 0,
                "safety_stock": float(mat.safety_stock) if mat.safety_stock else 0,
                "available_stock": available_stock,
                "reserved_stock": total_reserved,
                "is_low_stock": (mat.current_stock or 0) < (mat.safety_stock or 0),
                "batch_count": len(batches),
                "batches": batch_list,
            })

        return {
            "items": stock_data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ================== 2. 记录物料消耗 ==================
    def create_consumption(
        self,
        consumption_data: Dict[str, Any],
        current_user_id: int,
    ) -> Dict[str, Any]:
        """记录物料消耗"""
        from fastapi import HTTPException, status

        material_id = consumption_data.get("material_id")
        consumption_qty = consumption_data.get("consumption_qty")
        consumption_type = consumption_data.get("consumption_type", "PRODUCTION")

        if not material_id or not consumption_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="material_id 和 consumption_qty 为必填项"
            )

        # 查询物料
        material = get_or_404(self.db, Material, material_id)

        # 条码/二维码扫描支持
        barcode = consumption_data.get("barcode")
        batch_id = consumption_data.get("batch_id")

        if barcode and not batch_id:
            # 通过条码查找批次
            batch = self.db.query(MaterialBatch).filter(
                MaterialBatch.barcode == barcode,
                MaterialBatch.material_id == material_id
            ).first()
            if batch:
                batch_id = batch.id

        # 生成消耗单号
        consumption_no = f"CONS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{material.material_code}"

        # 计算差异 (浪费识别)
        standard_qty = consumption_data.get("standard_qty")
        variance_qty = 0
        variance_rate = 0
        is_waste = False

        if standard_qty:
            variance_qty = float(consumption_qty) - float(standard_qty)
            if standard_qty > 0:
                variance_rate = (variance_qty / float(standard_qty)) * 100
                # 差异超过10%视为异常浪费
                is_waste = abs(variance_rate) > 10

        # 计算成本
        unit_price = consumption_data.get("unit_price") or material.standard_price or 0
        total_cost = float(consumption_qty) * float(unit_price)

        # 创建消耗记录
        consumption = MaterialConsumption(
            consumption_no=consumption_no,
            material_id=material_id,
            batch_id=batch_id,
            material_code=material.material_code,
            material_name=material.material_name,
            consumption_date=consumption_data.get("consumption_date", datetime.now()),
            consumption_qty=consumption_qty,
            unit=consumption_data.get("unit", material.unit),
            work_order_id=consumption_data.get("work_order_id"),
            project_id=consumption_data.get("project_id"),
            requisition_id=consumption_data.get("requisition_id"),
            consumption_type=consumption_type,
            standard_qty=standard_qty,
            variance_qty=variance_qty,
            variance_rate=variance_rate,
            is_waste=is_waste,
            operator_id=consumption_data.get("operator_id", current_user_id),
            workshop_id=consumption_data.get("workshop_id"),
            unit_price=unit_price,
            total_cost=total_cost,
            remark=consumption_data.get("remark"),
        )

        self.db.add(consumption)

        # 更新批次库存
        if batch_id:
            batch = self.db.query(MaterialBatch).filter(MaterialBatch.id == batch_id).first()
            if batch:
                batch.current_qty = (batch.current_qty or 0) - consumption_qty
                batch.consumed_qty = (batch.consumed_qty or 0) + consumption_qty
                if batch.current_qty <= 0:
                    batch.status = 'DEPLETED'

        # 更新物料总库存
        material.current_stock = (material.current_stock or 0) - consumption_qty

        self.db.commit()
        self.db.refresh(consumption)

        # 检查是否需要触发预警
        self.check_and_create_alerts(material)

        return {
            "id": consumption.id,
            "consumption_no": consumption.consumption_no,
            "material_code": consumption.material_code,
            "material_name": consumption.material_name,
            "consumption_qty": float(consumption.consumption_qty),
            "is_waste": consumption.is_waste,
            "variance_rate": float(consumption.variance_rate) if consumption.variance_rate else 0,
        }

    # ================== 3. 消耗分析 ==================
    def get_consumption_analysis(
        self,
        material_id: Optional[int] = None,
        project_id: Optional[int] = None,
        work_order_id: Optional[int] = None,
        consumption_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: str = "day",
    ) -> Dict[str, Any]:
        """物料消耗分析"""
        query = self.db.query(MaterialConsumption)

        # 筛选条件
        if material_id:
            query = query.filter(MaterialConsumption.material_id == material_id)
        if project_id:
            query = query.filter(MaterialConsumption.project_id == project_id)
        if work_order_id:
            query = query.filter(MaterialConsumption.work_order_id == work_order_id)
        if consumption_type:
            query = query.filter(MaterialConsumption.consumption_type == consumption_type)
        if start_date:
            query = query.filter(MaterialConsumption.consumption_date >= start_date)
        if end_date:
            query = query.filter(MaterialConsumption.consumption_date <= end_date)

        consumptions = query.all()

        # 统计数据
        total_consumption = sum([float(c.consumption_qty or 0) for c in consumptions])
        total_cost = sum([float(c.total_cost or 0) for c in consumptions])
        total_standard = sum([float(c.standard_qty or 0) for c in consumptions if c.standard_qty])
        waste_count = len([c for c in consumptions if c.is_waste])

        # 分组统计
        grouped_data = {}
        if group_by == "material":
            for c in consumptions:
                key = f"{c.material_code}-{c.material_name}"
                if key not in grouped_data:
                    grouped_data[key] = {
                        "material_code": c.material_code,
                        "material_name": c.material_name,
                        "total_qty": 0,
                        "total_cost": 0,
                        "waste_qty": 0,
                    }
                grouped_data[key]["total_qty"] += float(c.consumption_qty or 0)
                grouped_data[key]["total_cost"] += float(c.total_cost or 0)
                if c.is_waste:
                    grouped_data[key]["waste_qty"] += float(c.consumption_qty or 0)

        elif group_by in ["day", "week", "month"]:
            for c in consumptions:
                if group_by == "day":
                    key = c.consumption_date.strftime("%Y-%m-%d")
                elif group_by == "week":
                    key = c.consumption_date.strftime("%Y-W%U")
                else:  # month
                    key = c.consumption_date.strftime("%Y-%m")

                if key not in grouped_data:
                    grouped_data[key] = {
                        "period": key,
                        "total_qty": 0,
                        "total_cost": 0,
                        "record_count": 0,
                    }
                grouped_data[key]["total_qty"] += float(c.consumption_qty or 0)
                grouped_data[key]["total_cost"] += float(c.total_cost or 0)
                grouped_data[key]["record_count"] += 1

        return {
            "summary": {
                "total_records": len(consumptions),
                "total_consumption": total_consumption,
                "total_cost": total_cost,
                "total_standard": total_standard,
                "waste_count": waste_count,
                "waste_rate": (waste_count / len(consumptions) * 100) if consumptions else 0,
            },
            "grouped_data": list(grouped_data.values()),
        }

    # ================== 4. 缺料预警列表 ==================
    def list_alerts(
        self,
        alert_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        status: str = "ACTIVE",
        material_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """物料预警列表"""
        from app.common.query_filters import apply_pagination

        query = self.db.query(MaterialAlert)

        if alert_type:
            query = query.filter(MaterialAlert.alert_type == alert_type)
        if alert_level:
            query = query.filter(MaterialAlert.alert_level == alert_level)
        if status:
            query = query.filter(MaterialAlert.status == status)
        if material_id:
            query = query.filter(MaterialAlert.material_id == material_id)

        query = query.order_by(desc(MaterialAlert.alert_date))

        total = query.count()
        offset = (page - 1) * page_size
        alerts = apply_pagination(query, offset, page_size).all()

        alert_data = [
            {
                "id": a.id,
                "alert_no": a.alert_no,
                "material_code": a.material_code,
                "material_name": a.material_name,
                "alert_type": a.alert_type,
                "alert_level": a.alert_level,
                "alert_date": a.alert_date.isoformat() if a.alert_date else None,
                "current_stock": float(a.current_stock) if a.current_stock else 0,
                "safety_stock": float(a.safety_stock) if a.safety_stock else 0,
                "shortage_qty": float(a.shortage_qty) if a.shortage_qty else 0,
                "days_to_stockout": a.days_to_stockout,
                "alert_message": a.alert_message,
                "recommendation": a.recommendation,
                "status": a.status,
                "assigned_to_id": a.assigned_to_id,
            }
            for a in alerts
        ]

        return {
            "items": alert_data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ================== 5. 配置预警规则 ==================
    def create_alert_rule(
        self,
        rule_data: Dict[str, Any],
        current_user_id: int,
    ) -> Dict[str, Any]:
        """配置物料预警规则"""
        rule = MaterialAlertRule(
            rule_name=rule_data["rule_name"],
            material_id=rule_data.get("material_id"),
            category_id=rule_data.get("category_id"),
            alert_type=rule_data["alert_type"],
            alert_level=rule_data.get("alert_level", "WARNING"),
            threshold_type=rule_data.get("threshold_type", "PERCENTAGE"),
            threshold_value=rule_data["threshold_value"],
            safety_days=rule_data.get("safety_days", 7),
            lead_time_days=rule_data.get("lead_time_days", 0),
            buffer_ratio=rule_data.get("buffer_ratio", 1.2),
            notify_users=rule_data.get("notify_users"),
            notify_roles=rule_data.get("notify_roles"),
            is_active=rule_data.get("is_active", True),
            priority=rule_data.get("priority", 0),
            description=rule_data.get("description"),
            created_by=current_user_id,
        )

        save_obj(self.db, rule)

        return {"id": rule.id, "rule_name": rule.rule_name}

    # ================== 6. 物料浪费追溯 ==================
    def get_waste_records(
        self,
        material_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_variance_rate: float = 10,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """物料浪费追溯"""
        from app.common.query_filters import apply_pagination

        query = self.db.query(MaterialConsumption).filter(
            MaterialConsumption.is_waste == True,
            MaterialConsumption.variance_rate >= min_variance_rate
        )

        if material_id:
            query = query.filter(MaterialConsumption.material_id == material_id)
        if project_id:
            query = query.filter(MaterialConsumption.project_id == project_id)
        if start_date:
            query = query.filter(MaterialConsumption.consumption_date >= start_date)
        if end_date:
            query = query.filter(MaterialConsumption.consumption_date <= end_date)

        query = query.order_by(desc(MaterialConsumption.variance_rate))

        total = query.count()
        offset = (page - 1) * page_size
        wastes = apply_pagination(query, offset, page_size).all()

        waste_data = []
        for w in wastes:
            # 获取关联信息
            project_name = None
            work_order_no = None

            if w.project_id:
                proj = self.db.query(Project).filter(Project.id == w.project_id).first()
                if proj:
                    project_name = proj.project_name

            if w.work_order_id:
                wo = self.db.query(WorkOrder).filter(WorkOrder.id == w.work_order_id).first()
                if wo:
                    work_order_no = wo.work_order_no

            waste_data.append({
                "id": w.id,
                "consumption_no": w.consumption_no,
                "material_code": w.material_code,
                "material_name": w.material_name,
                "consumption_date": w.consumption_date.isoformat() if w.consumption_date else None,
                "actual_qty": float(w.consumption_qty) if w.consumption_qty else 0,
                "standard_qty": float(w.standard_qty) if w.standard_qty else 0,
                "variance_qty": float(w.variance_qty) if w.variance_qty else 0,
                "variance_rate": float(w.variance_rate) if w.variance_rate else 0,
                "consumption_type": w.consumption_type,
                "project_name": project_name,
                "work_order_no": work_order_no,
                "total_cost": float(w.total_cost) if w.total_cost else 0,
                "remark": w.remark,
            })

        # 统计汇总
        total_waste_qty = sum([float(w.variance_qty or 0) for w in wastes])
        total_waste_cost = sum([
            float(w.variance_qty or 0) * float(w.unit_price or 0) for w in wastes
        ])

        return {
            "items": waste_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total_waste_qty": total_waste_qty,
                "total_waste_cost": total_waste_cost,
            },
        }

    # ================== 7. 批次追溯 ==================
    def trace_batch(
        self,
        batch_no: Optional[str] = None,
        batch_id: Optional[int] = None,
        barcode: Optional[str] = None,
        trace_direction: str = "forward",
    ) -> Dict[str, Any]:
        """批次追溯 - 支持正向和反向查询"""
        from fastapi import HTTPException, status

        # 查找批次
        batch = None
        if batch_id:
            batch = self.db.query(MaterialBatch).filter(MaterialBatch.id == batch_id).first()
        elif batch_no:
            batch = self.db.query(MaterialBatch).filter(MaterialBatch.batch_no == batch_no).first()
        elif barcode:
            batch = self.db.query(MaterialBatch).filter(MaterialBatch.barcode == barcode).first()

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到批次记录"
            )

        # 批次基本信息
        material = self.db.query(Material).filter(Material.id == batch.material_id).first()

        batch_info = {
            "batch_id": batch.id,
            "batch_no": batch.batch_no,
            "material_code": material.material_code if material else None,
            "material_name": material.material_name if material else None,
            "initial_qty": float(batch.initial_qty) if batch.initial_qty else 0,
            "current_qty": float(batch.current_qty) if batch.current_qty else 0,
            "consumed_qty": float(batch.consumed_qty) if batch.consumed_qty else 0,
            "production_date": batch.production_date.isoformat() if batch.production_date else None,
            "expire_date": batch.expire_date.isoformat() if batch.expire_date else None,
            "supplier_batch_no": batch.supplier_batch_no,
            "quality_status": batch.quality_status,
            "warehouse_location": batch.warehouse_location,
            "status": batch.status,
        }

        # 正向追溯: 查询消耗记录
        consumptions = self.db.query(MaterialConsumption).filter(
            MaterialConsumption.batch_id == batch.id
        ).order_by(desc(MaterialConsumption.consumption_date)).all()

        consumption_trail = []
        projects_used = set()
        work_orders_used = set()

        for c in consumptions:
            # 获取关联信息
            project_info = None
            work_order_info = None

            if c.project_id:
                proj = self.db.query(Project).filter(Project.id == c.project_id).first()
                if proj:
                    project_info = {
                        "id": proj.id,
                        "project_no": proj.project_no,
                        "project_name": proj.project_name,
                    }
                    projects_used.add(proj.id)

            if c.work_order_id:
                wo = self.db.query(WorkOrder).filter(WorkOrder.id == c.work_order_id).first()
                if wo:
                    work_order_info = {
                        "id": wo.id,
                        "work_order_no": wo.work_order_no,
                    }
                    work_orders_used.add(wo.id)

            consumption_trail.append({
                "consumption_no": c.consumption_no,
                "consumption_date": c.consumption_date.isoformat() if c.consumption_date else None,
                "consumption_qty": float(c.consumption_qty) if c.consumption_qty else 0,
                "consumption_type": c.consumption_type,
                "project": project_info,
                "work_order": work_order_info,
                "operator_id": c.operator_id,
            })

        return {
            "batch_info": batch_info,
            "consumption_trail": consumption_trail,
            "summary": {
                "total_consumptions": len(consumptions),
                "projects_count": len(projects_used),
                "work_orders_count": len(work_orders_used),
            }
        }

    # ================== 8. 物料成本分析 ==================
    def get_cost_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None,
        category_id: Optional[int] = None,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """物料成本分析"""
        query = self.db.query(MaterialConsumption)

        if start_date:
            query = query.filter(MaterialConsumption.consumption_date >= start_date)
        if end_date:
            query = query.filter(MaterialConsumption.consumption_date <= end_date)
        if project_id:
            query = query.filter(MaterialConsumption.project_id == project_id)

        consumptions = query.all()

        # 按物料聚合
        material_costs = {}
        for c in consumptions:
            if c.material_id not in material_costs:
                material_costs[c.material_id] = {
                    "material_id": c.material_id,
                    "material_code": c.material_code,
                    "material_name": c.material_name,
                    "total_qty": 0,
                    "total_cost": 0,
                }
            material_costs[c.material_id]["total_qty"] += float(c.consumption_qty or 0)
            material_costs[c.material_id]["total_cost"] += float(c.total_cost or 0)

        # 排序获取 Top N
        sorted_materials = sorted(
            material_costs.values(),
            key=lambda x: x["total_cost"],
            reverse=True
        )[:top_n]

        total_cost = sum([m["total_cost"] for m in material_costs.values()])

        return {
            "total_cost": total_cost,
            "material_count": len(material_costs),
            "top_materials": sorted_materials,
        }

    # ================== 9. 库存周转率 ==================
    def get_turnover_analysis(
        self,
        material_id: Optional[int] = None,
        category_id: Optional[int] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """库存周转率分析"""
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)

        query = self.db.query(Material).filter(Material.is_active == True)

        if material_id:
            query = query.filter(Material.id == material_id)
        if category_id:
            query = query.filter(Material.category_id == category_id)

        materials = query.all()

        turnover_data = []
        for mat in materials:
            # 查询期间内消耗
            consumptions = self.db.query(MaterialConsumption).filter(
                MaterialConsumption.material_id == mat.id,
                MaterialConsumption.consumption_date >= start_dt,
                MaterialConsumption.consumption_date <= end_dt
            ).all()

            total_consumption = sum([float(c.consumption_qty or 0) for c in consumptions])

            # 平均库存 (简化: 使用当前库存)
            avg_stock = float(mat.current_stock or 0)

            # 周转率和周转天数
            turnover_rate = (total_consumption / avg_stock) if avg_stock > 0 else 0
            turnover_days = (days / turnover_rate) if turnover_rate > 0 else 0

            turnover_data.append({
                "material_id": mat.id,
                "material_code": mat.material_code,
                "material_name": mat.material_name,
                "current_stock": avg_stock,
                "consumption_qty": total_consumption,
                "turnover_rate": round(turnover_rate, 2),
                "turnover_days": round(turnover_days, 1),
            })

        # 按周转率排序
        turnover_data.sort(key=lambda x: x["turnover_rate"], reverse=True)

        return {
            "period_days": days,
            "materials": turnover_data,
        }

    # ================== 辅助方法 ==================
    def check_and_create_alerts(self, material: Material):
        """检查并创建物料预警"""
        # 查询适用的预警规则
        rules = self.db.query(MaterialAlertRule).filter(
            MaterialAlertRule.is_active == True,
            or_(
                MaterialAlertRule.material_id == material.id,
                MaterialAlertRule.material_id == None  # 全局规则
            )
        ).all()

        for rule in rules:
            should_alert = False
            alert_message = ""
            shortage_qty = 0

            # 低库存预警
            if rule.alert_type == "LOW_STOCK":
                if rule.threshold_type == "PERCENTAGE":
                    threshold = float(material.safety_stock or 0) * (float(rule.threshold_value) / 100)
                    if float(material.current_stock or 0) < threshold:
                        should_alert = True
                        shortage_qty = threshold - float(material.current_stock or 0)
                        alert_message = f"{material.material_name} 库存低于安全库存的{rule.threshold_value}%"
                elif rule.threshold_type == "FIXED":
                    if float(material.current_stock or 0) < float(rule.threshold_value):
                        should_alert = True
                        shortage_qty = float(rule.threshold_value) - float(material.current_stock or 0)
                        alert_message = f"{material.material_name} 库存低于{rule.threshold_value}"

            # 缺料预警
            elif rule.alert_type == "SHORTAGE":
                if float(material.current_stock or 0) <= 0:
                    should_alert = True
                    alert_message = f"{material.material_name} 已缺料"

            if should_alert:
                # 检查是否已存在活动预警
                existing = self.db.query(MaterialAlert).filter(
                    MaterialAlert.material_id == material.id,
                    MaterialAlert.alert_type == rule.alert_type,
                    MaterialAlert.status == 'ACTIVE'
                ).first()

                if not existing:
                    # 创建新预警
                    alert_no = f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{material.material_code}"

                    # 计算消耗速率和缺货天数
                    avg_daily_consumption = self.calculate_avg_daily_consumption(material.id, days=30)
                    days_to_stockout = 0
                    if avg_daily_consumption > 0:
                        days_to_stockout = int(float(material.current_stock or 0) / avg_daily_consumption)

                    alert = MaterialAlert(
                        alert_no=alert_no,
                        material_id=material.id,
                        material_code=material.material_code,
                        material_name=material.material_name,
                        alert_date=datetime.now(),
                        alert_type=rule.alert_type,
                        alert_level=rule.alert_level,
                        current_stock=material.current_stock,
                        safety_stock=material.safety_stock,
                        shortage_qty=shortage_qty,
                        avg_daily_consumption=avg_daily_consumption,
                        days_to_stockout=days_to_stockout,
                        alert_message=alert_message,
                        recommendation=f"建议采购数量: {shortage_qty + float(material.safety_stock or 0)}",
                        status='ACTIVE',
                    )

                    self.db.add(alert)
                    self.db.commit()

    def calculate_avg_daily_consumption(self, material_id: int, days: int = 30) -> float:
        """计算平均日消耗"""
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)

        consumptions = self.db.query(MaterialConsumption).filter(
            MaterialConsumption.material_id == material_id,
            MaterialConsumption.consumption_date >= start_dt,
            MaterialConsumption.consumption_date <= end_dt
        ).all()

        total_consumption = sum([float(c.consumption_qty or 0) for c in consumptions])

        return total_consumption / days if days > 0 else 0

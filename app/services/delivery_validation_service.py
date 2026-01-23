# -*- coding: utf-8 -*-
"""
交期校验服务
支持物料交期查询、项目周期估算、交期合理性校验
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material import BomItem, Material
from app.models.vendor import Vendor
from app.models.project import Project
from app.models.sales import Quote, QuoteItem, QuoteVersion


class DeliveryValidationService:
    """交期校验服务"""

    # 项目阶段默认工期（天）
    DEFAULT_STAGE_DURATION = {
        "S1": 7,      # 需求进入
        "S2": 14,     # 方案设计
        "S3": 21,     # 采购备料
        "S4": 30,     # 加工制造
        "S5": 14,     # 装配调试
        "S6": 3,      # 出厂验收(FAT)
        "S7": 2,      # 包装发运
        "S8": 7,      # 现场安装(SAT)
        "S9": 0,      # 质保结项
    }

    # 物料类型默认交期（天）
    DEFAULT_MATERIAL_LEAD_TIME = {
        "标准件": 7,
        "机械件": 14,
        "电气件": 10,
        "气动件": 7,
        "外购件": 21,
        "定制件": 30,
    }

    @staticmethod
    def get_material_lead_time(
        db: Session,
        material_code: Optional[str] = None,
        material_id: Optional[int] = None,
        material_type: Optional[str] = None
    ) -> Tuple[int, Optional[str]]:
        """
        获取物料交期（天）

        Args:
            db: 数据库会话
            material_code: 物料编码
            material_id: 物料ID
            material_type: 物料类型

        Returns:
            (交期天数, 备注)
        """
        # 优先通过ID查询
        if material_id:
            material = db.query(Material).filter(Material.id == material_id).first()
            if material and material.lead_time_days:
                return material.lead_time_days, f"来自物料档案: {material.material_name}"

        # 其次通过编码查询
        if material_code:
            material = db.query(Material).filter(
                Material.material_code == material_code
            ).first()
            if material and material.lead_time_days:
                return material.lead_time_days, f"来自物料档案: {material.material_name}"

        # 最后使用物料类型默认值
        if material_type:
            default_days = DeliveryValidationService.DEFAULT_MATERIAL_LEAD_TIME.get(
                material_type, 14
            )
            return default_days, f"基于物料类型({material_type})的默认值"

        # 无任何信息，返回默认值
        return 14, "使用默认值14天"

    @staticmethod
    def get_max_material_lead_time(
        db: Session,
        items: List[QuoteItem]
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        获取报价单中最长物料交期

        Args:
            db: 数据库会话
            items: 报价明细列表

        Returns:
            (最长交期天数, 物料交期详情列表)
        """
        material_lead_times = []

        for item in items:
            # 只考虑需要采购的物料
            if item.item_type not in ['硬件', '外购件', '标准件', '机械件', '电气件', '气动件']:
                continue

            lead_time, remark = DeliveryValidationService.get_material_lead_time(
                db,
                material_code=item.material_code,
                material_type=item.item_type
            )

            material_lead_times.append({
                "item_name": item.item_name or f"项目{item.id}",
                "item_type": item.item_type,
                "lead_time_days": lead_time,
                "remark": remark,
                "quantity": getattr(item, 'quantity', 0) or 0,
                "is_critical": getattr(item, 'is_critical', False) or False
            })

        # 获取最长的交期（关键物料优先）
        critical_items = [m for m in material_lead_times if m.get("is_critical")]
        if critical_items:
            max_days = max(m["lead_time_days"] for m in critical_items)
        else:
            max_days = max([m["lead_time_days"] for m in material_lead_times]) if material_lead_times else 0

        return max_days, material_lead_times

    @staticmethod
    def estimate_project_cycle(
        db: Session,
        contract_amount: Optional[float] = None,
        project_type: Optional[str] = None,
        complexity_level: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        估算项目周期

        Args:
            db: 数据库会话
            contract_amount: 合同金额
            project_type: 项目类型
            complexity_level: 复杂度 (SIMPLE/MEDIUM/COMPLEX)

        Returns:
            项目周期估算结果
        """
        # 基础周期（天）- 根据复杂度
        base_days = {
            "SIMPLE": 45,    # 简单项目：1.5个月
            "MEDIUM": 75,    # 中等项目：2.5个月
            "COMPLEX": 105,  # 复杂项目：3.5个月
        }

        # 根据项目类型调整系数
        type_multiplier = {
            "单机类": 1.0,
            "线体类": 1.3,
            "改造类": 0.7,
            "测试设备": 0.9,
        }

        # 根据金额调整系数
        amount_multiplier = 1.0
        if contract_amount:
            if contract_amount > 5000000:  # 500万以上
                amount_multiplier = 1.2
            elif contract_amount > 2000000:  # 200万以上
                amount_multiplier = 1.1
            elif contract_amount < 500000:  # 50万以下
                amount_multiplier = 0.85

        base = base_days.get(complexity_level, 75)
        type_mult = type_multiplier.get(project_type, 1.0)

        estimated_days = int(base * type_mult * amount_multiplier)

        # 计算各阶段时间
        stage_details = []
        total_ratio = 0

        # 计算各阶段占比和天数
        stage_ratios = {
            "S1": 0.10,   # 需求进入
            "S2": 0.20,   # 方案设计
            "S3": 0.20,   # 采购备料
            "S4": 0.25,   # 加工制造
            "S5": 0.15,   # 装配调试
            "S6": 0.04,   # FAT
            "S7": 0.03,   # 发运
            "S8": 0.03,   # SAT
        }

        for stage, ratio in stage_ratios.items():
            stage_days = max(1, int(estimated_days * ratio))
            stage_name = {
                "S1": "需求进入", "S2": "方案设计", "S3": "采购备料",
                "S4": "加工制造", "S5": "装配调试", "S6": "出厂验收",
                "S7": "包装发运", "S8": "现场安装"
            }.get(stage, stage)
            stage_details.append({
                "stage": stage,
                "stage_name": stage_name,
                "days": stage_days,
                "ratio": ratio
            })

        # 计算预计完成日期
        start_date = date.today()
        end_date = start_date + timedelta(days=estimated_days)

        return {
            "estimated_total_days": estimated_days,
            "estimated_start_date": start_date.isoformat(),
            "estimated_end_date": end_date.isoformat(),
            "complexity_level": complexity_level,
            "project_type": project_type,
            "stage_details": stage_details,
            "calculation_base": f"基础{base}天 × 类型系数{type_mult} × 金额系数{amount_multiplier}"
        }

    @staticmethod
    def validate_delivery_date(
        db: Session,
        quote: Quote,
        version: QuoteVersion,
        items: List[QuoteItem]
    ) -> Dict[str, Any]:
        """
        校验报价交期的合理性

        Args:
            db: 数据库会话
            quote: 报价单
            version: 报价版本
            items: 报价明细

        Returns:
            校验结果
        """
        checks = []
        warnings = []
        errors = []

        # 1. 检查报价交期是否填写
        if not version.lead_time_days or version.lead_time_days <= 0:
            errors.append({
                "check": "交期填写",
                "status": "ERROR",
                "message": "请填写项目交期（天）"
            })
        else:
            checks.append({
                "check": "交期填写",
                "status": "PASS",
                "message": f"报价交期: {version.lead_time_days}天"
            })

        # 2. 获取最长物料交期
        max_material_days, material_details = DeliveryValidationService.get_max_material_lead_time(
            db, items
        )

        if max_material_days > 0:
            checks.append({
                "check": "物料交期",
                "status": "PASS",
                "message": f"最长物料交期: {max_material_days}天",
                "details": material_details[:5]  # 只返回前5个
            })

            # 检查报价交期是否足以覆盖物料交期
            if version.lead_time_days and version.lead_time_days < max_material_days:
                warnings.append({
                    "check": "物料交期覆盖",
                    "status": "WARNING",
                    "message": f"报价交期({version.lead_time_days}天)短于最长物料交期({max_material_days}天)，可能影响采购"
                })

        # 3. 估算项目周期并对比
        # Quote doesn't have project_type directly, get it from the related opportunity
        project_type = None
        if hasattr(quote, 'opportunity') and quote.opportunity:
            project_type = getattr(quote.opportunity, 'project_type', None)

        project_cycle = DeliveryValidationService.estimate_project_cycle(
            db,
            contract_amount=float(version.total_price or 0),
            project_type=project_type,
            complexity_level="MEDIUM"
        )

        estimated_days = project_cycle["estimated_total_days"]
        checks.append({
            "check": "项目周期估算",
            "status": "INFO",
            "message": f"基于项目类型和金额估算周期: {estimated_days}天",
            "details": project_cycle["stage_details"]
        })

        # 检查报价交期与估算周期的差异
        if version.lead_time_days:
            diff_ratio = (version.lead_time_days - estimated_days) / estimated_days if estimated_days > 0 else 0

            if diff_ratio < -0.3:  # 少于30%
                warnings.append({
                    "check": "交期合理性",
                    "status": "WARNING",
                    "message": f"报价交期({version.lead_time_days}天)比估算周期({estimated_days}天)少{abs(diff_ratio)*100:.0f}%，请确认可行性"
                })
            elif diff_ratio > 0.5:  # 多于50%
                warnings.append({
                    "check": "交期合理性",
                    "status": "INFO",
                    "message": f"报价交期({version.lead_time_days}天)比估算周期({estimated_days}天)多{diff_ratio*100:.0f}%，可能影响竞争力"
                })
            else:
                checks.append({
                    "check": "交期合理性",
                    "status": "PASS",
                    "message": f"报价交期({version.lead_time_days}天)在合理范围内"
                })

        # 4. 检查关键物料是否都有交期
        critical_items_without_leadtime = [
            item.item_name for item in items
            if getattr(item, 'is_critical', False) and not getattr(item, 'lead_time_days', None)
        ]

        if critical_items_without_leadtime:
            warnings.append({
                "check": "关键物料交期",
                "status": "WARNING",
                "message": f"以下关键物料未填写交期: {', '.join(critical_items_without_leadtime[:5])}"
            })

        # 5. 汇总结果
        status = "PASS"
        if errors:
            status = "ERROR"
        elif warnings:
            status = "WARNING"

        return {
            "status": status,
            "quoted_lead_time": version.lead_time_days,
            "max_material_lead_time": max_material_days,
            "estimated_project_cycle": estimated_days,
            "checks": checks,
            "warnings": warnings,
            "errors": errors,
            "suggestions": DeliveryValidationService._get_suggestions(
                version.lead_time_days, max_material_days, estimated_days
            )
        }

    @staticmethod
    def _get_suggestions(
        quoted_days: Optional[int],
        material_days: int,
        estimated_days: int
    ) -> List[str]:
        """生成优化建议"""
        suggestions = []

        if quoted_days:
            if quoted_days < material_days:
                suggestions.append(f"建议将交期调整为至少{material_days + 7}天，以覆盖最长物料交期并预留缓冲")

            if quoted_days < estimated_days:
                suggestions.append(f"建议将交期调整为至少{estimated_days}天，以匹配项目周期估算")

            # 建议的合理范围
            suggested_min = max(material_days, estimated_days)
            suggested_max = int(suggested_min * 1.2)
            suggestions.append(f"建议交期范围: {suggested_min}-{suggested_max}天")
        else:
            suggestions.append(f"建议交期: {max(material_days, estimated_days)}天（基于物料和项目周期）")

        return suggestions


# 创建单例
delivery_validation_service = DeliveryValidationService()

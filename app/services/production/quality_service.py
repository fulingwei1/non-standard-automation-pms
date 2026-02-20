# -*- coding: utf-8 -*-
"""
质量管理服务 - 生产模块

处理质检记录列表查询、质量预警列表、预警规则管理、返工单列表、纠正措施等
端点层的业务逻辑提取到此服务。
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.production import (
    DefectAnalysis,
    QualityAlertRule,
    QualityInspection,
    ReworkOrder,
)
from app.schemas.production.quality import QualityAlertResponse
from app.utils.db_helpers import save_obj


class ProductionQualityService:
    """质量管理端点业务逻辑服务"""

    def __init__(self, db: Session):
        self.db = db

    def list_inspections(
        self,
        skip: int,
        limit: int,
        material_id: Optional[int] = None,
        inspection_type: Optional[str] = None,
        inspection_result: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """查询质检记录列表"""
        query = self.db.query(QualityInspection)

        if material_id:
            query = query.filter(QualityInspection.material_id == material_id)
        if inspection_type:
            query = query.filter(QualityInspection.inspection_type == inspection_type)
        if inspection_result:
            query = query.filter(QualityInspection.inspection_result == inspection_result)
        if start_date:
            query = query.filter(QualityInspection.inspection_date >= start_date)
        if end_date:
            query = query.filter(QualityInspection.inspection_date <= end_date)

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
        }

    def list_alerts(
        self,
        skip: int,
        limit: int,
        alert_level: Optional[str] = None,
    ) -> dict:
        """查询质量预警列表"""
        query = self.db.query(QualityAlertRule).filter(
            QualityAlertRule.enabled == 1,
            QualityAlertRule.last_triggered_at.isnot(None),
        )

        if alert_level:
            query = query.filter(QualityAlertRule.alert_level == alert_level)

        total = query.count()
        rules = (
            query.order_by(QualityAlertRule.last_triggered_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        items = [
            QualityAlertResponse(
                alert_id=rule.id,
                rule_id=rule.id,
                rule_name=rule.rule_name,
                alert_type=rule.alert_type,
                alert_level=rule.alert_level,
                trigger_time=rule.last_triggered_at,
                current_value=float(rule.threshold_value),
                threshold_value=float(rule.threshold_value),
                message=f"质量预警: {rule.rule_name}",
                material_id=rule.target_material_id,
                process_id=rule.target_process_id,
            )
            for rule in rules
        ]

        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
        }

    def create_alert_rule(self, rule_data, current_user_id: int) -> QualityAlertRule:
        """创建质量预警规则"""
        # 生成规则编号
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"QR{today}"

        last_rule = (
            self.db.query(QualityAlertRule)
            .filter(QualityAlertRule.rule_no.like(f"{prefix}%"))
            .order_by(QualityAlertRule.rule_no.desc())
            .first()
        )

        if last_rule:
            last_seq = int(last_rule.rule_no[-4:])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        rule_no = f"{prefix}{new_seq:04d}"

        rule = QualityAlertRule(
            rule_no=rule_no,
            created_by=current_user_id,
            **rule_data.model_dump(),
        )

        save_obj(self.db, rule)
        return rule

    def list_alert_rules(self, enabled: Optional[int] = None) -> list:
        """查询质量预警规则列表"""
        query = self.db.query(QualityAlertRule)

        if enabled is not None:
            query = query.filter(QualityAlertRule.enabled == enabled)

        return query.all()

    def list_rework_orders(
        self,
        skip: int,
        limit: int,
        status: Optional[str] = None,
    ) -> dict:
        """查询返工单列表"""
        query = self.db.query(ReworkOrder)

        if status:
            query = query.filter(ReworkOrder.status == status)

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
        }

    def create_corrective_action(self, action_data) -> dict:
        """创建纠正措施"""
        from app.utils.db_helpers import get_or_404

        analysis = get_or_404(
            self.db, DefectAnalysis, action_data.defect_analysis_id, "不良品分析记录不存在"
        )

        if action_data.action_type == "CORRECTIVE":
            analysis.corrective_action = action_data.action_description
        else:
            analysis.preventive_action = action_data.action_description

        analysis.responsible_person_id = action_data.responsible_person_id
        analysis.due_date = action_data.due_date

        self.db.commit()

        return {
            "message": "纠正措施创建成功",
            "analysis_id": analysis.id,
        }

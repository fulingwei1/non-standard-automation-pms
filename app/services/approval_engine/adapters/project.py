# -*- coding: utf-8 -*-
"""
项目审批适配器

将项目模块接入统一审批系统
项目审批主要用于：项目立项、项目变更、项目结项等场景
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.project.core import Project

from .base import ApprovalAdapter


class ProjectApprovalAdapter(ApprovalAdapter):
    """
    项目审批适配器

    支持的条件字段:
    - entity.contract_amount: 合同金额
    - entity.budget_amount: 预算金额
    - entity.project_type: 项目类型
    - entity.project_category: 项目分类
    - entity.priority: 优先级
    """

    entity_type = "PROJECT"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[Project]:
        """获取项目实体"""
        return self.db.query(Project).filter(Project.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取项目数据用于条件路由

        Returns:
            包含项目关键数据的字典
        """
        project = self.get_entity(entity_id)
        if not project:
            return {}

        return {
            "project_code": project.project_code,
            "project_name": project.project_name,
            "short_name": project.short_name,
            "status": project.status,
            "stage": project.stage,
            "health": project.health,
            "project_type": project.project_type,
            "project_category": project.project_category,
            "product_category": project.product_category,
            "industry": project.industry,
            "customer_id": project.customer_id,
            "customer_name": project.customer_name,
            "contract_amount": float(project.contract_amount) if project.contract_amount else 0,
            "budget_amount": float(project.budget_amount) if project.budget_amount else 0,
            "actual_cost": float(project.actual_cost) if project.actual_cost else 0,
            "progress_pct": float(project.progress_pct) if project.progress_pct else 0,
            "pm_id": project.pm_id,
            "pm_name": project.pm_name,
            "dept_id": project.dept_id,
            "priority": project.priority,
            "planned_start_date": project.planned_start_date.isoformat() if project.planned_start_date else None,
            "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """提交审批时的回调"""
        project = self.get_entity(entity_id)
        if project:
            project.status = "PENDING_APPROVAL"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批通过时的回调"""
        project = self.get_entity(entity_id)
        if project:
            # 根据当前阶段决定审批通过后的状态
            if project.stage == "S1":
                # 立项审批通过，进入方案设计阶段
                project.status = "ST02"  # 进行中
                project.stage = "S2"
            else:
                project.status = "ST02"
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批驳回时的回调"""
        project = self.get_entity(entity_id)
        if project:
            project.status = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """撤回审批时的回调"""
        project = self.get_entity(entity_id)
        if project:
            project.status = "ST01"  # 草稿
            self.db.flush()

    def get_title(self, entity_id: int) -> str:
        """生成审批标题"""
        project = self.get_entity(entity_id)
        if project:
            return f"项目审批 - {project.project_code}: {project.project_name}"
        return f"项目审批 - #{entity_id}"

    def get_summary(self, entity_id: int) -> str:
        """生成审批摘要"""
        data = self.get_entity_data(entity_id)
        if not data:
            return ""

        parts = []
        if data.get("customer_name"):
            parts.append(f"客户: {data['customer_name']}")
        if data.get("contract_amount"):
            parts.append(f"合同金额: ¥{data['contract_amount']:,.2f}")
        if data.get("pm_name"):
            parts.append(f"项目经理: {data['pm_name']}")
        if data.get("project_type"):
            parts.append(f"类型: {data['project_type']}")

        return " | ".join(parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, str]:
        """验证是否可以提交审批"""
        project = self.get_entity(entity_id)
        if not project:
            return False, "项目不存在"

        if project.status not in ("ST01", "REJECTED"):
            return False, f"当前状态({project.status})不允许提交审批"

        if not project.project_name:
            return False, "项目名称不能为空"

        if not project.pm_id:
            return False, "请指定项目经理"

        return True, ""

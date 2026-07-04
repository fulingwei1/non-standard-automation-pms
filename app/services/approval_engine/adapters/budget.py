# -*- coding: utf-8 -*-
"""Project budget approval adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func

from app.models.approval import ApprovalInstance
from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.project import Project

from .base import ApprovalAdapter


class ProjectBudgetApprovalAdapter(ApprovalAdapter):
    """Connect project budgets to the unified approval engine."""

    entity_type = "PROJECT_BUDGET"

    def get_entity(self, entity_id: int) -> Optional[ProjectBudget]:
        return self.db.query(ProjectBudget).filter(ProjectBudget.id == entity_id).first()

    def _calculate_items_total(self, entity_id: int) -> Decimal:
        total = (
            self.db.query(func.coalesce(func.sum(ProjectBudgetItem.budget_amount), 0))
            .filter(ProjectBudgetItem.budget_id == entity_id)
            .scalar()
        )
        return Decimal(str(total or 0))

    def get_entity_data(self, entity_id: int) -> dict[str, Any]:
        budget = self.get_entity(entity_id)
        if not budget:
            return {}
        item_total = self._calculate_items_total(entity_id)
        return {
            "budget_id": budget.id,
            "budget_no": budget.budget_no,
            "budget_name": budget.budget_name,
            "budget_type": budget.budget_type,
            "project_id": budget.project_id,
            "project_code": budget.project.project_code if budget.project else None,
            "project_name": budget.project.project_name if budget.project else None,
            "total_amount": float(budget.total_amount or 0),
            "item_total": float(item_total),
            "status": budget.status,
            "version": budget.version,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        budget = self.get_entity(entity_id)
        if not budget:
            return
        budget.total_amount = self._calculate_items_total(entity_id) or budget.total_amount
        budget.status = "SUBMITTED"
        budget.submitted_at = instance.submitted_at
        budget.submitted_by = instance.initiator_id
        self.db.add(budget)

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        budget = self.get_entity(entity_id)
        if not budget:
            return
        budget.total_amount = self._calculate_items_total(entity_id) or budget.total_amount
        budget.status = "APPROVED"
        budget.approved_at = instance.completed_at
        budget.approved_by = instance.final_approver_id
        budget.is_active = True

        if budget.budget_type in ["INITIAL", "REVISED"]:
            project = self.db.query(Project).filter(Project.id == budget.project_id).first()
            if project:
                project.budget_amount = budget.total_amount
                self.db.add(project)

        self.db.query(ProjectBudget).filter(
            ProjectBudget.project_id == budget.project_id,
            ProjectBudget.id != budget.id,
            ProjectBudget.is_active,
        ).update({"is_active": False}, synchronize_session=False)
        self.db.add(budget)

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        budget = self.get_entity(entity_id)
        if not budget:
            return
        budget.status = "REJECTED"
        budget.approved_at = instance.completed_at
        budget.approved_by = instance.final_approver_id
        self.db.add(budget)

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        budget = self.get_entity(entity_id)
        if not budget:
            return
        budget.status = "DRAFT"
        budget.submitted_at = None
        budget.submitted_by = None
        self.db.add(budget)

    def generate_title(self, entity_id: int) -> str:
        budget = self.get_entity(entity_id)
        if not budget:
            return f"项目预算审批 - {entity_id}"
        return f"项目预算审批 - {budget.budget_no}"

    def generate_summary(self, entity_id: int) -> str:
        data = self.get_entity_data(entity_id)
        if not data:
            return ""
        return (
            f"{data.get('project_name') or '未指定项目'} / "
            f"{data.get('budget_name') or '未命名预算'} / "
            f"{data.get('total_amount') or 0:.2f}"
        )

    def validate_submit(self, entity_id: int) -> tuple[bool, Optional[str]]:
        budget = self.get_entity(entity_id)
        if not budget:
            return False, "预算不存在"
        if budget.status != "DRAFT":
            return False, "只能提交草稿状态的预算"
        if not budget.project_id:
            return False, "预算缺少项目ID，不能提交审批"
        item_total = self._calculate_items_total(entity_id)
        effective_total = item_total if item_total > 0 else Decimal(str(budget.total_amount or 0))
        if effective_total <= 0:
            return False, "预算总额必须大于0"
        return True, None

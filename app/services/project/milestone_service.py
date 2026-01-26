# -*- coding: utf-8 -*-
"""
Project milestone service built on the shared BaseCRUDService.

This service scopes every CRUD operation to a specific project_id so controllers
don't need to reimplement filtering/validation logic.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Sequence

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.crud import BaseCRUDService, SortOrder
from app.common.crud.exceptions import raise_already_exists, raise_not_found
from app.models.enums import InvoiceStatusEnum
from app.models.project import ProjectMilestone, ProjectPaymentPlan
from app.models.sales import Contract, Invoice
from app.schemas.project import MilestoneCreate, MilestoneResponse, MilestoneUpdate


class ProjectMilestoneService(
    BaseCRUDService[ProjectMilestone, MilestoneCreate, MilestoneUpdate, MilestoneResponse]
):
    """Project-scoped milestone CRUD service."""

    search_fields: Sequence[str] = ("milestone_name", "milestone_code", "description")
    allowed_sort_fields: Sequence[str] = (
        "planned_date",
        "created_at",
        "updated_at",
        "milestone_name",
    )
    default_sort_field: str = "planned_date"
    default_sort_order: SortOrder = SortOrder.DESC
    soft_delete_field: Optional[str] = None  # model没有deleted_at字段

    def __init__(self, db: Session, project_id: int):
        super().__init__(
            model=ProjectMilestone,
            db=db,
            response_schema=MilestoneResponse,
            resource_name="里程碑",
            default_filters={"project_id": project_id},
        )
        self.project_id = project_id

    # ------------------------------------------------------------------ #
    # Overrides to enforce project scope and per-project uniqueness
    # ------------------------------------------------------------------ #
    def get(
        self,
        object_id: int,
        *,
        load_relationships: Optional[Sequence[str]] = None,
    ) -> MilestoneResponse:
        db_obj = self._get_object_or_404(object_id, load_relationships=load_relationships)
        return self._to_response(db_obj)

    def delete(
        self,
        object_id: int,
        *,
        soft_delete: Optional[bool] = None,
    ) -> bool:
        self._get_object_or_404(object_id)
        return super().delete(object_id, soft_delete=soft_delete)

    def _before_create(self, obj_in: MilestoneCreate) -> MilestoneCreate:
        payload = obj_in.model_copy(update={"project_id": self.project_id})
        self._ensure_unique_code(payload.milestone_code)
        return payload

    def _before_update(
        self,
        object_id: int,
        obj_in: MilestoneUpdate,
        db_obj: ProjectMilestone,
    ) -> MilestoneUpdate:
        if db_obj.project_id != self.project_id:
            raise_not_found(self.resource_name, object_id)

        updated_code = getattr(obj_in, "milestone_code", None)
        if updated_code:
            self._ensure_unique_code(updated_code, current_id=object_id)

        return obj_in

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _ensure_unique_code(self, milestone_code: Optional[str], current_id: Optional[int] = None) -> None:
        """Ensure milestone_code is unique within the project."""
        if not milestone_code:
            return

        query = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == self.project_id,
            ProjectMilestone.milestone_code == milestone_code,
        )
        if current_id:
            query = query.filter(ProjectMilestone.id != current_id)

        if query.first():
            raise_already_exists(self.resource_name, "milestone_code", milestone_code)

    def _get_object_or_404(
        self,
        object_id: int,
        *,
        load_relationships: Optional[Sequence[str]] = None,
    ) -> ProjectMilestone:
        db_obj = self.repository.get(object_id, load_relationships=load_relationships)
        if not db_obj or db_obj.project_id != self.project_id:
            raise_not_found(self.resource_name, object_id)
        return db_obj

    def complete_milestone(
        self,
        milestone_id: int,
        *,
        actual_date: Optional[date] = None,
        auto_trigger_invoice: bool = True,
    ) -> ProjectMilestone:
        milestone = self._get_object_or_404(milestone_id)
        self._ensure_can_complete(milestone)

        milestone.status = "COMPLETED"
        if actual_date:
            milestone.actual_date = actual_date
        elif not milestone.actual_date:
            milestone.actual_date = date.today()

        self.db.add(milestone)
        self.db.flush()

        if auto_trigger_invoice:
            self._auto_trigger_invoice(milestone_id)

        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    # ------------------------------------------------------------------ #
    # Completion helpers
    # ------------------------------------------------------------------ #
    def _ensure_can_complete(self, milestone: ProjectMilestone) -> None:
        try:
            from app.services.progress_integration_service import ProgressIntegrationService

            integration_service = ProgressIntegrationService(self.db)
            can_complete, missing_items = integration_service.check_milestone_completion_requirements(milestone)

            if not can_complete:
                raise HTTPException(
                    status_code=400,
                    detail=f"里程碑不满足完成条件：{', '.join(missing_items)}"
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.error("检查里程碑完成条件失败: %s", exc, exc_info=True)

    def _auto_trigger_invoice(self, milestone_id: int) -> None:
        payment_plans = (
            self.db.query(ProjectPaymentPlan)
            .filter(
                ProjectPaymentPlan.milestone_id == milestone_id,
                ProjectPaymentPlan.status == "PENDING",
            )
            .all()
        )

        if not payment_plans:
            return

        for plan in payment_plans:
            if plan.invoice_id:
                continue

            contract = None
            if plan.contract_id:
                contract = self.db.query(Contract).filter(Contract.id == plan.contract_id).first()

            if not contract:
                continue

            invoice_code = self._generate_invoice_code()
            invoice = Invoice(
                invoice_code=invoice_code,
                contract_id=contract.id,
                project_id=plan.project_id,
                payment_id=None,
                invoice_type="NORMAL",
                amount=plan.planned_amount,
                tax_rate=Decimal("13"),
                tax_amount=plan.planned_amount * Decimal("13") / Decimal("100"),
                total_amount=plan.planned_amount * Decimal("113") / Decimal("100"),
                status=InvoiceStatusEnum.DRAFT,
                payment_status="PENDING",
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                buyer_name=contract.customer.customer_name if contract.customer else None,
                buyer_tax_no=contract.customer.tax_no if contract.customer else None,
            )
            self.db.add(invoice)
            self.db.flush()

            plan.invoice_id = invoice.id
            plan.invoice_no = invoice_code
            plan.invoice_date = date.today()
            plan.invoice_amount = invoice.total_amount
            plan.status = "INVOICED"
            self.db.add(plan)

    def _generate_invoice_code(self) -> str:
        today = datetime.now()
        prefix = f"INV-{today.strftime('%y%m%d')}-"
        max_invoice = (
            self.db.query(Invoice)
            .filter(Invoice.invoice_code.like(f"{prefix}%"))
            .order_by(desc(Invoice.invoice_code))
            .first()
        )

        if max_invoice:
            try:
                seq = int(max_invoice.invoice_code.split("-")[-1]) + 1
            except (ValueError, TypeError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"

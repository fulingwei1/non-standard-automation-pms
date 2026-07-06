# -*- coding: utf-8 -*-
"""Shared audit helpers for lead-backed sales operation logs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.sales import Lead
from app.models.sales.operation_log import SalesEntityType
from app.models.user import User
from app.services.sales.operation_log_service import SalesOperationLogService


def _audit_scalar(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def lead_audit_value(lead: Lead) -> dict[str, Any]:
    return {
        "lead_id": lead.id,
        "lead_code": lead.lead_code,
        "tenant_id": lead.tenant_id,
        "source": lead.source,
        "customer_name": lead.customer_name,
        "industry": lead.industry,
        "contact_name": lead.contact_name,
        "contact_phone": lead.contact_phone,
        "demand_summary": lead.demand_summary,
        "owner_id": lead.owner_id,
        "status": _audit_scalar(lead.status),
        "next_action_at": _audit_scalar(lead.next_action_at),
        "selected_advantage_products": lead.selected_advantage_products,
        "product_match_type": lead.product_match_type,
        "is_advantage_product": lead.is_advantage_product,
        "requirement_detail_id": lead.requirement_detail_id,
        "assessment_id": lead.assessment_id,
        "completeness": lead.completeness,
        "assignee_id": lead.assignee_id,
        "assessment_status": lead.assessment_status,
        "priority_score": lead.priority_score,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def log_lead_operation(
    db: Session,
    lead: Lead,
    operation_type: str,
    operator: User,
    *,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    operation_desc: str,
    remark: str | None = None,
) -> None:
    old_snapshot = old_value or {}
    new_snapshot = new_value or {}
    SalesOperationLogService.log_operation(
        db,
        entity_type=SalesEntityType.LEAD,
        entity_id=lead.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=lead.lead_code,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=remark,
    )

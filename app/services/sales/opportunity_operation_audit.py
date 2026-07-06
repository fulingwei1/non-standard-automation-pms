# -*- coding: utf-8 -*-
"""Shared audit helpers for opportunity-backed sales operation logs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.sales import Opportunity
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


def opportunity_audit_value(opportunity: Opportunity) -> dict[str, Any]:
    return {
        "opportunity_id": opportunity.id,
        "opp_code": opportunity.opp_code,
        "lead_id": opportunity.lead_id,
        "customer_id": opportunity.customer_id,
        "opp_name": opportunity.opp_name,
        "project_type": opportunity.project_type,
        "equipment_type": opportunity.equipment_type,
        "stage": _audit_scalar(opportunity.stage),
        "probability": opportunity.probability,
        "est_amount": _audit_scalar(opportunity.est_amount),
        "est_margin": _audit_scalar(opportunity.est_margin),
        "expected_close_date": _audit_scalar(opportunity.expected_close_date),
        "closed_at": _audit_scalar(getattr(opportunity, "closed_at", None)),
        "close_reason": getattr(opportunity, "close_reason", None),
        "budget_range": opportunity.budget_range,
        "decision_chain": opportunity.decision_chain,
        "delivery_window": opportunity.delivery_window,
        "acceptance_basis": opportunity.acceptance_basis,
        "score": opportunity.score,
        "risk_level": opportunity.risk_level,
        "owner_id": opportunity.owner_id,
        "updated_by": opportunity.updated_by,
        "gate_status": _audit_scalar(opportunity.gate_status),
        "gate_passed_at": _audit_scalar(opportunity.gate_passed_at),
        "assessment_id": opportunity.assessment_id,
        "requirement_maturity": opportunity.requirement_maturity,
        "assessment_status": opportunity.assessment_status,
        "priority_score": opportunity.priority_score,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def log_opportunity_operation(
    db: Session,
    opportunity: Opportunity,
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
        entity_type=SalesEntityType.OPPORTUNITY,
        entity_id=opportunity.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=opportunity.opp_code,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=remark,
    )

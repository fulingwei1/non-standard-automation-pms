# -*- coding: utf-8 -*-
"""Shared audit helpers for quote-backed sales operation logs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.sales import Quote, QuoteVersion
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


def quote_version_audit_value(version: QuoteVersion | None) -> dict[str, Any] | None:
    if not version:
        return None
    return {
        "version_id": version.id,
        "quote_id": version.quote_id,
        "version_no": version.version_no,
        "status": _audit_scalar(version.status),
        "approval_status": _audit_scalar(version.approval_status),
        "total_price": _audit_scalar(version.total_price),
        "amount_without_tax": _audit_scalar(version.amount_without_tax),
        "tax_rate": _audit_scalar(version.tax_rate),
        "tax_amount": _audit_scalar(version.tax_amount),
        "amount_with_tax": _audit_scalar(version.amount_with_tax),
        "cost_total": _audit_scalar(version.cost_total),
        "gross_margin": _audit_scalar(version.gross_margin),
        "lead_time_days": version.lead_time_days,
        "presale_solution_id": version.presale_solution_id,
        "presale_ticket_id": version.presale_ticket_id,
        "approved_by": version.approved_by,
        "approved_at": _audit_scalar(version.approved_at),
    }


def quote_audit_value(
    quote: Quote,
    *,
    current_version: QuoteVersion | None = None,
) -> dict[str, Any]:
    version = current_version or quote.current_version
    return {
        "quote_id": quote.id,
        "quote_code": quote.quote_code,
        "opportunity_id": quote.opportunity_id,
        "customer_id": quote.customer_id,
        "status": _audit_scalar(quote.status),
        "current_version_id": quote.current_version_id,
        "valid_until": _audit_scalar(quote.valid_until),
        "delivery_date": _audit_scalar(quote.delivery_date),
        "owner_id": quote.owner_id,
        "current_version": quote_version_audit_value(version),
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def log_quote_operation(
    db: Session,
    quote: Quote,
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
        entity_type=SalesEntityType.QUOTE,
        entity_id=quote.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=quote.quote_code,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=remark,
    )


def log_quote_version_operation(
    db: Session,
    version: QuoteVersion,
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
        entity_type=SalesEntityType.QUOTE_VERSION,
        entity_id=version.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=f"{version.quote_id}-{version.version_no}",
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=remark,
    )

# -*- coding: utf-8 -*-
"""Shared audit helpers for invoice-backed sales operation logs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.sales import Invoice
from app.models.sales.operation_log import SalesEntityType
from app.models.user import User
from app.services.sales.operation_log_service import SalesOperationLogService


def audit_scalar(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def invoice_total(invoice: Invoice) -> Decimal:
    return invoice.total_amount or invoice.amount or Decimal("0")


def invoice_paid(invoice: Invoice) -> Decimal:
    return invoice.paid_amount or Decimal("0")


def invoice_audit_value(invoice: Invoice) -> dict[str, Any]:
    total = invoice_total(invoice)
    paid = invoice_paid(invoice)
    return {
        "invoice_id": invoice.id,
        "invoice_code": invoice.invoice_code,
        "contract_id": invoice.contract_id,
        "project_id": invoice.project_id,
        "payment_id": invoice.payment_id,
        "invoice_type": invoice.invoice_type,
        "amount": audit_scalar(invoice.amount),
        "tax_rate": audit_scalar(invoice.tax_rate),
        "tax_amount": audit_scalar(invoice.tax_amount),
        "total_amount": audit_scalar(total),
        "paid_amount": audit_scalar(paid),
        "unpaid_amount": audit_scalar(total - paid),
        "payment_status": invoice.payment_status,
        "paid_date": audit_scalar(invoice.paid_date),
        "status": audit_scalar(invoice.status),
        "issue_date": audit_scalar(invoice.issue_date),
        "due_date": audit_scalar(invoice.due_date),
        "buyer_name": invoice.buyer_name,
        "buyer_tax_no": invoice.buyer_tax_no,
        "remark": invoice.remark,
        "approval_status": invoice.approval_status,
        "approval_instance_id": invoice.approval_instance_id,
    }


def changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def log_invoice_operation(
    db: Session,
    invoice: Invoice,
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
        entity_type=SalesEntityType.INVOICE,
        entity_id=invoice.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=invoice.invoice_code,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=changed_fields(old_snapshot, new_snapshot),
        remark=remark,
    )

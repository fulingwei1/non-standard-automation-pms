# -*- coding: utf-8 -*-
"""Shared audit helpers for customer-backed sales operation logs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.project.customer import Customer
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


def customer_audit_value(customer: Customer) -> dict[str, Any]:
    return {
        "customer_id": customer.id,
        "customer_code": customer.customer_code,
        "customer_name": customer.customer_name,
        "short_name": customer.short_name,
        "customer_type": customer.customer_type,
        "industry": customer.industry,
        "scale": customer.scale,
        "address": customer.address,
        "website": customer.website,
        "credit_limit": _audit_scalar(customer.credit_limit),
        "payment_terms": customer.payment_terms,
        "account_period": customer.account_period,
        "customer_source": customer.customer_source,
        "sales_owner_id": customer.sales_owner_id,
        "status": customer.status,
        "customer_level": customer.customer_level,
        "annual_revenue": _audit_scalar(customer.annual_revenue),
        "cooperation_years": customer.cooperation_years,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def log_customer_operation(
    db: Session,
    customer: Customer,
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
        entity_type=SalesEntityType.CUSTOMER,
        entity_id=customer.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=customer.customer_code,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=remark,
    )

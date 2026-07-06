# -*- coding: utf-8 -*-
"""Shared audit helpers for contract-backed sales operation logs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.sales import Contract
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


def contract_audit_value(contract: Contract) -> dict[str, Any]:
    return {
        "contract_id": contract.id,
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name,
        "contract_type": contract.contract_type,
        "customer_contract_no": contract.customer_contract_no,
        "opportunity_id": contract.opportunity_id,
        "quote_version_id": contract.quote_id,
        "customer_id": contract.customer_id,
        "project_id": contract.project_id,
        "total_amount": _audit_scalar(contract.total_amount),
        "amount_without_tax": _audit_scalar(contract.amount_without_tax),
        "tax_rate": _audit_scalar(contract.tax_rate),
        "tax_amount": _audit_scalar(contract.tax_amount),
        "amount_with_tax": _audit_scalar(contract.amount_with_tax),
        "received_amount": _audit_scalar(contract.received_amount),
        "unreceived_amount": _audit_scalar(contract.unreceived_amount),
        "signing_date": _audit_scalar(contract.signing_date),
        "effective_date": _audit_scalar(contract.effective_date),
        "expiry_date": _audit_scalar(contract.expiry_date),
        "payment_terms": contract.payment_terms,
        "delivery_terms": contract.delivery_terms,
        "contract_subject": contract.contract_subject,
        "status": contract.status,
        "sales_owner_id": contract.sales_owner_id,
        "contract_manager_id": contract.contract_manager_id,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def log_contract_operation(
    db: Session,
    contract: Contract,
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
        entity_type=SalesEntityType.CONTRACT,
        entity_id=contract.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=contract.contract_code,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=remark,
    )

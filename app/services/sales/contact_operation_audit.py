# -*- coding: utf-8 -*-
"""Shared audit helpers for contact-backed sales operation logs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.sales.contacts import Contact
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


def contact_audit_value(contact: Contact) -> dict[str, Any]:
    return {
        "contact_id": contact.id,
        "customer_id": contact.customer_id,
        "name": contact.name,
        "position": contact.position,
        "department": contact.department,
        "mobile": contact.mobile,
        "phone": contact.phone,
        "email": contact.email,
        "wechat": contact.wechat,
        "birthday": _audit_scalar(contact.birthday),
        "hobbies": contact.hobbies,
        "notes": contact.notes,
        "is_primary": contact.is_primary,
        "decision_role": contact.decision_role,
        "influence_level": contact.influence_level,
        "attitude": contact.attitude,
        "relationship_strength": contact.relationship_strength,
        "last_contact_date": _audit_scalar(contact.last_contact_date),
        "key_concerns": contact.key_concerns,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def log_contact_operation(
    db: Session,
    contact: Contact,
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
        entity_type=SalesEntityType.CONTACT,
        entity_id=contact.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=contact.name,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=remark,
    )

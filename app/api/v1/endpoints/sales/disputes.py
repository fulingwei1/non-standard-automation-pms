# -*- coding: utf-8 -*-
"""
回款争议管理 API endpoints
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.sales import ReceivableDispute
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import ReceivableDisputeCreate, ReceivableDisputeResponse
from app.services.sales.operation_log_service import SalesOperationLogService

router = APIRouter()


def _audit_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _dispute_audit_value(dispute: ReceivableDispute) -> dict[str, Any]:
    return {
        "dispute_id": dispute.id,
        "payment_id": dispute.payment_id,
        "reason_code": dispute.reason_code,
        "description": dispute.description,
        "status": _audit_value(dispute.status),
        "responsible_dept": dispute.responsible_dept,
        "responsible_id": dispute.responsible_id,
        "expect_resolve_date": _audit_value(dispute.expect_resolve_date),
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def _log_dispute_operation(
    db: Session,
    dispute: ReceivableDispute,
    operation_type: str,
    operator: User,
    *,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    operation_desc: str,
) -> None:
    old_snapshot = old_value or {}
    new_snapshot = new_value or {}
    SalesOperationLogService.log_operation(
        db,
        entity_type=SalesEntityType.RECEIVABLE_DISPUTE,
        entity_id=dispute.id,
        entity_code=f"DISPUTE-{dispute.id}",
        operation_type=operation_type,
        operator=operator,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=dispute.reason_code,
    )


@router.get("/disputes", response_model=PaginatedResponse[ReceivableDisputeResponse])
def read_disputes(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取回款争议列表
    """
    query = db.query(ReceivableDispute)

    if status:
        query = query.filter(ReceivableDispute.status == status)

    total = query.count()
    disputes = apply_pagination(
        query.order_by(desc(ReceivableDispute.created_at)), pagination.offset, pagination.limit
    ).all()

    dispute_responses = []
    for dispute in disputes:
        dispute_dict = {
            **{c.name: getattr(dispute, c.name) for c in dispute.__table__.columns},
            "responsible_name": dispute.responsible.real_name if dispute.responsible else None,
        }
        dispute_responses.append(ReceivableDisputeResponse(**dispute_dict))

    return PaginatedResponse(
        items=dispute_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.post("/disputes", response_model=ReceivableDisputeResponse, status_code=201)
def create_dispute(
    *,
    db: Session = Depends(deps.get_db),
    dispute_in: ReceivableDisputeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建回款争议
    """
    dispute = ReceivableDispute(**dispute_in.model_dump())
    db.add(dispute)
    db.flush()
    _log_dispute_operation(
        db,
        dispute,
        SalesOperationType.CREATE,
        current_user,
        new_value=_dispute_audit_value(dispute),
        operation_desc="创建回款争议",
    )
    db.commit()
    db.refresh(dispute)

    dispute_dict = {
        **{c.name: getattr(dispute, c.name) for c in dispute.__table__.columns},
        "responsible_name": dispute.responsible.real_name if dispute.responsible else None,
    }
    return ReceivableDisputeResponse(**dispute_dict)

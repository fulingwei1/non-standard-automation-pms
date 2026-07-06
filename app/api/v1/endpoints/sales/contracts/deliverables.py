# -*- coding: utf-8 -*-
"""
合同交付物与变更 API endpoints
包括：交付物清单、合同变更记录
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, ContractAmendment, ContractDeliverable
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.sales import (
    ContractAmendmentCreate,
    ContractAmendmentResponse,
    ContractDeliverableResponse,
)
from app.services.sales.contract_operation_audit import (
    contract_audit_value,
    log_contract_operation,
)
from app.utils.db_helpers import get_or_404

from ..utils import generate_amendment_no

router = APIRouter()


def _audit_scalar(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _contract_amendment_audit_value(amendment: ContractAmendment) -> dict[str, Any]:
    fields = [
        "id",
        "contract_id",
        "amendment_no",
        "amendment_type",
        "title",
        "description",
        "reason",
        "old_value",
        "new_value",
        "amount_change",
        "schedule_impact",
        "other_impact",
        "requestor_id",
        "request_date",
        "status",
        "approver_id",
        "approval_date",
        "approval_comment",
        "attachments",
    ]
    return {field: _audit_scalar(getattr(amendment, field, None)) for field in fields}


def _contract_amendment_audit_values(
    db: Session, contract_id: int
) -> list[dict[str, Any]]:
    return [
        _contract_amendment_audit_value(amendment)
        for amendment in db.query(ContractAmendment)
        .filter(ContractAmendment.contract_id == contract_id)
        .order_by(ContractAmendment.id)
        .all()
    ]


def _amendment_input_value(payload: ContractAmendmentCreate, field: str) -> Any:
    return getattr(payload, field, None)


def _build_amendment_response(amendment: ContractAmendment) -> dict[str, Any]:
    return {
        "id": amendment.id,
        "contract_id": amendment.contract_id,
        "amendment_no": amendment.amendment_no,
        "amendment_type": amendment.amendment_type,
        "title": amendment.title,
        "description": amendment.description,
        "reason": amendment.reason,
        "old_value": amendment.old_value,
        "new_value": amendment.new_value,
        "amount_change": amendment.amount_change,
        "schedule_impact": amendment.schedule_impact,
        "other_impact": amendment.other_impact,
        "requestor_id": amendment.requestor_id,
        "requestor_name": amendment.requestor.real_name if amendment.requestor else None,
        "request_date": amendment.request_date,
        "status": amendment.status,
        "approver_id": amendment.approver_id,
        "approver_name": amendment.approver.real_name if amendment.approver else None,
        "approval_date": amendment.approval_date,
        "approval_comment": amendment.approval_comment,
        "attachments": amendment.attachments,
        "amendment_reason": amendment.reason or "",
        "amendment_content": amendment.description,
        "amendment_amount": amendment.amount_change,
        "effective_date": amendment.request_date,
        "remark": amendment.other_impact,
        "created_by_name": amendment.requestor.real_name if amendment.requestor else None,
        "created_at": amendment.created_at,
        "updated_at": amendment.updated_at,
    }


def _check_contract_scope(db: Session, contract_id: int, current_user: User) -> Contract:
    """加载合同并检查数据权限，返回 Contract 或抛 403"""
    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")
    if not security.check_sales_data_permission(contract, current_user, db, "sales_owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该合同")
    return contract


@router.get(
    "/contracts/{contract_id}/deliverables", response_model=List[ContractDeliverableResponse]
)
def get_contract_deliverables(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.require_permission("contract:view")),
) -> Any:
    """
    获取合同交付物清单
    """
    _check_contract_scope(db, contract_id, current_user)

    deliverables = (
        db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()
    )
    return [
        ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns})
        for d in deliverables
    ]


@router.get("/contracts/{contract_id}/amendments", response_model=List[ContractAmendmentResponse])
def get_contract_amendments(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("contract:view")),
) -> Any:
    """
    获取合同变更记录列表
    """
    _check_contract_scope(db, contract_id, current_user)

    query = db.query(ContractAmendment).filter(ContractAmendment.contract_id == contract_id)

    if status:
        query = query.filter(ContractAmendment.status == status)

    amendments = query.order_by(
        desc(ContractAmendment.request_date), desc(ContractAmendment.created_at)
    ).all()

    return [_build_amendment_response(amendment) for amendment in amendments]


@router.post(
    "/contracts/{contract_id}/amendments", response_model=ContractAmendmentResponse, status_code=201
)
def create_contract_amendment(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    amendment_in: ContractAmendmentCreate,
    current_user: User = Depends(security.require_permission("contract:update")),
) -> Any:
    """
    创建合同变更记录
    """
    contract = _check_contract_scope(db, contract_id, current_user)

    # 生成变更编号
    amendment_no = generate_amendment_no(db, contract.contract_code)
    old_contract = contract_audit_value(contract)
    old_contract["contract_amendments"] = _contract_amendment_audit_values(
        db, contract.id
    )

    amendment_type = amendment_in.amendment_type
    description = (
        _amendment_input_value(amendment_in, "description")
        or _amendment_input_value(amendment_in, "amendment_content")
        or amendment_type
    )
    title = (
        _amendment_input_value(amendment_in, "title")
        or description[:200]
        or f"{amendment_type}变更"
    )
    amount_change = _amendment_input_value(amendment_in, "amount_change")
    if amount_change is None:
        amount_change = _amendment_input_value(amendment_in, "amendment_amount")

    amendment = ContractAmendment(
        contract_id=contract_id,
        amendment_no=amendment_no,
        amendment_type=amendment_type,
        title=title,
        description=description,
        reason=(
            _amendment_input_value(amendment_in, "reason")
            or _amendment_input_value(amendment_in, "amendment_reason")
        ),
        old_value=_amendment_input_value(amendment_in, "old_value"),
        new_value=_amendment_input_value(amendment_in, "new_value"),
        amount_change=amount_change,
        schedule_impact=_amendment_input_value(amendment_in, "schedule_impact"),
        other_impact=(
            _amendment_input_value(amendment_in, "other_impact")
            or _amendment_input_value(amendment_in, "remark")
        ),
        requestor_id=current_user.id,
        request_date=(
            _amendment_input_value(amendment_in, "request_date")
            or _amendment_input_value(amendment_in, "effective_date")
            or date.today()
        ),
        status="PENDING",
        attachments=_amendment_input_value(amendment_in, "attachments"),
    )

    db.add(amendment)
    db.flush()

    new_contract = contract_audit_value(contract)
    new_contract["contract_amendments"] = _contract_amendment_audit_values(
        db, contract.id
    )
    log_contract_operation(
        db,
        contract,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_contract,
        new_value=new_contract,
        operation_desc="创建合同变更记录",
        remark=amendment.reason,
    )
    db.commit()
    db.refresh(amendment)

    return _build_amendment_response(amendment)

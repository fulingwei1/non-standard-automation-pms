# -*- coding: utf-8 -*-
"""
合同交付物与变更 API endpoints
包括：交付物清单、合同变更记录
"""

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, ContractAmendment, ContractDeliverable
from app.models.user import User
from app.schemas.sales import (
    ContractAmendmentCreate,
    ContractAmendmentResponse,
    ContractDeliverableResponse,
)

from ..utils import generate_amendment_no

router = APIRouter()


@router.get("/contracts/{contract_id}/deliverables", response_model=List[ContractDeliverableResponse])
def get_contract_deliverables(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同交付物清单
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()
    return [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables]


@router.get("/contracts/{contract_id}/amendments", response_model=List[ContractAmendmentResponse])
def get_contract_amendments(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同变更记录列表
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    query = db.query(ContractAmendment).filter(ContractAmendment.contract_id == contract_id)

    if status:
        query = query.filter(ContractAmendment.status == status)

    amendments = query.order_by(desc(ContractAmendment.request_date), desc(ContractAmendment.created_at)).all()

    result = []
    for amendment in amendments:
        result.append({
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
            "created_at": amendment.created_at,
            "updated_at": amendment.updated_at,
        })

    return result


@router.post("/contracts/{contract_id}/amendments", response_model=ContractAmendmentResponse, status_code=201)
def create_contract_amendment(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    amendment_in: ContractAmendmentCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建合同变更记录
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 生成变更编号
    amendment_no = generate_amendment_no(db, contract.contract_code)

    amendment = ContractAmendment(
        contract_id=contract_id,
        amendment_no=amendment_no,
        amendment_type=amendment_in.amendment_type,
        title=amendment_in.title,
        description=amendment_in.description,
        reason=amendment_in.reason,
        old_value=amendment_in.old_value,
        new_value=amendment_in.new_value,
        amount_change=amendment_in.amount_change,
        schedule_impact=amendment_in.schedule_impact,
        other_impact=amendment_in.other_impact,
        requestor_id=current_user.id,
        request_date=amendment_in.request_date,
        status="PENDING",
        attachments=amendment_in.attachments,
    )

    db.add(amendment)
    db.commit()
    db.refresh(amendment)

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
        "created_at": amendment.created_at,
        "updated_at": amendment.updated_at,
    }

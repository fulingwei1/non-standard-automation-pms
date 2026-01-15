# -*- coding: utf-8 -*-
"""
多级审批 - 自动生成
从 sales/quotes.py 拆分
"""

from typing import Any, List, Optional

from datetime import datetime

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session, joinedload

from sqlalchemy import desc, or_

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.sales import (

from app.schemas.sales import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/quote-approvals",
    tags=["approvals_multi"]
)

# 共 2 个路由

@router.put("/quote-approvals/{approval_id}/approve", response_model=QuoteApprovalResponse)
def approve_quote_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    approval_opinion: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过（多级审批）
    """
    approval = db.query(QuoteApproval).filter(QuoteApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限
    if not security.check_sales_approval_permission(current_user, approval, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此记录"
        )

    approval.approval_result = "APPROVED"
    approval.approval_opinion = approval_opinion
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 检查是否所有审批都已完成
    quote = db.query(Quote).filter(Quote.id == approval.quote_id).first()
    if quote:
        pending_approvals = db.query(QuoteApproval).filter(
            QuoteApproval.quote_id == approval.quote_id,
            QuoteApproval.status == "PENDING"
        ).count()

        if pending_approvals == 0:
            # 所有审批都已完成，更新报价状态
            quote.status = "APPROVED"
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            if version:
                version.approved_by = current_user.id
                version.approved_at = datetime.now()

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return QuoteApprovalResponse(
        id=approval.id,
        quote_id=approval.quote_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/quote-approvals/{approval_id}/reject", response_model=QuoteApprovalResponse)
def reject_quote_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回（多级审批）
    """
    approval = db.query(QuoteApproval).filter(QuoteApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限
    if not security.check_sales_approval_permission(current_user, approval, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此记录"
        )

    approval.approval_result = "REJECTED"
    approval.approval_opinion = rejection_reason
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 驳回后，报价状态变为被拒
    quote = db.query(Quote).filter(Quote.id == approval.quote_id).first()
    if quote:
        quote.status = "REJECTED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return QuoteApprovalResponse(
        id=approval.id,
        quote_id=approval.quote_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )




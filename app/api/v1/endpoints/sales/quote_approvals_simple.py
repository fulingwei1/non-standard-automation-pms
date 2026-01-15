# -*- coding: utf-8 -*-
"""
单级审批 - 自动生成
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
    prefix="/quotes/{quote_id}/approvals",
    tags=["approvals_simple"]
)

# 共 2 个路由

# ==================== 单级审批（兼容旧接口） ====================


@router.post("/quotes/{quote_id}/approve", response_model=ResponseModel)
def approve_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approve_request: QuoteApproveRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批报价（单级审批，兼容旧接口）
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if not quote.current_version_id:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    if approve_request.approved:
        quote.status = "APPROVED"
        version.approved_by = current_user.id
        version.approved_at = datetime.now()
    else:
        quote.status = "REJECTED"

    db.commit()

    return ResponseModel(
        code=200,
        message="报价审批完成" if approve_request.approved else "报价已驳回"
    )


@router.get("/quotes/{quote_id}/approvals", response_model=List[QuoteApprovalResponse])
def get_quote_approvals(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价审批记录列表
    """
    approvals = db.query(QuoteApproval).filter(QuoteApproval.quote_id == quote_id).order_by(QuoteApproval.approval_level).all()

    result = []
    for approval in approvals:
        approver_name = None
        if approval.approver_id:
            approver = db.query(User).filter(User.id == approval.approver_id).first()
            approver_name = approver.real_name if approver else None

        result.append(QuoteApprovalResponse(
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
        ))

    return result


# ==================== 多级审批 ====================




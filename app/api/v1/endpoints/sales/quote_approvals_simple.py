# -*- coding: utf-8 -*-
"""
报价简单审批
包含：单级审批操作
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteVersion
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/quotes/{quote_id}/approve", response_model=ResponseModel)
def simple_approve(
    quote_id: int,
    decision: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    简单审批（单级审批）

    Args:
        quote_id: 报价ID
        decision: 决策（approved: bool, comment: str）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 审批结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status not in ["DRAFT", "PENDING_APPROVAL"]:
        raise HTTPException(status_code=400, detail=f"当前状态({quote.status})不能审批")

    approved = decision.get("approved", True)
    comment = decision.get("comment", "")

    if approved:
        quote.status = "APPROVED"

        # 更新版本审批信息
        if quote.current_version_id:
            version = db.query(QuoteVersion).filter(
                QuoteVersion.id == quote.current_version_id
            ).first()
            if version:
                version.approved_by = current_user.id
                version.approved_at = datetime.now()

        message = "报价审批通过"
    else:
        quote.status = "REJECTED"
        message = "报价审批拒绝"

    db.commit()

    return ResponseModel(
        code=200,
        message=message,
        data={
            "quote_id": quote_id,
            "status": quote.status,
            "approved_by": current_user.real_name or current_user.username,
            "comment": comment
        }
    )


@router.post("/quotes/{quote_id}/reject", response_model=ResponseModel)
def simple_reject(
    quote_id: int,
    reason: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    拒绝报价

    Args:
        quote_id: 报价ID
        reason: 拒绝原因
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 拒绝结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    quote.status = "REJECTED"
    db.commit()

    return ResponseModel(
        code=200,
        message="报价已拒绝",
        data={
            "quote_id": quote_id,
            "status": quote.status,
            "reason": reason.get("reason", "")
        }
    )


@router.post("/quotes/{quote_id}/revise", response_model=ResponseModel)
def request_revision(
    quote_id: int,
    request_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    要求修改（退回修改）

    Args:
        quote_id: 报价ID
        request_data: 修改要求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 操作结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status not in ["PENDING_APPROVAL"]:
        raise HTTPException(status_code=400, detail="只有待审批状态可以退回修改")

    quote.status = "REVISION_REQUIRED"
    db.commit()

    return ResponseModel(
        code=200,
        message="已退回修改",
        data={
            "quote_id": quote_id,
            "status": quote.status,
            "revision_notes": request_data.get("notes", "")
        }
    )

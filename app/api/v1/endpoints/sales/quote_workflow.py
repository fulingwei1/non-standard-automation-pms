# -*- coding: utf-8 -*-
"""
报价工作流管理
包含：提交审批、撤回、获取审批历史
"""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteApproval
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/quotes/{quote_id}/submit", response_model=ResponseModel)
def submit_quote_for_approval(
    quote_id: int,
    submit_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    提交报价审批

    Args:
        quote_id: 报价ID
        submit_data: 提交数据（可包含审批人ID等）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 提交结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status not in ["DRAFT", "REJECTED"]:
        raise HTTPException(status_code=400, detail=f"当前状态({quote.status})不能提交审批")

    # 更新状态为待审批
    quote.status = "PENDING_APPROVAL"

    # 创建审批记录
    approver_id = submit_data.get("approver_id")
    approval = QuoteApproval(
        quote_id=quote_id,
        approval_level=1,
        approval_role="SALES_MANAGER",
        approver_id=approver_id,
        status="PENDING",
    )
    db.add(approval)
    db.commit()

    return ResponseModel(
        code=200,
        message="报价已提交审批",
        data={"quote_id": quote_id, "status": quote.status}
    )


@router.post("/quotes/{quote_id}/withdraw", response_model=ResponseModel)
def withdraw_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    撤回报价审批

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 撤回结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail="只有待审批状态的报价可以撤回")

    # 检查是否是报价负责人
    if quote.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有报价负责人可以撤回")

    # 更新状态
    quote.status = "DRAFT"

    # 取消待处理的审批记录
    pending_approvals = db.query(QuoteApproval).filter(
        QuoteApproval.quote_id == quote_id,
        QuoteApproval.status == "PENDING"
    ).all()
    for approval in pending_approvals:
        approval.status = "CANCELLED"

    db.commit()

    return ResponseModel(
        code=200,
        message="报价已撤回",
        data={"quote_id": quote_id, "status": quote.status}
    )


@router.get("/quotes/{quote_id}/workflow/history", response_model=ResponseModel)
def get_workflow_history(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价审批历史

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 审批历史
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    approvals = db.query(QuoteApproval).filter(
        QuoteApproval.quote_id == quote_id
    ).order_by(desc(QuoteApproval.created_at)).all()

    history = [{
        "id": a.id,
        "approval_level": a.approval_level,
        "approval_role": a.approval_role,
        "approver_id": a.approver_id,
        "approver_name": a.approver_name,
        "approval_result": a.approval_result,
        "approval_opinion": a.approval_opinion,
        "status": a.status,
        "approved_at": a.approved_at.isoformat() if a.approved_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in approvals]

    return ResponseModel(
        code=200,
        message="获取审批历史成功",
        data={"quote_id": quote_id, "history": history}
    )


@router.get("/quotes/workflow/pending", response_model=ResponseModel)
def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取当前用户待审批的报价列表

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 待审批列表
    """
    pending = db.query(QuoteApproval).filter(
        QuoteApproval.approver_id == current_user.id,
        QuoteApproval.status == "PENDING"
    ).all()

    quote_ids = [a.quote_id for a in pending]
    quotes = db.query(Quote).filter(Quote.id.in_(quote_ids)).all() if quote_ids else []
    quote_map = {q.id: q for q in quotes}

    pending_list = [{
        "approval_id": a.id,
        "quote_id": a.quote_id,
        "quote_code": quote_map.get(a.quote_id).quote_code if quote_map.get(a.quote_id) else None,
        "approval_level": a.approval_level,
        "approval_role": a.approval_role,
        "due_date": a.due_date.isoformat() if a.due_date else None,
        "is_overdue": a.is_overdue,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in pending]

    return ResponseModel(
        code=200,
        message="获取待审批列表成功",
        data={"count": len(pending_list), "items": pending_list}
    )

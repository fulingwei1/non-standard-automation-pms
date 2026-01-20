# -*- coding: utf-8 -*-
"""
报价成本审批管理
包含：成本审批列表、发起成本审批、审批操作
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteVersion, QuoteCostApproval
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/quotes/{quote_id}/cost-approvals", response_model=ResponseModel)
def get_cost_approvals(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价的成本审批记录

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 成本审批列表
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    approvals = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.quote_id == quote_id
    ).order_by(desc(QuoteCostApproval.created_at)).all()

    approvals_data = [{
        "id": a.id,
        "quote_version_id": a.quote_version_id,
        "approval_status": a.approval_status,
        "approval_level": a.approval_level,
        "current_approver_id": a.current_approver_id,
        "total_price": float(a.total_price) if a.total_price else None,
        "cost_total": float(a.cost_total) if a.cost_total else None,
        "gross_margin": float(a.gross_margin) if a.gross_margin else None,
        "margin_warning": a.margin_warning,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in approvals]

    return ResponseModel(
        code=200,
        message="获取成本审批列表成功",
        data={"quote_id": quote_id, "approvals": approvals_data}
    )


@router.post("/quotes/{quote_id}/cost-approvals", response_model=ResponseModel)
def create_cost_approval(
    quote_id: int,
    approval_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    发起成本审批

    Args:
        quote_id: 报价ID
        approval_data: 审批数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version_id = approval_data.get("quote_version_id") or quote.current_version_id
    if not version_id:
        raise HTTPException(status_code=400, detail="请指定报价版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    # 检查是否有未完成的成本审批
    pending = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.quote_id == quote_id,
        QuoteCostApproval.quote_version_id == version_id,
        QuoteCostApproval.approval_status == "PENDING"
    ).first()
    if pending:
        raise HTTPException(status_code=400, detail="该版本已有待审批的成本审批记录")

    # 检查毛利率是否低于预警线
    margin_warning = False
    min_margin = approval_data.get("min_margin", 15.0)  # 默认15%
    if version.gross_margin and float(version.gross_margin) < min_margin:
        margin_warning = True

    approval = QuoteCostApproval(
        quote_id=quote_id,
        quote_version_id=version_id,
        approval_status="PENDING",
        approval_level=1,
        current_approver_id=approval_data.get("approver_id"),
        total_price=version.total_price,
        cost_total=version.cost_total,
        gross_margin=version.gross_margin,
        margin_warning=margin_warning,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    return ResponseModel(
        code=200,
        message="成本审批已发起",
        data={
            "id": approval.id,
            "margin_warning": margin_warning,
            "approval_level": approval.approval_level
        }
    )


@router.post("/quotes/cost-approvals/{approval_id}/approve", response_model=ResponseModel)
def approve_cost(
    approval_id: int,
    action_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    执行成本审批操作

    Args:
        approval_id: 审批ID
        action_data: 操作数据（action: approve/reject, comment）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 操作结果
    """
    approval = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.id == approval_id
    ).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.approval_status != "PENDING":
        raise HTTPException(status_code=400, detail="该审批已完成")

    # 检查审批权限
    if approval.current_approver_id and approval.current_approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="您没有审批权限")

    action = action_data.get("action", "approve")
    comment = action_data.get("comment", "")

    if action == "approve":
        approval.approval_status = "APPROVED"
        approval.approved_at = datetime.now()
        approval.approved_by = current_user.id
        approval.approval_comment = comment
        message = "成本审批已通过"
    elif action == "reject":
        approval.approval_status = "REJECTED"
        approval.approved_at = datetime.now()
        approval.approved_by = current_user.id
        approval.approval_comment = comment
        message = "成本审批已拒绝"
    else:
        raise HTTPException(status_code=400, detail="无效的操作")

    db.commit()

    return ResponseModel(
        code=200,
        message=message,
        data={"id": approval.id, "status": approval.approval_status}
    )


@router.get("/quotes/cost-approvals/pending", response_model=ResponseModel)
def get_my_pending_cost_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取我的待审批成本审批列表

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 待审批列表
    """
    pending = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.current_approver_id == current_user.id,
        QuoteCostApproval.approval_status == "PENDING"
    ).order_by(desc(QuoteCostApproval.created_at)).all()

    items = [{
        "id": a.id,
        "quote_id": a.quote_id,
        "quote_version_id": a.quote_version_id,
        "total_price": float(a.total_price) if a.total_price else None,
        "cost_total": float(a.cost_total) if a.cost_total else None,
        "gross_margin": float(a.gross_margin) if a.gross_margin else None,
        "margin_warning": a.margin_warning,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in pending]

    return ResponseModel(
        code=200,
        message="获取待审批列表成功",
        data={"count": len(items), "items": items}
    )

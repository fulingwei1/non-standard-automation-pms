# -*- coding: utf-8 -*-
"""
报价多级审批管理
包含：多级审批流程配置、审批链操作
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteApproval
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


# 审批层级配置
APPROVAL_LEVELS = {
    1: {"role": "SALES_MANAGER", "name": "销售经理"},
    2: {"role": "SALES_DIRECTOR", "name": "销售总监"},
    3: {"role": "GM", "name": "总经理"},
}


@router.get("/quotes/{quote_id}/approvals", response_model=ResponseModel)
def get_quote_approvals(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价审批链

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 审批链
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    approvals = db.query(QuoteApproval).filter(
        QuoteApproval.quote_id == quote_id
    ).order_by(QuoteApproval.approval_level, desc(QuoteApproval.created_at)).all()

    chain = [{
        "id": a.id,
        "level": a.approval_level,
        "role": a.approval_role,
        "role_name": APPROVAL_LEVELS.get(a.approval_level, {}).get("name", a.approval_role),
        "approver_id": a.approver_id,
        "approver_name": a.approver_name,
        "status": a.status,
        "result": a.approval_result,
        "opinion": a.approval_opinion,
        "approved_at": a.approved_at.isoformat() if a.approved_at else None,
        "is_overdue": a.is_overdue,
    } for a in approvals]

    # 当前审批层级
    current_level = None
    for a in approvals:
        if a.status == "PENDING":
            current_level = a.approval_level
            break

    return ResponseModel(
        code=200,
        message="获取审批链成功",
        data={
            "quote_id": quote_id,
            "quote_status": quote.status,
            "current_level": current_level,
            "total_levels": len(APPROVAL_LEVELS),
            "chain": chain
        }
    )


@router.post("/quotes/{quote_id}/approvals/start-multi", response_model=ResponseModel)
def start_multi_level_approval(
    quote_id: int,
    config: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    启动多级审批流程

    Args:
        quote_id: 报价ID
        config: 配置（levels: 审批层级数，approvers: 各级审批人）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 启动结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status not in ["DRAFT", "REJECTED"]:
        raise HTTPException(status_code=400, detail="当前状态不能发起审批")

    levels = config.get("levels", 2)
    approvers = config.get("approvers", {})

    # 创建各级审批记录
    created = []
    for level in range(1, levels + 1):
        level_config = APPROVAL_LEVELS.get(level, {})
        approver_id = approvers.get(str(level))

        approval = QuoteApproval(
            quote_id=quote_id,
            approval_level=level,
            approval_role=level_config.get("role", f"LEVEL_{level}"),
            approver_id=approver_id,
            status="PENDING" if level == 1 else "WAITING",
        )
        db.add(approval)
        created.append({"level": level, "role": level_config.get("name", f"第{level}级")})

    quote.status = "PENDING_APPROVAL"
    db.commit()

    return ResponseModel(
        code=200,
        message=f"已启动{levels}级审批流程",
        data={"quote_id": quote_id, "levels": created}
    )


@router.post("/quotes/approvals/{approval_id}/decide", response_model=ResponseModel)
def decide_approval(
    approval_id: int,
    decision: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    审批决策

    Args:
        approval_id: 审批ID
        decision: 决策（action: approve/reject, opinion）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 决策结果
    """
    approval = db.query(QuoteApproval).filter(QuoteApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="该审批不在待处理状态")

    # 权限检查
    if approval.approver_id and approval.approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="您没有审批权限")

    action = decision.get("action", "approve")
    opinion = decision.get("opinion", "")

    approval.approver_name = current_user.real_name or current_user.username
    approval.approval_opinion = opinion
    approval.approved_at = datetime.now()

    quote = db.query(Quote).filter(Quote.id == approval.quote_id).first()

    if action == "approve":
        approval.status = "APPROVED"
        approval.approval_result = "APPROVED"

        # 检查是否还有下一级审批
        next_approval = db.query(QuoteApproval).filter(
            QuoteApproval.quote_id == approval.quote_id,
            QuoteApproval.approval_level == approval.approval_level + 1,
            QuoteApproval.status == "WAITING"
        ).first()

        if next_approval:
            next_approval.status = "PENDING"
            message = f"第{approval.approval_level}级审批通过，已转至下一级"
        else:
            quote.status = "APPROVED"
            message = "全部审批通过"

    elif action == "reject":
        approval.status = "REJECTED"
        approval.approval_result = "REJECTED"
        quote.status = "REJECTED"

        # 取消后续审批
        db.query(QuoteApproval).filter(
            QuoteApproval.quote_id == approval.quote_id,
            QuoteApproval.status == "WAITING"
        ).update({"status": "CANCELLED"})

        message = "审批已拒绝"
    else:
        raise HTTPException(status_code=400, detail="无效的操作")

    db.commit()

    return ResponseModel(
        code=200,
        message=message,
        data={
            "approval_id": approval.id,
            "quote_status": quote.status,
            "action": action
        }
    )

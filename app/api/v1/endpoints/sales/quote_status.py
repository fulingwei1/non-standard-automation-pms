# -*- coding: utf-8 -*-
"""
报价状态管理
包含：状态定义、状态转换、状态历史
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteApproval
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.status_update_service import StatusUpdateService
from app.utils.db_helpers import get_or_404

router = APIRouter()

# 状态定义
QUOTE_STATUSES = {
    "DRAFT": {"name": "草稿", "color": "gray", "order": 1},
    "PENDING_APPROVAL": {"name": "待审批", "color": "yellow", "order": 2},
    "IN_REVIEW": {"name": "审核中", "color": "blue", "order": 3},
    "APPROVED": {"name": "已批准", "color": "green", "order": 4},
    "REJECTED": {"name": "已拒绝", "color": "red", "order": 5},
    "REVISION_REQUIRED": {"name": "需修改", "color": "orange", "order": 6},
    "SENT": {"name": "已发送", "color": "cyan", "order": 7},
    "ACCEPTED": {"name": "已接受", "color": "green", "order": 8},
    "CONVERTED": {"name": "已转换", "color": "purple", "order": 9},
    "EXPIRED": {"name": "已过期", "color": "gray", "order": 10},
    "CANCELLED": {"name": "已取消", "color": "gray", "order": 11},
}

# 状态转换规则
STATUS_TRANSITIONS = {
    "DRAFT": ["PENDING_APPROVAL", "CANCELLED"],
    "PENDING_APPROVAL": ["IN_REVIEW", "APPROVED", "REJECTED", "DRAFT"],
    "IN_REVIEW": ["APPROVED", "REJECTED", "REVISION_REQUIRED"],
    "APPROVED": ["SENT", "EXPIRED", "CANCELLED"],
    "REJECTED": ["DRAFT", "CANCELLED"],
    "REVISION_REQUIRED": ["DRAFT", "PENDING_APPROVAL"],
    "SENT": ["ACCEPTED", "REJECTED", "EXPIRED"],
    "ACCEPTED": ["CONVERTED"],
    "CONVERTED": [],
    "EXPIRED": ["DRAFT"],
    "CANCELLED": [],
}


@router.get("/quotes/statuses", response_model=ResponseModel)
def get_all_statuses(
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取所有报价状态定义

    Args:
        current_user: 当前用户

    Returns:
        ResponseModel: 状态定义列表
    """
    statuses = [{
        "code": code,
        "name": info["name"],
        "color": info["color"],
        "order": info["order"],
        "allowed_transitions": STATUS_TRANSITIONS.get(code, [])
    } for code, info in QUOTE_STATUSES.items()]

    statuses.sort(key=lambda x: x["order"])

    return ResponseModel(
        code=200,
        message="获取状态定义成功",
        data={"statuses": statuses}
    )


@router.get("/quotes/{quote_id}/status", response_model=ResponseModel)
def get_quote_status(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价当前状态及可转换状态

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 状态信息
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    current_status = quote.status
    status_info = QUOTE_STATUSES.get(current_status, {"name": current_status, "color": "gray"})
    allowed_transitions = STATUS_TRANSITIONS.get(current_status, [])

    return ResponseModel(
        code=200,
        message="获取状态成功",
        data={
            "quote_id": quote_id,
            "current_status": current_status,
            "status_name": status_info["name"],
            "status_color": status_info["color"],
            "allowed_transitions": [{
                "code": t,
                "name": QUOTE_STATUSES.get(t, {}).get("name", t)
            } for t in allowed_transitions]
        }
    )


@router.post("/quotes/{quote_id}/status", response_model=ResponseModel)
def change_quote_status(
    quote_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    变更报价状态

    Args:
        quote_id: 报价ID
        status_data: 状态数据（new_status, reason）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 变更结果
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    new_status = status_data.get("new_status")
    if not new_status:
        raise HTTPException(status_code=400, detail="请指定目标状态")

    # 使用通用 StatusUpdateService 进行状态转换验证和更新
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=quote,
        new_status=new_status,
        operator=current_user,
        valid_statuses=list(QUOTE_STATUSES.keys()),
        transition_rules=STATUS_TRANSITIONS,
        timestamp_fields={},  # quote.updated_at 由 save_obj 处理
    )

    if not result.success:
        old_name = QUOTE_STATUSES.get(result.old_status, {}).get("name", result.old_status)
        new_name = QUOTE_STATUSES.get(new_status, {}).get("name", new_status)
        raise HTTPException(
            status_code=400,
            detail=f"不能从 {old_name} 转换为 {new_name}",
        )

    db.commit()

    old_name = QUOTE_STATUSES.get(result.old_status, {}).get("name", result.old_status)
    new_name = QUOTE_STATUSES.get(result.new_status, {}).get("name", result.new_status)
    return ResponseModel(
        code=200,
        message=f"状态已从 {old_name} 变更为 {new_name}",
        data={
            "quote_id": quote_id,
            "old_status": result.old_status,
            "new_status": result.new_status,
        },
    )


@router.get("/quotes/{quote_id}/status/history", response_model=ResponseModel)
def get_status_history(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价状态变更历史（通过审批记录推断）

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 状态历史
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    # 从审批记录获取状态变更
    approvals = db.query(QuoteApproval).filter(
        QuoteApproval.quote_id == quote_id
    ).order_by(QuoteApproval.created_at).all()

    history = []

    # 添加创建记录
    history.append({
        "status": "DRAFT",
        "status_name": "草稿",
        "action": "创建",
        "operator": None,
        "timestamp": quote.created_at.isoformat() if quote.created_at else None,
        "remark": "报价创建"
    })

    # 从审批记录推断状态变更
    for a in approvals:
        if a.status == "APPROVED":
            history.append({
                "status": "APPROVED",
                "status_name": "已批准",
                "action": "审批通过",
                "operator": a.approver_name,
                "timestamp": a.approved_at.isoformat() if a.approved_at else None,
                "remark": a.approval_opinion
            })
        elif a.status == "REJECTED":
            history.append({
                "status": "REJECTED",
                "status_name": "已拒绝",
                "action": "审批拒绝",
                "operator": a.approver_name,
                "timestamp": a.approved_at.isoformat() if a.approved_at else None,
                "remark": a.approval_opinion
            })

    # 添加当前状态
    if quote.status not in ["DRAFT", "APPROVED", "REJECTED"]:
        history.append({
            "status": quote.status,
            "status_name": QUOTE_STATUSES.get(quote.status, {}).get("name", quote.status),
            "action": "状态变更",
            "operator": None,
            "timestamp": quote.updated_at.isoformat() if quote.updated_at else None,
            "remark": None
        })

    return ResponseModel(
        code=200,
        message="获取状态历史成功",
        data={"quote_id": quote_id, "history": history}
    )


@router.get("/quotes/status/summary", response_model=ResponseModel)
def get_status_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价状态统计

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 状态统计
    """
    summary = []
    for status_code, status_info in QUOTE_STATUSES.items():
        count = db.query(Quote).filter(Quote.status == status_code).count()
        summary.append({
            "status": status_code,
            "name": status_info["name"],
            "color": status_info["color"],
            "count": count
        })

    summary.sort(key=lambda x: QUOTE_STATUSES.get(x["status"], {}).get("order", 99))
    total = sum(s["count"] for s in summary)

    return ResponseModel(
        code=200,
        message="获取状态统计成功",
        data={"total": total, "summary": summary}
    )

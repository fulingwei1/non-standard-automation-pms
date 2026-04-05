# -*- coding: utf-8 -*-
"""
售前费用管理 API
端点：
  POST /expenses           — 录入费用
  GET  /expenses           — 费用列表
  GET  /expenses/stats     — 费用统计
  POST /expenses/approve   — 费用审批
"""

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale_expense import PresaleExpense
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.presale_expense import (
    ExpenseApprovalRequest,
    PresaleExpenseCreate,
    PresaleExpenseResponse,
)

router = APIRouter(prefix="/expenses", tags=["presale-expenses"])


@router.post("", response_model=ResponseModel)
def create_expense(
    payload: PresaleExpenseCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """录入售前费用"""
    expense = PresaleExpense(
        expense_type=payload.expense_type,
        amount=payload.amount,
        expense_date=payload.expense_date,
        description=payload.description,
        ticket_id=payload.ticket_id,
        opportunity_id=payload.opportunity_id,
        user_id=payload.user_id or current_user.id,
        user_name=current_user.real_name or current_user.username,
        department_id=payload.department_id,
        approval_status="PENDING",
        created_by=current_user.id,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    return ResponseModel(
        code=200,
        message="费用录入成功",
        data={
            "id": expense.id,
            "expense_type": expense.expense_type,
            "amount": float(expense.amount),
            "approval_status": expense.approval_status,
        },
    )


@router.get("", response_model=ResponseModel)
def list_expenses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    expense_type: Optional[str] = Query(None, description="费用类型筛选"),
    approval_status: Optional[str] = Query(None, description="审批状态筛选"),
    ticket_id: Optional[int] = Query(None, description="关联工单ID"),
    opportunity_id: Optional[int] = Query(None, description="关联商机ID"),
    user_id: Optional[int] = Query(None, description="人员ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
) -> Any:
    """费用列表（分页+筛选）"""
    query = db.query(PresaleExpense)

    if expense_type:
        query = query.filter(PresaleExpense.expense_type == expense_type)
    if approval_status:
        query = query.filter(PresaleExpense.approval_status == approval_status)
    if ticket_id:
        query = query.filter(PresaleExpense.ticket_id == ticket_id)
    if opportunity_id:
        query = query.filter(PresaleExpense.opportunity_id == opportunity_id)
    if user_id:
        query = query.filter(PresaleExpense.user_id == user_id)
    if start_date:
        query = query.filter(PresaleExpense.expense_date >= start_date)
    if end_date:
        query = query.filter(PresaleExpense.expense_date <= end_date)

    total = query.count()
    items = (
        query.order_by(PresaleExpense.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
            "items": [
                {
                    "id": e.id,
                    "expense_type": e.expense_type,
                    "amount": float(e.amount or 0),
                    "expense_date": str(e.expense_date) if e.expense_date else None,
                    "description": e.description,
                    "ticket_id": e.ticket_id,
                    "opportunity_id": e.opportunity_id,
                    "user_id": e.user_id,
                    "user_name": e.user_name,
                    "department_id": e.department_id,
                    "department_name": e.department_name,
                    "approval_status": e.approval_status,
                    "approved_by": e.approved_by,
                    "approved_at": str(e.approved_at) if e.approved_at else None,
                    "approval_note": e.approval_note,
                    "created_at": str(e.created_at) if e.created_at else None,
                }
                for e in items
            ],
        },
    )


@router.get("/stats", response_model=ResponseModel)
def get_expense_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
) -> Any:
    """费用统计分析（按时间/类型/人员）"""
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        end_date = today

    base_q = db.query(PresaleExpense).filter(
        PresaleExpense.expense_date >= start_date,
        PresaleExpense.expense_date <= end_date,
    )

    all_expenses = base_q.all()
    total_count = len(all_expenses)
    total_amount = sum(float(e.amount or 0) for e in all_expenses)

    # 按类型统计
    type_map: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_amount": 0.0})
    for e in all_expenses:
        t = e.expense_type or "OTHER"
        type_map[t]["count"] += 1
        type_map[t]["total_amount"] += float(e.amount or 0)

    by_type = [
        {"label": k, "count": v["count"], "total_amount": round(v["total_amount"], 2)}
        for k, v in type_map.items()
    ]

    # 按人员统计
    user_map: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_amount": 0.0})
    for e in all_expenses:
        name = e.user_name or f"user_{e.user_id}"
        user_map[name]["count"] += 1
        user_map[name]["total_amount"] += float(e.amount or 0)

    by_user = [
        {"label": k, "count": v["count"], "total_amount": round(v["total_amount"], 2)}
        for k, v in user_map.items()
    ]

    # 按月统计
    month_map: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_amount": 0.0})
    for e in all_expenses:
        if e.expense_date:
            month_key = e.expense_date.strftime("%Y-%m")
        else:
            month_key = "unknown"
        month_map[month_key]["count"] += 1
        month_map[month_key]["total_amount"] += float(e.amount or 0)

    by_month = [
        {"label": k, "count": v["count"], "total_amount": round(v["total_amount"], 2)}
        for k, v in sorted(month_map.items())
    ]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_count": total_count,
            "total_amount": round(total_amount, 2),
            "by_type": by_type,
            "by_user": by_user,
            "by_month": by_month,
        },
    )


@router.post("/approve", response_model=ResponseModel)
def approve_expense(
    payload: ExpenseApprovalRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """费用审批"""
    expense = db.query(PresaleExpense).filter(PresaleExpense.id == payload.expense_id).first()
    if not expense:
        return ResponseModel(code=404, message="费用记录不存在", data=None)

    if expense.approval_status != "PENDING":
        return ResponseModel(code=400, message="该费用已审批，无法重复操作", data=None)

    expense.approval_status = payload.action.value
    expense.approved_by = current_user.id
    expense.approved_at = datetime.now()
    expense.approval_note = payload.note

    db.commit()
    db.refresh(expense)

    return ResponseModel(
        code=200,
        message=f"费用已{('通过' if payload.action.value == 'APPROVED' else '驳回')}",
        data={
            "id": expense.id,
            "approval_status": expense.approval_status,
            "approved_by": expense.approved_by,
            "approved_at": str(expense.approved_at),
        },
    )

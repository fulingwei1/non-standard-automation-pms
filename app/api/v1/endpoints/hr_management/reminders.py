# -*- coding: utf-8 -*-
"""
合同到期提醒端点
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.organization import (
    ContractReminder,
    Employee,
    EmployeeContract,
)
from app.models.user import User

router = APIRouter()


@router.get("/contract-reminders")
def get_contract_reminders(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    reminder_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """获取合同到期提醒列表"""
    query = db.query(ContractReminder).join(Employee)

    if reminder_status:
        query = query.filter(ContractReminder.status == reminder_status)

    total = query.count()
    reminders = apply_pagination(query.order_by(ContractReminder.contract_end_date.asc()), pagination.offset, pagination.limit).all()

    items = []
    for r in reminders:
        items.append({
            "id": r.id,
            "contract_id": r.contract_id,
            "employee_id": r.employee_id,
            "employee_name": r.employee.name if r.employee else None,
            "reminder_type": r.reminder_type,
            "reminder_date": str(r.reminder_date) if r.reminder_date else None,
            "contract_end_date": str(r.contract_end_date) if r.contract_end_date else None,
            "days_until_expiry": r.days_until_expiry,
            "status": r.status,
            "handle_action": r.handle_action,
        })

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total)
    }


@router.put("/contract-reminders/{reminder_id}/handle")
def handle_contract_reminder(
    reminder_id: int,
    action: str = Query(..., description="处理动作: renew, terminate, extend, ignore"),
    remark: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """处理合同到期提醒"""
    reminder = db.query(ContractReminder).filter(ContractReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒记录不存在")

    reminder.status = "handled"
    reminder.handled_at = datetime.now()
    reminder.handled_by = current_user.id
    reminder.handle_action = action
    reminder.handle_remark = remark

    db.commit()

    return {"success": True, "message": "提醒已处理"}


@router.post("/contract-reminders/generate")
def generate_contract_reminders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """
    生成合同到期提醒（手动触发，也可由定时任务调用）
    提前两个月、一个月、两周发送提醒
    """
    today = date.today()
    two_months_later = today + timedelta(days=60)

    # 查找需要提醒的合同
    contracts = db.query(EmployeeContract).join(Employee).filter(
        EmployeeContract.status == "active",
        EmployeeContract.end_date <= two_months_later,
        EmployeeContract.end_date >= today,
        Employee.is_active == True
    ).all()

    created_count = 0

    for contract in contracts:
        days_until = (contract.end_date - today).days if contract.end_date else 0

        # 确定提醒类型
        if days_until <= 14:
            reminder_type = "two_weeks"
        elif days_until <= 30:
            reminder_type = "one_month"
        else:
            reminder_type = "two_months"

        # 检查是否已有相同类型的提醒
        existing = db.query(ContractReminder).filter(
            ContractReminder.contract_id == contract.id,
            ContractReminder.reminder_type == reminder_type
        ).first()

        if not existing:
            reminder = ContractReminder(
                contract_id=contract.id,
                employee_id=contract.employee_id,
                reminder_type=reminder_type,
                reminder_date=today,
                contract_end_date=contract.end_date,
                days_until_expiry=days_until,
                status="pending"
            )
            db.add(reminder)
            created_count += 1

            # 更新合同的提醒状态
            contract.reminder_sent = True
            contract.reminder_sent_at = datetime.now()

    db.commit()

    return {
        "success": True,
        "message": f"已生成 {created_count} 条合同到期提醒",
        "created_count": created_count
    }

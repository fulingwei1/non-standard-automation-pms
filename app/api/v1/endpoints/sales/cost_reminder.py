# -*- coding: utf-8 -*-
"""
成本管理 - 物料成本更新提醒

包含成本更新提醒的配置和管理
"""

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import MaterialCostUpdateReminder
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import (
    MaterialCostUpdateReminderResponse,
    MaterialCostUpdateReminderUpdate,
)

router = APIRouter()


@router.get("/purchase-material-costs/reminder", response_model=MaterialCostUpdateReminderResponse)
def get_cost_update_reminder(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取物料成本更新提醒配置和状态
    """
    reminder = db.query(MaterialCostUpdateReminder).filter(
        MaterialCostUpdateReminder.is_enabled
    ).order_by(desc(MaterialCostUpdateReminder.created_at)).first()

    if not reminder:
        # 创建默认提醒配置
        reminder = MaterialCostUpdateReminder(
            reminder_type="PERIODIC",
            reminder_interval_days=30,
            next_reminder_date=date.today() + timedelta(days=30),
            is_enabled=True,
            include_standard=True,
            include_non_standard=True,
            notify_roles=["procurement", "procurement_manager", "采购工程师", "采购专员", "采购部经理"],
            reminder_count=0
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

    # 计算距离下次提醒的天数
    days_until_next = None
    is_due = False

    if reminder.next_reminder_date:
        today = date.today()
        delta = (reminder.next_reminder_date - today).days
        days_until_next = delta
        is_due = delta <= 0

    reminder_dict = {
        **{c.name: getattr(reminder, c.name) for c in reminder.__table__.columns},
        "days_until_next": days_until_next,
        "is_due": is_due
    }

    return MaterialCostUpdateReminderResponse(**reminder_dict)


@router.put("/purchase-material-costs/reminder", response_model=MaterialCostUpdateReminderResponse)
def update_cost_update_reminder(
    *,
    db: Session = Depends(deps.get_db),
    reminder_in: MaterialCostUpdateReminderUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新物料成本更新提醒配置
    """
    reminder = db.query(MaterialCostUpdateReminder).filter(
        MaterialCostUpdateReminder.is_enabled
    ).order_by(desc(MaterialCostUpdateReminder.created_at)).first()

    if not reminder:
        reminder = MaterialCostUpdateReminder(
            reminder_type="PERIODIC",
            reminder_interval_days=30,
            next_reminder_date=date.today() + timedelta(days=30),
            is_enabled=True,
            include_standard=True,
            include_non_standard=True,
            notify_roles=["procurement", "procurement_manager", "采购工程师", "采购专员", "采购部经理"],
            reminder_count=0
        )
        db.add(reminder)

    update_data = reminder_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(reminder, field):
            setattr(reminder, field, value)

    reminder.last_updated_by = current_user.id
    reminder.last_updated_at = datetime.now()

    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # 计算距离下次提醒的天数
    days_until_next = None
    is_due = False

    if reminder.next_reminder_date:
        today = date.today()
        delta = (reminder.next_reminder_date - today).days
        days_until_next = delta
        is_due = delta <= 0

    reminder_dict = {
        **{c.name: getattr(reminder, c.name) for c in reminder.__table__.columns},
        "days_until_next": days_until_next,
        "is_due": is_due
    }

    return MaterialCostUpdateReminderResponse(**reminder_dict)


@router.post("/purchase-material-costs/reminder/acknowledge", response_model=ResponseModel)
def acknowledge_cost_update_reminder(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认物料成本更新提醒（标记为已处理，更新下次提醒日期）
    """
    reminder = db.query(MaterialCostUpdateReminder).filter(
        MaterialCostUpdateReminder.is_enabled
    ).order_by(desc(MaterialCostUpdateReminder.created_at)).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="提醒配置不存在")

    # 更新提醒日期
    reminder.last_reminder_date = date.today()
    reminder.next_reminder_date = date.today() + timedelta(days=reminder.reminder_interval_days)
    reminder.reminder_count = (reminder.reminder_count or 0) + 1
    reminder.last_updated_by = current_user.id
    reminder.last_updated_at = datetime.now()

    db.add(reminder)
    db.commit()

    return ResponseModel(
        code=200,
        message="提醒已确认",
        data={
            "next_reminder_date": reminder.next_reminder_date.isoformat(),
            "reminder_count": reminder.reminder_count
        }
    )

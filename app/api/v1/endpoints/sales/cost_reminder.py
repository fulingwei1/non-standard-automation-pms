# -*- coding: utf-8 -*-
"""
成本管理 - 物料成本更新提醒

包含成本更新提醒的配置和管理
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import MaterialCostUpdateReminder
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import (
    MaterialCostUpdateReminderResponse,
    MaterialCostUpdateReminderUpdate,
)
from app.services.sales.operation_log_service import SalesOperationLogService
from app.utils.db_helpers import save_obj

router = APIRouter()


def _audit_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _reminder_audit_value(reminder: MaterialCostUpdateReminder) -> dict[str, Any]:
    return {
        "reminder_id": reminder.id,
        "reminder_type": reminder.reminder_type,
        "reminder_interval_days": reminder.reminder_interval_days,
        "last_reminder_date": _audit_value(reminder.last_reminder_date),
        "next_reminder_date": _audit_value(reminder.next_reminder_date),
        "is_enabled": reminder.is_enabled,
        "material_type_filter": reminder.material_type_filter,
        "include_standard": reminder.include_standard,
        "include_non_standard": reminder.include_non_standard,
        "notify_roles": reminder.notify_roles,
        "notify_users": reminder.notify_users,
        "reminder_count": reminder.reminder_count,
        "last_updated_by": reminder.last_updated_by,
        "last_updated_at": _audit_value(reminder.last_updated_at),
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def _log_reminder_operation(
    db: Session,
    reminder: MaterialCostUpdateReminder,
    operation_type: str,
    operator: User,
    *,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    operation_desc: str,
) -> None:
    old_snapshot = old_value or {}
    new_snapshot = new_value or {}
    SalesOperationLogService.log_operation(
        db,
        entity_type=SalesEntityType.MATERIAL_COST_REMINDER,
        entity_id=reminder.id,
        entity_code=f"REMINDER-{reminder.id}",
        operation_type=operation_type,
        operator=operator,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark="material_cost_reminder",
    )


@router.get("/purchase-material-costs/reminder", response_model=MaterialCostUpdateReminderResponse)
def get_cost_update_reminder(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取物料成本更新提醒配置和状态
    """
    reminder = (
        db.query(MaterialCostUpdateReminder)
        .filter(MaterialCostUpdateReminder.is_enabled)
        .order_by(desc(MaterialCostUpdateReminder.created_at))
        .first()
    )

    if not reminder:
        # 创建默认提醒配置
        reminder = MaterialCostUpdateReminder(
            reminder_type="PERIODIC",
            reminder_interval_days=30,
            next_reminder_date=date.today() + timedelta(days=30),
            is_enabled=True,
            include_standard=True,
            include_non_standard=True,
            notify_roles=[
                "procurement",
                "procurement_manager",
                "采购工程师",
                "采购专员",
                "采购部经理",
            ],
            reminder_count=0,
        )
        save_obj(db, reminder)

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
        "is_due": is_due,
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
    reminder = (
        db.query(MaterialCostUpdateReminder)
        .filter(MaterialCostUpdateReminder.is_enabled)
        .order_by(desc(MaterialCostUpdateReminder.created_at))
        .first()
    )

    if not reminder:
        reminder = MaterialCostUpdateReminder(
            reminder_type="PERIODIC",
            reminder_interval_days=30,
            next_reminder_date=date.today() + timedelta(days=30),
            is_enabled=True,
            include_standard=True,
            include_non_standard=True,
            notify_roles=[
                "procurement",
                "procurement_manager",
                "采购工程师",
                "采购专员",
                "采购部经理",
            ],
            reminder_count=0,
        )
        db.add(reminder)

    old_value = _reminder_audit_value(reminder)
    update_data = reminder_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(reminder, field):
            setattr(reminder, field, value)

    reminder.last_updated_by = current_user.id
    reminder.last_updated_at = datetime.now()

    db.add(reminder)
    db.flush()
    _log_reminder_operation(
        db,
        reminder,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=_reminder_audit_value(reminder),
        operation_desc="更新物料成本提醒配置",
    )
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
        "is_due": is_due,
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
    reminder = (
        db.query(MaterialCostUpdateReminder)
        .filter(MaterialCostUpdateReminder.is_enabled)
        .order_by(desc(MaterialCostUpdateReminder.created_at))
        .first()
    )

    if not reminder:
        raise HTTPException(status_code=404, detail="提醒配置不存在")

    old_value = _reminder_audit_value(reminder)
    # 更新提醒日期
    reminder.last_reminder_date = date.today()
    reminder.next_reminder_date = date.today() + timedelta(days=reminder.reminder_interval_days)
    reminder.reminder_count = (reminder.reminder_count or 0) + 1
    reminder.last_updated_by = current_user.id
    reminder.last_updated_at = datetime.now()

    db.add(reminder)
    db.flush()
    _log_reminder_operation(
        db,
        reminder,
        SalesOperationType.STATUS_CHANGE,
        current_user,
        old_value=old_value,
        new_value=_reminder_audit_value(reminder),
        operation_desc="确认物料成本更新提醒",
    )
    db.commit()

    return ResponseModel(
        code=200,
        message="提醒已确认",
        data={
            "next_reminder_date": reminder.next_reminder_date.isoformat(),
            "reminder_count": reminder.reminder_count,
        },
    )

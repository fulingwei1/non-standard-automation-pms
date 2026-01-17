# -*- coding: utf-8 -*-
"""
通知设置API
"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.notification import NotificationSettings
from app.models.user import User
from app.schemas.notification import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)

router = APIRouter()


@router.get("/settings", response_model=NotificationSettingsResponse)
def get_notification_settings(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("notification:read")),
) -> Any:
    """
    获取通知设置（用户偏好）
    """
    settings = (
        db.query(NotificationSettings)
        .filter(NotificationSettings.user_id == current_user.id)
        .first()
    )

    # 如果不存在，创建默认设置
    if not settings:
        settings = NotificationSettings(
            user_id=current_user.id,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return NotificationSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        wechat_enabled=settings.wechat_enabled,
        system_enabled=settings.system_enabled,
        task_notifications=settings.task_notifications,
        approval_notifications=settings.approval_notifications,
        alert_notifications=settings.alert_notifications,
        issue_notifications=settings.issue_notifications,
        project_notifications=settings.project_notifications,
        quiet_hours_start=settings.quiet_hours_start,
        quiet_hours_end=settings.quiet_hours_end,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.put("/settings", response_model=NotificationSettingsResponse)
def update_notification_settings(
    *,
    db: Session = Depends(deps.get_db),
    settings_in: NotificationSettingsUpdate,
    current_user: User = Depends(security.require_permission("notification:read")),
) -> Any:
    """
    更新通知设置
    """
    settings = (
        db.query(NotificationSettings)
        .filter(NotificationSettings.user_id == current_user.id)
        .first()
    )

    # 如果不存在，创建
    if not settings:
        settings = NotificationSettings(user_id=current_user.id)
        db.add(settings)

    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    db.add(settings)
    db.commit()
    db.refresh(settings)

    return NotificationSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        wechat_enabled=settings.wechat_enabled,
        system_enabled=settings.system_enabled,
        task_notifications=settings.task_notifications,
        approval_notifications=settings.approval_notifications,
        alert_notifications=settings.alert_notifications,
        issue_notifications=settings.issue_notifications,
        project_notifications=settings.project_notifications,
        quiet_hours_start=settings.quiet_hours_start,
        quiet_hours_end=settings.quiet_hours_end,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )

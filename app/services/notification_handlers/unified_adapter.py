# -*- coding: utf-8 -*-
"""
Legacy notification handler adapter for unified NotificationService.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationChannel,
    NotificationPriority,
)


def map_alert_level_to_priority(alert_level: Optional[str]) -> str:
    if not alert_level:
        return NotificationPriority.NORMAL
    level_upper = alert_level.upper()
    mapping = {
        "URGENT": NotificationPriority.URGENT,
        "CRITICAL": NotificationPriority.URGENT,
        "WARNING": NotificationPriority.HIGH,
        "WARN": NotificationPriority.HIGH,
        "INFO": NotificationPriority.NORMAL,
    }
    return mapping.get(level_upper, NotificationPriority.NORMAL)


def resolve_recipient_id(
    db: Session,
    notification,
    user: Optional[User],
    target_field: Optional[str] = None,
    target_value: Optional[str] = None,
) -> Optional[int]:
    if getattr(notification, "notify_user_id", None):
        return notification.notify_user_id
    if user and getattr(user, "id", None):
        return user.id
    if target_field and target_value:
        try:
            candidate = (
                db.query(User).filter(getattr(User, target_field) == target_value).first()
            )
            if candidate:
                return candidate.id
        except Exception:
            return None
    return None


def send_alert_via_unified(
    db: Session,
    notification,
    alert,
    user: Optional[User],
    channel: str,
    target_field: Optional[str] = None,
    target_value: Optional[str] = None,
    wechat_template: Optional[dict] = None,
) -> dict:
    recipient_id = resolve_recipient_id(
        db, notification, user, target_field=target_field, target_value=target_value
    )
    if not recipient_id:
        raise ValueError("Notification requires recipient user")

    title = (
        getattr(notification, "notify_title", None)
        or getattr(alert, "alert_title", None)
        or "预警通知"
    )
    content = (
        getattr(notification, "notify_content", None)
        or getattr(alert, "alert_content", None)
        or ""
    )
    alert_id = getattr(alert, "id", None)

    request = NotificationRequest(
        recipient_id=recipient_id,
        notification_type="ALERT_NOTIFICATION",
        category="alert",
        title=title,
        content=content,
        priority=map_alert_level_to_priority(getattr(alert, "alert_level", None)),
        channels=[channel],
        source_type="alert",
        source_id=alert_id,
        link_url=f"/alerts/{alert_id}" if alert_id else None,
        extra_data={
            "alert_no": getattr(alert, "alert_no", None),
            "alert_level": getattr(alert, "alert_level", None),
            "target_type": getattr(alert, "target_type", None),
            "target_name": getattr(alert, "target_name", None),
        },
        wechat_template=wechat_template,
        force_send=True,
    )

    from app.services.unified_notification_service import get_notification_service

    result = get_notification_service(db).send_notification(request)
    if not result.get("success", False):
        raise ValueError(result.get("message", "Notification send failed"))
    return result


__all__ = [
    "NotificationChannel",
    "NotificationPriority",
    "map_alert_level_to_priority",
    "resolve_recipient_id",
    "send_alert_via_unified",
]

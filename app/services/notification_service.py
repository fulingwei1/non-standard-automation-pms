# -*- coding: utf-8 -*-
"""Backward-compatible notification service facade.

The canonical implementation lives under ``app.services.notification``.  Older
modules still import ``app.services.notification_service`` and expect the legacy
enum names plus a small convenience API, so this module adapts those calls to the
unified notification stack.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Sequence

from app.core.config import settings
from app.models.alert import AlertNotification
from app.models.notification import Notification
from app.services.notification.channels.base import (
    NotificationChannel as UnifiedNotificationChannel,
    NotificationRequest,
)
from app.services.notification.notification_dispatcher import NotificationDispatcher
from app.services.notification.unified_notification_service import (
    get_notification_service,
    notification_service,
)

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    WEB = "WEB"
    EMAIL = "EMAIL"
    WECHAT = "WECHAT"
    SMS = "SMS"
    WEBHOOK = "WEBHOOK"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_COMPLETED = "TASK_COMPLETED"
    DEADLINE_REMINDER = "DEADLINE_REMINDER"
    PROJECT_UPDATE = "PROJECT_UPDATE"
    SYSTEM_ANNOUNCEMENT = "SYSTEM_ANNOUNCEMENT"
    ALERT = "ALERT"


class NotificationService:
    """Legacy facade that builds unified notification requests."""

    def __init__(self, db=None):
        self.db = db
        self._db = db
        self.enabled_channels = self._get_enabled_channels()

    def _get_enabled_channels(self) -> list[NotificationChannel]:
        channels = [NotificationChannel.WEB]
        if getattr(settings, "EMAIL_ENABLED", False):
            channels.append(NotificationChannel.EMAIL)
        if getattr(settings, "SMS_ENABLED", False):
            channels.append(NotificationChannel.SMS)
        if getattr(settings, "WECHAT_ENABLED", False):
            channels.append(NotificationChannel.WECHAT)
        webhook_url = getattr(settings, "WEBHOOK_URL", None) or getattr(
            settings, "WECHAT_WEBHOOK_URL", None
        )
        if webhook_url:
            channels.append(NotificationChannel.WEBHOOK)
        return channels

    def _map_old_channel_to_new(self, channel: Any) -> str:
        value = channel.value if isinstance(channel, Enum) else str(channel)
        mapping = {
            "WEB": UnifiedNotificationChannel.SYSTEM,
            "SYSTEM": UnifiedNotificationChannel.SYSTEM,
            "EMAIL": UnifiedNotificationChannel.EMAIL,
            "WECHAT": UnifiedNotificationChannel.WECHAT,
            "SMS": UnifiedNotificationChannel.SMS,
            "WEBHOOK": UnifiedNotificationChannel.WEBHOOK,
        }
        return mapping.get(value.upper(), UnifiedNotificationChannel.SYSTEM)

    def _map_old_priority_to_new(self, priority: Any) -> str:
        if isinstance(priority, Enum):
            return str(priority.value)
        if isinstance(priority, str):
            return priority
        return str(priority)

    def _infer_category(self, notification_type: Any) -> str:
        value = notification_type.value if isinstance(notification_type, Enum) else str(
            notification_type
        )
        if value in {NotificationType.TASK_ASSIGNED.value, NotificationType.TASK_COMPLETED.value}:
            return "task"
        if value == NotificationType.DEADLINE_REMINDER.value:
            return "task"
        if value == NotificationType.PROJECT_UPDATE.value:
            return "project"
        return "general"

    def _build_request(
        self,
        recipient_id: int,
        notification_type: Any,
        title: str,
        content: str,
        priority: Any = NotificationPriority.NORMAL,
        channels: Optional[Sequence[Any]] = None,
        data: Optional[dict] = None,
        link: Optional[str] = None,
    ) -> NotificationRequest:
        mapped_channels = None
        if channels:
            mapped_channels = [self._map_old_channel_to_new(channel) for channel in channels]
        return NotificationRequest(
            recipient_id=recipient_id,
            notification_type=(
                notification_type.value
                if isinstance(notification_type, Enum)
                else str(notification_type)
            ),
            category=self._infer_category(notification_type),
            title=title,
            content=content,
            priority=self._map_old_priority_to_new(priority),
            channels=mapped_channels,
            extra_data=data,
            link_url=link,
        )

    def send_notification(self, *args, **kwargs) -> bool:
        explicit_db = "db" in kwargs
        db = kwargs.pop("db", self._db)
        if explicit_db and db is None:
            return False

        if args and isinstance(args[0], int):
            recipient_id = args[0]
            title = args[1] if len(args) > 1 else kwargs.pop("title", "")
            content = args[2] if len(args) > 2 else kwargs.pop("content", "")
            notification_type = kwargs.pop(
                "notification_type", NotificationType.SYSTEM_ANNOUNCEMENT
            )
        else:
            recipient_id = kwargs.pop("recipient_id")
            notification_type = kwargs.pop("notification_type")
            title = kwargs.pop("title")
            content = kwargs.pop("content")

        effective_db = db or self._db
        if effective_db is None:
            return False

        request = self._build_request(
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            content=content,
            priority=kwargs.pop("priority", NotificationPriority.NORMAL),
            channels=kwargs.pop("channels", None),
            data=kwargs.pop("data", None),
            link=kwargs.pop("link", None),
        )
        try:
            result = get_notification_service(effective_db).send_notification(request)
            return bool(result.get("success"))
        except Exception as exc:
            logger.error("发送通知失败: %s", exc)
            return False

    def send_task_assigned_notification(
        self,
        db,
        assignee_id: int,
        task_name: str,
        project_name: str,
        task_id: Optional[int] = None,
        due_date: Optional[datetime] = None,
    ) -> bool:
        content = f"项目 {project_name} 分配了新任务：{task_name}"
        if due_date:
            content += f"，截止日期：{due_date:%Y-%m-%d}"
        return self.send_notification(
            db=db,
            recipient_id=assignee_id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title=f"新任务：{task_name}",
            content=content,
            data={"task_id": task_id} if task_id else None,
            link=f"/tasks/{task_id}" if task_id else None,
        )

    def send_task_completed_notification(
        self,
        db,
        task_owner_id: int,
        task_name: str,
        project_name: str,
    ) -> bool:
        return self.send_notification(
            db=db,
            recipient_id=task_owner_id,
            notification_type=NotificationType.TASK_COMPLETED,
            title=f"任务已完成：{task_name}",
            content=f"项目 {project_name} 的任务 {task_name} 已完成",
        )

    def send_deadline_reminder(
        self,
        db,
        recipient_id: int,
        task_name: str,
        due_date: datetime,
        days_remaining: int,
    ) -> bool:
        urgent = days_remaining <= 1
        title = f"{'紧急' if urgent else ''}截止提醒：{task_name}"
        content = f"任务 {task_name} 将于 {due_date:%Y-%m-%d} 到期，剩余 {days_remaining} 天"
        return self.send_notification(
            db=db,
            recipient_id=recipient_id,
            notification_type=NotificationType.DEADLINE_REMINDER,
            title=title,
            content=content,
            priority=NotificationPriority.URGENT if urgent else NotificationPriority.NORMAL,
        )

    def get_unread_count(self, user_id: int) -> int:
        try:
            return self.db.query(Notification).filter(Notification.user_id == user_id).count()
        except Exception:
            return 0

    def mark_as_read(self, notification_id: int) -> bool:
        try:
            notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                return False
            notification.read = True
            self.db.commit()
            return True
        except Exception:
            return False

    def get_notification_history(self, user_id: int):
        try:
            return (
                self.db.query(Notification)
                .filter(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .all()
            )
        except Exception:
            return []


def get_notification_service_instance(db=None) -> NotificationService:
    return NotificationService(db=db)


class AlertNotificationService:
    """Legacy alert notification facade."""

    def __init__(self, db):
        self.db = db

    @staticmethod
    def create_alert_notification(db, alert, channel: str):
        notification = AlertNotification(
            alert_id=alert.id,
            notify_channel=str(channel).upper(),
            notify_target=str(getattr(alert, "assignee_id", None) or ""),
            notify_user_id=getattr(alert, "assignee_id", None),
            notify_title=getattr(alert, "alert_title", None),
            notify_content=getattr(alert, "alert_content", None),
            status="PENDING",
        )
        db.add(notification)
        db.commit()
        return notification

    def _normalize_channels(self, channels: Optional[Sequence[Any]]) -> list[str]:
        if not channels:
            return ["SYSTEM"]
        valid = {"SYSTEM", "EMAIL", "WECHAT", "SMS", "WEBHOOK", "WEB"}
        normalized = []
        for channel in channels:
            if not channel:
                continue
            value = channel.value if isinstance(channel, Enum) else str(channel).upper()
            if value in valid:
                normalized.append("SYSTEM" if value == "WEB" else value)
        return normalized or ["SYSTEM"]

    def _recipient_ids(self, alert, user=None, user_ids: Optional[Sequence[int]] = None) -> list[int]:
        recipients = []
        if user_ids:
            recipients.extend(uid for uid in user_ids if isinstance(uid, int))
        if user is not None and isinstance(getattr(user, "id", None), int):
            recipients.append(user.id)
        for attr in ("assignee_id", "handler_id", "notify_user_id"):
            value = getattr(alert, attr, None)
            if isinstance(value, int):
                recipients.append(value)
        return list(dict.fromkeys(recipients))

    def send_alert_notification(
        self,
        alert,
        user=None,
        user_ids: Optional[Sequence[int]] = None,
        channels: Optional[Sequence[Any]] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        force_send: bool = False,
    ) -> bool:
        try:
            recipients = self._recipient_ids(alert, user=user, user_ids=user_ids)
            if not recipients:
                return False
            result = NotificationDispatcher(self.db).dispatch_alert_notifications(
                alert=alert,
                user_ids=recipients,
                channels=self._normalize_channels(channels),
                title=title,
                content=content,
                force_send=force_send,
            )
            return any(bool(value) for value in result.values())
        except Exception as exc:
            logger.error("发送预警通知失败: %s", exc)
            return False

    def get_user_notifications(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        try:
            query = self.db.query(AlertNotification).filter(
                AlertNotification.notify_user_id == user_id
            )
            total = query.count()
            notifications = query.order_by(AlertNotification.created_at.desc()).offset(offset).limit(
                limit
            ).all()
            return {"success": True, "items": notifications, "total": total}
        except Exception:
            return {"success": False, "items": [], "total": 0}

    def get_unread_count(self, user_id: int) -> int:
        try:
            return (
                self.db.query(AlertNotification)
                .filter(
                    AlertNotification.notify_user_id == user_id,
                    AlertNotification.status == "PENDING",
                )
                .count()
            )
        except Exception:
            return 0

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        try:
            notification = (
                self.db.query(AlertNotification)
                .filter(
                    AlertNotification.id == notification_id,
                    AlertNotification.notify_user_id == user_id,
                )
                .first()
            )
            if not notification:
                return False
            notification.status = "SENT"
            self.db.commit()
            return True
        except Exception:
            return False

    def batch_mark_read(self, notification_ids: list, user_id: int) -> dict:
        try:
            notifications = (
                self.db.query(AlertNotification)
                .filter(
                    AlertNotification.id.in_(notification_ids),
                    AlertNotification.notify_user_id == user_id,
                )
                .all()
            )
            for notification in notifications:
                notification.status = "SENT"
            self.db.commit()
            return {"success": True, "success_count": len(notifications)}
        except Exception:
            return {"success": False, "success_count": 0}


__all__ = [
    "AlertNotificationService",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationRequest",
    "NotificationService",
    "NotificationType",
    "get_notification_service",
    "get_notification_service_instance",
    "notification_service",
]

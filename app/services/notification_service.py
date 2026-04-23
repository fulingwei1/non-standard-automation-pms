# -*- coding: utf-8 -*-
"""通知服务兼容层。"""

from __future__ import annotations

import logging
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import Notification as WebNotification
from app.services.channel_handlers.base import (
    NotificationChannel as UnifiedNotificationChannel,
    NotificationPriority as UnifiedNotificationPriority,
    NotificationRequest,
    NotificationResult,
)
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.unified_notification_service import get_notification_service, notification_service

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    WEB = "WEB"
    SYSTEM = "SYSTEM"
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
    """旧接口兼容包装。"""

    def __init__(self, db: Optional[Session] = None):
        self._db = db
        self.enabled_channels = self._get_enabled_channels()

    def _get_enabled_channels(self) -> List[NotificationChannel]:
        channels = [NotificationChannel.WEB]
        if getattr(settings, "EMAIL_ENABLED", False):
            channels.append(NotificationChannel.EMAIL)
        if getattr(settings, "SMS_ENABLED", False):
            channels.append(NotificationChannel.SMS)
        if getattr(settings, "WECHAT_ENABLED", False):
            channels.append(NotificationChannel.WECHAT)
        if getattr(settings, "WECHAT_WEBHOOK_URL", None):
            channels.append(NotificationChannel.WEBHOOK)
        return channels

    def _map_old_channel_to_new(self, channel: Any) -> str:
        value = getattr(channel, "value", channel)
        value = str(value).upper()
        mapping = {
            "WEB": UnifiedNotificationChannel.SYSTEM,
            "SYSTEM": UnifiedNotificationChannel.SYSTEM,
            "EMAIL": UnifiedNotificationChannel.EMAIL,
            "WECHAT": UnifiedNotificationChannel.WECHAT,
            "SMS": UnifiedNotificationChannel.SMS,
            "WEBHOOK": UnifiedNotificationChannel.WEBHOOK,
        }
        return mapping.get(value, UnifiedNotificationChannel.SYSTEM)

    def _map_old_priority_to_new(self, priority: Any) -> str:
        if isinstance(priority, NotificationPriority):
            return priority.value
        if isinstance(priority, UnifiedNotificationPriority):
            return str(priority)
        if isinstance(priority, str):
            return priority
        return str(priority)

    def _infer_category(self, notification_type: Any) -> str:
        value = getattr(notification_type, "value", notification_type)
        value = str(value).upper()
        if value in {
            NotificationType.TASK_ASSIGNED.value,
            NotificationType.TASK_COMPLETED.value,
            NotificationType.DEADLINE_REMINDER.value,
        }:
            return "task"
        if value == NotificationType.PROJECT_UPDATE.value:
            return "project"
        if value == NotificationType.ALERT.value:
            return "alert"
        return "general"

    def _normalize_channels(self, channels: Optional[Sequence[Any]]) -> Optional[List[str]]:
        if not channels:
            return None
        normalized: List[str] = []
        for channel in channels:
            if channel is None:
                continue
            mapped = self._map_old_channel_to_new(channel)
            if mapped not in normalized:
                normalized.append(mapped)
        return normalized or None

    def _build_request(
        self,
        recipient_id: int,
        notification_type: Any,
        title: str,
        content: str,
        priority: Any = NotificationPriority.NORMAL,
        channels: Optional[Sequence[Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        link: Optional[str] = None,
    ) -> NotificationRequest:
        raw_type = getattr(notification_type, "value", notification_type)
        raw_type = str(raw_type)
        category = self._infer_category(raw_type)
        return NotificationRequest(
            recipient_id=recipient_id,
            notification_type=raw_type,
            category=category,
            title=title,
            content=content,
            priority=self._map_old_priority_to_new(priority),
            channels=self._normalize_channels(channels),
            source_type=category,
            link_url=link,
            extra_data=data,
        )

    def send_notification(self, *args, **kwargs) -> bool:
        if args and not kwargs:
            if len(args) >= 5:
                db, recipient_id, notification_type, title, content = args[:5]
                priority = args[5] if len(args) > 5 else NotificationPriority.NORMAL
                channels = args[6] if len(args) > 6 else None
                data = args[7] if len(args) > 7 else None
                link = args[8] if len(args) > 8 else None
            elif len(args) >= 3:
                db = self._db
                recipient_id, title, content = args[:3]
                notification_type = NotificationType.SYSTEM_ANNOUNCEMENT
                priority = NotificationPriority.NORMAL
                channels = None
                data = None
                link = None
            else:
                return False
        else:
            db = kwargs.get("db", self._db)
            recipient_id = kwargs.get("recipient_id")
            notification_type = kwargs.get(
                "notification_type", NotificationType.SYSTEM_ANNOUNCEMENT
            )
            title = kwargs.get("title", "")
            content = kwargs.get("content", "")
            priority = kwargs.get("priority", NotificationPriority.NORMAL)
            channels = kwargs.get("channels")
            data = kwargs.get("data")
            link = kwargs.get("link")

        if db is None or recipient_id is None:
            return False

        try:
            request = self._build_request(
                recipient_id=recipient_id,
                notification_type=notification_type,
                title=title,
                content=content,
                priority=priority,
                channels=channels,
                data=data,
                link=link,
            )
            result = get_notification_service(db).send_notification(request)
            return bool(result.get("success"))
        except Exception as exc:
            logger.error("send_notification failed: %s", exc)
            return False

    def send_task_assigned_notification(
        self,
        db: Session,
        assignee_id: int,
        task_name: str,
        project_name: str,
        task_id: int,
        due_date: Optional[datetime] = None,
    ) -> bool:
        content = f"您有新任务《{task_name}》，所属项目：{project_name}"
        if due_date is not None:
            due_text = due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date)
            content = f"{content}，截止日期：{due_text}"
        return self.send_notification(
            db=db,
            recipient_id=assignee_id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title=f"新任务分配: {task_name}",
            content=content,
            data={"task_id": task_id, "project_name": project_name},
            link=f"/tasks/{task_id}",
        )

    def send_task_completed_notification(
        self,
        db: Session,
        task_owner_id: int,
        task_name: str,
        project_name: str,
        task_id: Optional[int] = None,
    ) -> bool:
        return self.send_notification(
            db=db,
            recipient_id=task_owner_id,
            notification_type=NotificationType.TASK_COMPLETED,
            title=f"任务已完成: {task_name}",
            content=f"项目《{project_name}》中的任务《{task_name}》已完成。",
            data={"task_id": task_id, "project_name": project_name},
            link=f"/tasks/{task_id}" if task_id else None,
        )

    def send_deadline_reminder(
        self,
        db: Session,
        recipient_id: int,
        task_name: str,
        due_date: Any,
        days_remaining: int,
        task_id: Optional[int] = None,
    ) -> bool:
        due_text = due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date)
        urgent = days_remaining <= 1
        title = f"{'紧急' if urgent else '截止'}提醒: {task_name}"
        prefix = "紧急" if urgent else "提醒"
        content = f"{prefix}：任务《{task_name}》将于 {due_text} 到期，剩余 {days_remaining} 天。"
        return self.send_notification(
            db=db,
            recipient_id=recipient_id,
            notification_type=NotificationType.DEADLINE_REMINDER,
            title=title,
            content=content,
            priority=NotificationPriority.HIGH if urgent else NotificationPriority.NORMAL,
            data={"task_id": task_id, "days_remaining": days_remaining},
            link=f"/tasks/{task_id}" if task_id else None,
        )

    def get_unread_count(self, user_id: int) -> int:
        if not self._db:
            return 0
        try:
            return self._db.query(WebNotification).filter(WebNotification.user_id == user_id).count()
        except Exception:
            return 0

    def mark_as_read(self, notification_id: int, user_id: Optional[int] = None) -> bool:
        if not self._db:
            return False
        try:
            notification = self._db.query(WebNotification).filter(WebNotification.id == notification_id).first()
            if not notification:
                return False
            setattr(notification, "read", True)
            setattr(notification, "is_read", True)
            if hasattr(self._db, "commit"):
                self._db.commit()
            return True
        except Exception:
            return False

    def get_notification_history(self, user_id: int):
        if not self._db:
            return []
        try:
            return (
                self._db.query(WebNotification)
                .filter(WebNotification.user_id == user_id)
                .order_by(WebNotification.created_at.desc())
                .all()
            )
        except Exception:
            return []


def get_notification_service_instance(db: Optional[Session] = None) -> NotificationService:
    return NotificationService(db=db)


class AlertNotificationService:
    """预警通知旧接口兼容包装。"""

    def __init__(self, db: Session):
        self.db = db
        self._notification_service = get_notification_service(db)

    @staticmethod
    def create_alert_notification(
        db: Session, alert: AlertRecord, notify_channel: str, status: str = "PENDING"
    ) -> AlertNotification:
        notification = AlertNotification(
            alert_id=alert.id,
            notify_channel=str(notify_channel).upper(),
            notify_target=str(
                getattr(alert, "assignee_id", None)
                or getattr(alert, "handler_id", None)
                or getattr(alert, "project_id", None)
                or "0"
            ),
            notify_user_id=getattr(alert, "assignee_id", None) or getattr(alert, "handler_id", None),
            notify_title=getattr(alert, "alert_title", None) or "预警通知",
            notify_content=getattr(alert, "alert_content", None) or "",
            status=status,
        )
        db.add(notification)
        db.commit()
        return notification

    def _resolve_user_ids(
        self,
        alert: AlertRecord,
        user: Optional[Any] = None,
        user_ids: Optional[Sequence[int]] = None,
    ) -> List[int]:
        if user_ids:
            return [int(uid) for uid in user_ids if uid]
        if user and getattr(user, "id", None):
            return [int(user.id)]
        for attr in ("assignee_id", "handler_id"):
            value = getattr(alert, attr, None)
            if value:
                return [int(value)]
        return []

    def send_alert_notification(
        self,
        alert: AlertRecord,
        user: Optional[Any] = None,
        user_ids: Optional[Sequence[int]] = None,
        channels: Optional[Sequence[Any]] = None,
    ) -> bool:
        try:
            resolved_user_ids = self._resolve_user_ids(alert, user=user, user_ids=user_ids)
            if not resolved_user_ids:
                return False

            normalized_channels = self._normalize_channels(channels) or [UnifiedNotificationChannel.SYSTEM]
            dispatcher = NotificationDispatcher(self.db)
            result = dispatcher.dispatch_alert_notifications(
                alert=alert,
                user_ids=resolved_user_ids,
                channels=normalized_channels,
                title=getattr(alert, "alert_title", None),
                content=getattr(alert, "alert_content", None),
            )
            return bool(
                result.get("queued") or result.get("sent") or result.get("created")
            )
        except Exception as exc:
            logger.error("send_alert_notification failed: %s", exc)
            return False

    def _normalize_channels(self, channels: Optional[Sequence[Any]]) -> Optional[List[str]]:
        return NotificationService(self.db)._normalize_channels(channels)

    def get_user_notifications(
        self, user_id: int, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        try:
            query = self.db.query(AlertNotification).filter(AlertNotification.notify_user_id == user_id)
            total = query.count()
            notifications = (
                query.order_by(AlertNotification.created_at.desc())
                .offset(max(page - 1, 0) * page_size)
                .limit(page_size)
                .all()
            )
            items = []
            for notification in notifications:
                alert = self.db.query(AlertRecord).filter(AlertRecord.id == notification.alert_id).first()
                items.append(
                    {
                        "id": notification.id,
                        "alert_id": notification.alert_id,
                        "channel": notification.notify_channel,
                        "status": notification.status,
                        "title": notification.notify_title,
                        "created_at": notification.created_at,
                        "sent_at": notification.sent_at,
                        "alert_title": getattr(alert, "alert_title", None),
                        "alert_level": getattr(alert, "alert_level", None),
                    }
                )
            return {"success": True, "total": total, "items": items}
        except Exception:
            return {"success": False, "total": 0, "items": []}

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        try:
            notification = (
                self.db.query(AlertNotification)
                .filter(AlertNotification.id == notification_id)
                .first()
            )
            if not notification:
                return False
            notification.status = "SENT"
            notification.read_at = datetime.now()
            self.db.commit()
            return True
        except Exception:
            return False

    def get_unread_count(self, user_id: int) -> int:
        try:
            return self.db.query(AlertNotification).filter(AlertNotification.notify_user_id == user_id).count()
        except Exception:
            return 0

    def batch_mark_read(self, notification_ids: Sequence[int], user_id: int) -> Dict[str, Any]:
        try:
            notifications = (
                self.db.query(AlertNotification)
                .filter(AlertNotification.id.in_(list(notification_ids)))
                .all()
            )
            for notification in notifications:
                notification.status = "SENT"
                notification.read_at = datetime.now()
            self.db.commit()
            return {"success": True, "success_count": len(notifications)}
        except Exception:
            return {"success": False, "success_count": 0}


__all__ = [
    "AlertNotificationService",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationRequest",
    "NotificationResult",
    "NotificationService",
    "NotificationType",
    "NotificationDispatcher",
    "UnifiedNotificationChannel",
    "UnifiedNotificationPriority",
    "WebNotification",
    "get_notification_service",
    "get_notification_service_instance",
    "notification_service",
]

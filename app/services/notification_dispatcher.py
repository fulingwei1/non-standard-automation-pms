# -*- coding: utf-8 -*-
"""
Notification dispatcher for alert channels (system/WeChat/email).
Provides simple retry and logging helpers.

This module acts as a coordinator, delegating to the unified NotificationService.

通知系统架构：
- app.services.unified_notification_service: 主通知服务，提供 NotificationService 和 get_notification_service()
- app.services.notification_service: 兼容层，re-export 统一服务并提供旧接口的枚举和 AlertNotificationService
- app.services.notification_dispatcher (本模块): 预警通知调度协调器，内部使用统一服务
- app.services.notification_queue: Redis 通知队列（异步分发）
- app.services.notification_utils: 通知工具函数（渠道解析、接收者解析、免打扰判断等）
- app.services.channel_handlers/: 渠道处理器（System/Email/WeChat/SMS/Webhook）

BACKWARD COMPATIBILITY: This module maintains the same interface while using the new unified service.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import Notification
from app.models.notification import NotificationSettings
from app.models.user import User
from app.services.unified_notification_service import get_notification_service
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationChannel,
    NotificationPriority,
)
from app.services.notification_utils import (
    resolve_channels,
    resolve_recipients,
    resolve_channel_target,
    channel_allowed,
    is_quiet_hours,
    next_quiet_resume,
)
from app.utils.scheduler_metrics import (
    record_notification_failure,
    record_notification_success,
)


class NotificationDispatcher:
    """Dispatch alert notifications to specific channels (Coordinator).
    
    Now uses unified NotificationService internally.
    """

    RETRY_SCHEDULE = [5, 15, 30, 60]

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.unified_service = get_notification_service(db)

    def create_system_notification(
        self,
        recipient_id: int,
        notification_type: str,
        title: str,
        content: str,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        link_url: Optional[str] = None,
        priority: str = "NORMAL",
        extra_data: Optional[dict] = None,
    ) -> Notification:
        """创建站内通知记录（不自动提交）。"""
        notification = Notification(
            user_id=recipient_id,
            notification_type=notification_type,
            title=title,
            content=content,
            source_type=source_type,
            source_id=source_id,
            link_url=link_url,
            priority=priority,
            extra_data=extra_data or {},
        )
        self.db.add(notification)
        return notification

    def send_notification_request(self, request: NotificationRequest) -> dict:
        """发送通知请求（统一入口）。"""
        return self.unified_service.send_notification(request)

    def _resolve_recipients_by_ids(
        self, user_ids: Sequence[int]
    ) -> Dict[int, Dict[str, Optional[User]]]:
        if not user_ids:
            return {}
        clean_ids = {uid for uid in user_ids if isinstance(uid, int)}
        if not clean_ids:
            return {}
        users = (
            self.db.query(User)
            .filter(User.id.in_(list(clean_ids)))
            .filter(User.is_active)
            .all()
        )
        if not users:
            return {}
        settings_list = (
            self.db.query(NotificationSettings)
            .filter(NotificationSettings.user_id.in_([user.id for user in users]))
            .all()
        )
        settings_map = {setting.user_id: setting for setting in settings_list}
        return {
            user.id: {"user": user, "settings": settings_map.get(user.id)}
            for user in users
        }

    def _compute_next_retry(self, retry_count: int) -> datetime:
        idx = min(retry_count, len(self.RETRY_SCHEDULE)) - 1
        minutes = self.RETRY_SCHEDULE[idx] if idx >= 0 else self.RETRY_SCHEDULE[0]
        return datetime.now() + timedelta(minutes=minutes)

    def _map_channel_to_unified(self, channel: str) -> str:
        """映射旧渠道名称到统一服务渠道名称"""
        channel_upper = channel.upper()
        mapping = {
            "SYSTEM": NotificationChannel.SYSTEM,
            "EMAIL": NotificationChannel.EMAIL,
            "WECHAT": NotificationChannel.WECHAT,
            "SMS": NotificationChannel.SMS,
            "WEBHOOK": NotificationChannel.WEBHOOK,
        }
        return mapping.get(channel_upper, NotificationChannel.SYSTEM)

    def _map_alert_level_to_priority(self, alert_level: str) -> str:
        """映射预警级别到通知优先级"""
        level_upper = alert_level.upper() if alert_level else "NORMAL"
        mapping = {
            "URGENT": NotificationPriority.URGENT,
            "CRITICAL": NotificationPriority.URGENT,
            "WARNING": NotificationPriority.HIGH,
            "INFO": NotificationPriority.NORMAL,
        }
        return mapping.get(level_upper, NotificationPriority.NORMAL)

    def _resolve_recipient_id(
        self, notification: AlertNotification, user: Optional[User]
    ) -> int:
        recipient_id = notification.notify_user_id
        if not recipient_id and user:
            recipient_id = user.id
        if not recipient_id:
            raise ValueError("Notification requires recipient_id or user")
        return recipient_id

    def _build_request(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        recipient_id: int,
        unified_channel: str,
        force_send: bool = False,
    ) -> NotificationRequest:
        return NotificationRequest(
            recipient_id=recipient_id,
            notification_type="ALERT",
            category="alert",
            title=notification.notify_title or alert.alert_title or "预警通知",
            content=notification.notify_content or alert.alert_content or "",
            priority=self._map_alert_level_to_priority(alert.alert_level),
            channels=[unified_channel],
            source_type="alert",
            source_id=alert.id,
            link_url=f"/alerts/{alert.id}",
            extra_data={
                "alert_no": alert.alert_no,
                "alert_level": alert.alert_level,
                "target_type": alert.target_type,
                "target_name": alert.target_name,
            },
            force_send=force_send,
        )

    def build_notification_request(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User],
        force_send: bool = False,
    ) -> NotificationRequest:
        channel = (notification.notify_channel or "SYSTEM").upper()
        unified_channel = self._map_channel_to_unified(channel)
        recipient_id = self._resolve_recipient_id(notification, user)
        return self._build_request(
            notification=notification,
            alert=alert,
            recipient_id=recipient_id,
            unified_channel=unified_channel,
            force_send=force_send,
        )

    def dispatch(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User],
        request: Optional[NotificationRequest] = None,
        force_send: bool = False,
    ) -> bool:
        """Send notification based on channel using unified service."""
        channel = (notification.notify_channel or "SYSTEM").upper()
        unified_channel = self._map_channel_to_unified(channel)
        effective_force_send = force_send or (request.force_send if request else False)
        
        try:
            # 确定接收者
            if request is not None:
                if effective_force_send and not request.force_send:
                    request.force_send = True
                recipient_id = request.recipient_id
            else:
                recipient_id = self._resolve_recipient_id(notification, user)

            # 免打扰处理（与统一服务一致）
            settings = None
            if isinstance(recipient_id, int):
                settings = (
                    self.db.query(NotificationSettings)
                    .filter(NotificationSettings.user_id == recipient_id)
                    .first()
                )
            if not effective_force_send and settings and is_quiet_hours(settings, datetime.now()):
                notification.status = "PENDING"
                notification.error_message = "Delayed due to quiet hours"
                notification.next_retry_at = next_quiet_resume(
                    settings, datetime.now()
                )
                notification.retry_count = notification.retry_count or 0
                return True

            # 构建通知请求
            if request is None:
                request = self._build_request(
                    notification=notification,
                    alert=alert,
                    recipient_id=recipient_id,
                    unified_channel=unified_channel,
                    force_send=effective_force_send,
                )

            # 使用统一服务发送
            result = self.unified_service.send_notification(request)
            
            if result.get("success", False):
                notification.status = "SENT"
                notification.sent_at = datetime.now()
                notification.error_message = None
                notification.next_retry_at = None
                notification.retry_count = notification.retry_count or 0
                record_notification_success(channel)
                return True
            else:
                # 发送失败
                error_msg = result.get("message", "Unknown error")
                notification.status = "FAILED"
                notification.error_message = error_msg
                notification.retry_count = (notification.retry_count or 0) + 1
                notification.next_retry_at = self._compute_next_retry(
                    notification.retry_count
                )
                record_notification_failure(channel)
                self.logger.error(
                    f"[notification] channel={channel} alert_id={alert.id} target={notification.notify_target} "
                    f"failed: {error_msg}"
                )
                return False
                
        except Exception as exc:
            notification.status = "FAILED"
            notification.error_message = str(exc)
            notification.retry_count = (notification.retry_count or 0) + 1
            notification.next_retry_at = self._compute_next_retry(
                notification.retry_count
            )
            record_notification_failure(channel)
            self.logger.error(
                f"[notification] channel={channel} alert_id={alert.id} target={notification.notify_target} "
                f"failed: {exc}"
            )
            return False

    def dispatch_alert_notifications(
        self,
        alert: AlertRecord,
        user_ids: Optional[Sequence[int]] = None,
        channels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        force_send: bool = False,
    ) -> Dict[str, int]:
        """创建并发送预警通知（使用队列优先）。"""
        from app.services.notification_queue import enqueue_notification

        if user_ids:
            recipients = self._resolve_recipients_by_ids(user_ids)
        else:
            try:
                recipients = resolve_recipients(self.db, alert)
            except Exception:
                recipients = {}

        if not recipients:
            return {"created": 0, "queued": 0, "sent": 0, "failed": 0}

        if channels:
            channel_list = [str(ch).upper() for ch in channels if ch]
        else:
            try:
                channel_list = resolve_channels(alert)
            except Exception:
                channel_list = ["SYSTEM"]

        if not channel_list:
            channel_list = ["SYSTEM"]

        notify_title = (
            title
            or getattr(alert, "alert_title", None)
            or getattr(alert, "title", None)
            or "预警通知"
        )
        notify_content = (
            content
            or getattr(alert, "alert_content", None)
            or getattr(alert, "description", None)
            or ""
        )

        created = 0
        created_notifications: List[Tuple[AlertNotification, User]] = []

        for recipient in recipients.values():
            user = recipient.get("user")
            settings = recipient.get("settings")
            if not user:
                continue

            for channel in channel_list:
                if not force_send and not channel_allowed(channel, settings):
                    continue
                target = resolve_channel_target(channel, user)
                if not target:
                    continue

                existing = (
                    self.db.query(AlertNotification)
                    .filter(
                        AlertNotification.alert_id == alert.id,
                        AlertNotification.notify_channel == channel,
                        AlertNotification.notify_target == target,
                    )
                    .first()
                )
                if existing:
                    continue

                notification = AlertNotification(
                    alert_id=alert.id,
                    notify_channel=channel,
                    notify_target=target,
                    notify_user_id=user.id,
                    notify_title=notify_title,
                    notify_content=notify_content,
                    status="PENDING",
                )
                self.db.add(notification)
                created += 1
                created_notifications.append((notification, user))

        if created == 0:
            return {"created": 0, "queued": 0, "sent": 0, "failed": 0}

        self.db.flush()

        queued = 0
        sent = 0
        failed = 0

        for notification, user in created_notifications:
            request = self.build_notification_request(
                notification, alert, user, force_send=force_send
            )
            enqueued = enqueue_notification(
                {
                    "notification_id": notification.id,
                    "alert_id": notification.alert_id,
                    "notify_channel": notification.notify_channel,
                    "request": request.__dict__,
                }
            )
            if enqueued:
                notification.status = "QUEUED"
                notification.next_retry_at = None
                queued += 1
                continue

            if self.dispatch(
                notification,
                alert,
                user,
                request=request,
                force_send=force_send,
            ):
                sent += 1
            else:
                failed += 1

        return {"created": created, "queued": queued, "sent": sent, "failed": failed}


# Re-export utility functions for backward compatibility
__all__ = [
    "NotificationDispatcher",
    "resolve_channels",
    "resolve_recipients",
    "resolve_channel_target",
    "channel_allowed",
    "is_quiet_hours",
    "next_quiet_resume",
]

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
from typing import Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
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
        )

    def build_notification_request(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User],
    ) -> NotificationRequest:
        channel = (notification.notify_channel or "SYSTEM").upper()
        unified_channel = self._map_channel_to_unified(channel)
        recipient_id = self._resolve_recipient_id(notification, user)
        return self._build_request(
            notification=notification,
            alert=alert,
            recipient_id=recipient_id,
            unified_channel=unified_channel,
        )

    def dispatch(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User],
        request: Optional[NotificationRequest] = None,
    ) -> bool:
        """Send notification based on channel using unified service."""
        channel = (notification.notify_channel or "SYSTEM").upper()
        unified_channel = self._map_channel_to_unified(channel)
        
        try:
            # 确定接收者
            if request is not None:
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
            if settings and is_quiet_hours(settings, datetime.now()):
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

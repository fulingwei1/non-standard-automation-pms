# -*- coding: utf-8 -*-
"""
Notification dispatcher for alert channels (system/WeChat/email).
Provides simple retry and logging helpers.

This module acts as a coordinator, delegating to the unified NotificationService.

BACKWARD COMPATIBILITY: This module maintains the same interface while using the new unified service.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
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

    def dispatch(
        self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]
    ) -> bool:
        """Send notification based on channel using unified service."""
        channel = (notification.notify_channel or "SYSTEM").upper()
        unified_channel = self._map_channel_to_unified(channel)
        
        try:
            # 确定接收者
            recipient_id = notification.notify_user_id
            if not recipient_id and user:
                recipient_id = user.id
            if not recipient_id:
                raise ValueError("Notification requires recipient_id or user")

            # 构建通知请求
            request = NotificationRequest(
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

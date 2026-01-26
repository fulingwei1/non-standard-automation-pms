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
    """Dispatch alert notifications to specific channels (Coordinator)."""

    RETRY_SCHEDULE = [5, 15, 30, 60]

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.system_handler = SystemNotificationHandler(db, self)
        self.email_handler = EmailNotificationHandler(db, self)
        self.wechat_handler = WeChatNotificationHandler(db, self)
        self.sms_handler = SMSNotificationHandler(db, self)

    def _compute_next_retry(self, retry_count: int) -> datetime:
        idx = min(retry_count, len(self.RETRY_SCHEDULE)) - 1
        minutes = self.RETRY_SCHEDULE[idx] if idx >= 0 else self.RETRY_SCHEDULE[0]
        return datetime.now() + timedelta(minutes=minutes)

    def dispatch(
        self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]
    ) -> bool:
        """Send notification based on channel."""
        channel = (notification.notify_channel or "SYSTEM").upper()
        try:
            if channel == "SYSTEM":
                self.system_handler.send(notification, alert, user)
            elif channel == "EMAIL":
                self.email_handler.send(notification, alert, user)
            elif channel == "WECHAT":
                self.wechat_handler.send(notification, alert, user)
            elif channel == "SMS":
                self.sms_handler.send(notification, alert, user)
            else:
                raise ValueError(f"Unsupported notify channel: {channel}")

            notification.status = "SENT"
            notification.sent_at = datetime.now()
            notification.error_message = None
            notification.next_retry_at = None
            notification.retry_count = notification.retry_count or 0
            record_notification_success(channel)
            return True
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

# -*- coding: utf-8 -*-
"""向后兼容入口: app.services.notification_dispatcher."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import NotificationSettings
from app.models.user import User
from app.services.notification.channels.base import NotificationRequest
from app.services.notification.notification_dispatcher import (
    NotificationDispatcher as _NotificationDispatcher,
    channel_allowed,
    is_quiet_hours,
    next_quiet_resume,
    resolve_channel_target,
    resolve_channels,
    resolve_recipients,
)
from app.services.notification.unified_notification_service import get_notification_service
from app.utils.scheduler_metrics import (
    record_notification_failure,
    record_notification_success,
)

logger = logging.getLogger(__name__)


class NotificationDispatcher(_NotificationDispatcher):
    """兼容包装，确保旧 patch 目标仍然生效。"""

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.unified_service = get_notification_service(db)

    def dispatch(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User],
        request: Optional[NotificationRequest] = None,
        force_send: bool = False,
    ) -> bool:
        channel = (notification.notify_channel or "SYSTEM").upper()
        unified_channel = self._map_channel_to_unified(channel)
        effective_force_send = force_send or (request.force_send if request else False)

        try:
            if request is not None:
                if effective_force_send and not request.force_send:
                    request.force_send = True
                recipient_id = request.recipient_id
            else:
                recipient_id = self._resolve_recipient_id(notification, user)

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
                notification.next_retry_at = next_quiet_resume(settings, datetime.now())
                notification.retry_count = notification.retry_count or 0
                return True

            if request is None:
                request = self._build_request(
                    notification=notification,
                    alert=alert,
                    recipient_id=recipient_id,
                    unified_channel=unified_channel,
                    force_send=effective_force_send,
                )

            result = self.unified_service.send_notification(request)

            if result.get("success", False):
                notification.status = "SENT"
                notification.sent_at = datetime.now()
                notification.error_message = None
                notification.next_retry_at = None
                notification.retry_count = notification.retry_count or 0
                record_notification_success(channel)
                return True

            error_msg = result.get("message", "Unknown error")
            notification.status = "FAILED"
            notification.error_message = error_msg
            notification.retry_count = (notification.retry_count or 0) + 1
            notification.next_retry_at = self._compute_next_retry(notification.retry_count)
            record_notification_failure(channel)
            self.logger.error(
                f"[notification] channel={channel} alert_id={alert.id} target={notification.notify_target} failed: {error_msg}"
            )
            return False

        except Exception as exc:
            notification.status = "FAILED"
            notification.error_message = str(exc)
            notification.retry_count = (notification.retry_count or 0) + 1
            notification.next_retry_at = self._compute_next_retry(notification.retry_count)
            record_notification_failure(channel)
            self.logger.error(
                f"[notification] channel={channel} alert_id={alert.id} target={notification.notify_target} failed: {exc}"
            )
            return False


__all__ = [
    "NotificationDispatcher",
    "get_notification_service",
    "record_notification_success",
    "record_notification_failure",
    "resolve_channels",
    "resolve_recipients",
    "resolve_channel_target",
    "channel_allowed",
    "is_quiet_hours",
    "next_quiet_resume",
]

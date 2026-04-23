# -*- coding: utf-8 -*-
"""向后兼容入口: app.services.notification_handlers.system_handler."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import Notification
from app.models.user import User
from app.services.notification.handlers.unified_adapter import (
    NotificationChannel,
    send_alert_via_unified,
)

if TYPE_CHECKING:
    from app.services.notification_dispatcher import NotificationDispatcher


class SystemNotificationHandler:
    def __init__(self, db: Session, parent: "NotificationDispatcher" = None):
        self.db = db
        self._parent = parent

    def send(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User] = None,
    ) -> None:
        user_id = notification.notify_user_id
        if not user_id:
            raise ValueError("System notification requires notify_user_id")

        existing = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.source_type == "alert",
                Notification.source_id == alert.id,
                Notification.notification_type == "ALERT_NOTIFICATION",
            )
            .first()
        )
        if existing:
            return

        send_alert_via_unified(
            db=self.db,
            notification=notification,
            alert=alert,
            user=user,
            channel=NotificationChannel.SYSTEM,
        )


__all__ = ["SystemNotificationHandler", "send_alert_via_unified", "NotificationChannel"]

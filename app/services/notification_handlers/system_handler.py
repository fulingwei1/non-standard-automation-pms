# -*- coding: utf-8 -*-
"""系统通知处理器（站内消息）"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import Notification
from app.models.user import User
from app.services.notification_handlers.unified_adapter import (
    NotificationChannel,
    send_alert_via_unified,
)

if TYPE_CHECKING:
    from app.services.notification_dispatcher import NotificationDispatcher


class SystemNotificationHandler:
    """系统通知处理器（站内消息）"""

    def __init__(self, db: Session, parent: "NotificationDispatcher" = None):
        self.db = db
        self._parent = parent

    def send(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User] = None,
    ) -> None:
        """
        发送系统通知（创建站内消息记录）

        Args:
            notification: 通知对象
            alert: 预警记录
            user: 目标用户

        Raises:
            ValueError: 当缺少必要参数时
        """
        user_id = notification.notify_user_id
        if not user_id:
            raise ValueError("System notification requires notify_user_id")

        # 检查是否已存在相同的通知（避免重复）
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

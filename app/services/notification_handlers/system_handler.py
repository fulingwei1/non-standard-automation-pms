# -*- coding: utf-8 -*-
"""系统通知处理器（站内消息）"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import Notification
from app.models.user import User

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

        self.db.add(
            Notification(
                user_id=user_id,
                notification_type="ALERT_NOTIFICATION",
                title=notification.notify_title or alert.alert_title,
                content=notification.notify_content or alert.alert_content,
                source_type="alert",
                source_id=alert.id,
                link_url=f"/alerts/{alert.id}",
                priority=alert.alert_level,
                extra_data={
                    "alert_no": alert.alert_no,
                    "alert_level": alert.alert_level,
                    "target_type": alert.target_type,
                    "target_name": alert.target_name,
                },
            )
        )

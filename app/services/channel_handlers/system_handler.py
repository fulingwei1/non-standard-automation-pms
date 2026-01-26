# -*- coding: utf-8 -*-
"""
站内通知处理器
"""

from datetime import datetime

from app.models.notification import Notification
from app.services.channel_handlers.base import (
    ChannelHandler,
    NotificationRequest,
    NotificationResult,
)


class SystemChannelHandler(ChannelHandler):
    """站内通知处理器"""

    def send(self, request: NotificationRequest) -> NotificationResult:
        notification = Notification(
            user_id=request.recipient_id,
            notification_type=request.notification_type,
            title=request.title,
            content=request.content,
            source_type=request.source_type,
            source_id=request.source_id,
            link_url=request.link_url,
            priority=request.priority,
            extra_data=request.extra_data or {},
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return NotificationResult(
            channel=self.channel, success=True, sent_at=datetime.now().isoformat()
        )

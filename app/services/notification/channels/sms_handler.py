# -*- coding: utf-8 -*-
"""
短信通知处理器
"""

from app.core.config import settings
from app.models.user import User
from app.services.channel_handlers.base import (
    ChannelHandler,
    NotificationRequest,
    NotificationResult,
)


class SMSChannelHandler(ChannelHandler):
    """短信通知处理器"""

    def send(self, request: NotificationRequest) -> NotificationResult:
        if not self.is_enabled():
            return NotificationResult(
                channel=self.channel, success=False, error_message="短信功能未启用"
            )

        recipient = self.db.query(User).filter(User.id == request.recipient_id).first()
        if not recipient or not recipient.phone:
            return NotificationResult(
                channel=self.channel, success=False, error_message="用户未配置手机号"
            )

        self.logger.info(f"[短信通知] 发送给 {recipient.phone}: {request.title}")
        return NotificationResult(channel=self.channel, success=True)

    def is_enabled(self) -> bool:
        return bool(settings.SMS_ENABLED)

# -*- coding: utf-8 -*-
"""
邮件通知处理器（统一渠道接口）

EmailChannelHandler: 统一渠道系统的邮件处理器（ChannelHandler 接口）
EmailNotificationHandler: 完整 SMTP 邮件处理器（预警通知系统使用）

完整的 SMTP 邮件发送实现在 notification_handlers/email_handler.py 中。
"""

from datetime import datetime

from app.core.config import settings
from app.models.user import User
from app.services.channel_handlers.base import (
    ChannelHandler,
    NotificationRequest,
    NotificationResult,
)


from app.services.notification_handlers.email_handler import EmailNotificationHandler

__all__ = ["EmailChannelHandler", "EmailNotificationHandler"]


class EmailChannelHandler(ChannelHandler):
    """邮件通知处理器"""

    def send(self, request: NotificationRequest) -> NotificationResult:
        if not self.is_enabled():
            return NotificationResult(
                channel=self.channel, success=False, error_message="邮件功能未启用"
            )

        recipient = self.db.query(User).filter(User.id == request.recipient_id).first()
        if not recipient or not recipient.email:
            return NotificationResult(
                channel=self.channel, success=False, error_message="用户未配置邮箱"
            )

        self.logger.info(f"[邮件通知] 发送给 {recipient.email}: {request.title}")
        return NotificationResult(
            channel=self.channel, success=True, sent_at=datetime.now().isoformat()
        )

    def is_enabled(self) -> bool:
        return bool(settings.EMAIL_ENABLED)

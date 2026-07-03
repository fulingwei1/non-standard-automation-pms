# -*- coding: utf-8 -*-
"""
邮件通知处理器（统一渠道接口）

EmailChannelHandler: 统一渠道系统的邮件处理器（ChannelHandler 接口）
EmailNotificationHandler: 完整 SMTP 邮件处理器（预警通知系统使用）

完整的 SMTP 邮件发送实现在 notification_handlers/email_handler.py 中。
"""

import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings
from app.models.user import User
from app.services.channel_handlers.base import (
    ChannelHandler,
    NotificationRequest,
    NotificationResult,
)

__all__ = ["EmailChannelHandler", "EmailNotificationHandler"]


def __getattr__(name):
    # 延迟导入以打破循环依赖：
    # handlers.email_handler -> unified_adapter -> channels(__init__) -> channels.email_handler
    # -> handlers.email_handler。仅在真正访问 EmailNotificationHandler 时再导入。
    if name == "EmailNotificationHandler":
        from app.services.notification.handlers.email_handler import (
            EmailNotificationHandler,
        )

        return EmailNotificationHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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

        config_error = self._validate_smtp_config()
        if config_error:
            return NotificationResult(
                channel=self.channel,
                success=False,
                error_message=config_error,
            )

        try:
            self._send_smtp_message(
                to_email=recipient.email,
                subject=request.title,
                content=request.content,
            )
        except Exception as exc:
            self.logger.exception("[邮件通知] SMTP发送失败: %s", exc)
            return NotificationResult(
                channel=self.channel,
                success=False,
                error_message=f"邮件SMTP发送失败: {exc}",
            )

        self.logger.info("[邮件通知] 已通过SMTP发送给 %s: %s", recipient.email, request.title)
        return NotificationResult(
            channel=self.channel, success=True, sent_at=datetime.now().isoformat()
        )

    def is_enabled(self) -> bool:
        return bool(settings.EMAIL_ENABLED)

    def _validate_smtp_config(self) -> Optional[str]:
        if not self._setting_str("EMAIL_FROM") or not self._setting_str("EMAIL_SMTP_SERVER"):
            return "邮件SMTP配置不完整"

        username = self._setting_str("EMAIL_USERNAME")
        password = self._setting_str("EMAIL_PASSWORD")
        if bool(username) != bool(password):
            return "邮件SMTP认证配置不完整"
        return None

    def _send_smtp_message(self, to_email: str, subject: str, content: str) -> None:
        message = EmailMessage()
        message["From"] = self._setting_str("EMAIL_FROM")
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(content or "")

        smtp = smtplib.SMTP(
            self._setting_str("EMAIL_SMTP_SERVER"),
            self._setting_int("EMAIL_SMTP_PORT", default=587),
            timeout=10,
        )
        try:
            username = self._setting_str("EMAIL_USERNAME")
            password = self._setting_str("EMAIL_PASSWORD")
            if username and password:
                smtp.starttls()
                smtp.login(username, password)
            smtp.send_message(message)
        finally:
            try:
                smtp.quit()
            except Exception:
                pass

    @staticmethod
    def _setting_str(name: str) -> Optional[str]:
        value = getattr(settings, name, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _setting_int(name: str, default: int) -> int:
        value = getattr(settings, name, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

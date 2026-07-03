# -*- coding: utf-8 -*-
"""notification_sender单元测试"""
from unittest.mock import Mock, patch

from app.services.timesheet.reminder.notification_sender import NotificationSender

class TestNotificationSenderInit:
    def test_init(self):
        service = NotificationSender(Mock())
        assert service is not None


class TestNotificationSenderEmail:
    @patch("app.services.timesheet.reminder.notification_sender.settings")
    @patch("app.services.timesheet.reminder.notification_sender.smtplib.SMTP")
    def test_email_notification_uses_canonical_email_settings(
        self, mock_smtp_cls, mock_settings
    ):
        """工时提醒邮件应使用 app.core.config 中现行 EMAIL_* 配置。"""
        mock_settings.SMTP_HOST = None
        mock_settings.EMAIL_SMTP_SERVER = "smtp.example.com"
        mock_settings.EMAIL_SMTP_PORT = 2525
        mock_settings.EMAIL_FROM = "noreply@example.com"
        mock_settings.EMAIL_USERNAME = None
        mock_settings.EMAIL_PASSWORD = None

        mock_server = Mock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        reminder = Mock()
        reminder.title = "补交工时提醒"
        reminder.content = "请补交本周工时"
        reminder.reminder_no = "TSR-001"
        reminder.extra_data = {}

        user = Mock()
        user.email = "user@example.com"
        user.username = "alice"

        service = NotificationSender(Mock())

        result = service._send_email_notification(reminder, user)

        assert result is True
        mock_smtp_cls.assert_called_once_with("smtp.example.com", 2525)
        mock_server.send_message.assert_called_once()

    @patch("app.services.timesheet.reminder.notification_sender.settings")
    def test_email_notification_fails_without_smtp_server(self, mock_settings):
        """缺少真实SMTP服务器时不能假报成功。"""
        mock_settings.SMTP_HOST = None
        mock_settings.EMAIL_SMTP_SERVER = None

        reminder = Mock()
        reminder.reminder_no = "TSR-002"

        user = Mock()
        user.email = "user@example.com"
        user.username = "alice"

        service = NotificationSender(Mock())

        result = service._send_email_notification(reminder, user)

        assert result is False

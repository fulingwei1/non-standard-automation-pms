# -*- coding: utf-8 -*-
"""第二十四批 - notification_handlers/email_handler 单元测试"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

pytest.importorskip("app.services.notification_handlers.email_handler")

from app.services.notification_handlers.email_handler import EmailNotificationHandler


def _make_handler(email_enabled=True):
    db = MagicMock()
    with patch("app.services.notification_handlers.email_handler.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = email_enabled
        handler = EmailNotificationHandler(db=db)
        handler._settings_patch = mock_settings
    return handler, db


class TestEmailNotificationHandlerSend:
    @patch("app.services.notification_handlers.email_handler.settings")
    def test_raises_when_email_disabled(self, mock_settings):
        mock_settings.EMAIL_ENABLED = False
        db = MagicMock()
        handler = EmailNotificationHandler(db=db)
        notification = MagicMock()
        notification.notify_target = "test@test.com"
        alert = MagicMock()
        with pytest.raises(ValueError, match="Email channel disabled"):
            handler.send(notification, alert)

    @patch("app.services.notification_handlers.email_handler.send_alert_via_unified")
    @patch("app.services.notification_handlers.email_handler.settings")
    def test_send_with_email_enabled(self, mock_settings, mock_send):
        mock_settings.EMAIL_ENABLED = True
        db = MagicMock()
        handler = EmailNotificationHandler(db=db)

        notification = MagicMock()
        notification.notify_target = "user@example.com"
        notification.notify_email = None
        notification.notify_user_id = None
        alert = MagicMock()
        user = MagicMock()
        user.email = "user@example.com"

        handler.send(notification, alert, user=user)
        mock_send.assert_called_once()

    @patch("app.services.notification_handlers.email_handler.settings")
    def test_raises_when_no_recipient(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        db = MagicMock()
        handler = EmailNotificationHandler(db=db)

        notification = MagicMock()
        notification.notify_target = None
        notification.notify_email = None
        notification.notify_user_id = None
        alert = MagicMock()

        with pytest.raises(ValueError, match="requires recipient"):
            handler.send(notification, alert, user=None)


class TestEmailNotificationHandlerBuildMethods:
    def test_build_simple_html_contains_title(self):
        db = MagicMock()
        handler = EmailNotificationHandler(db=db)

        alert = MagicMock()
        alert.alert_level = "HIGH"
        alert.alert_no = "ALT-001"
        alert.project = None
        alert.triggered_at = None
        alert.status = "ACTIVE"

        html = handler._build_simple_html(
            alert=alert,
            title="测试预警",
            content="预警内容",
            level_color="#FF0000",
            alert_url="http://example.com/alert/1",
        )
        assert "测试预警" in html
        assert "ALT-001" in html

    def test_build_plain_text_contains_info(self):
        db = MagicMock()
        handler = EmailNotificationHandler(db=db)

        alert = MagicMock()
        alert.alert_level = "MEDIUM"
        alert.alert_no = "ALT-002"
        alert.project = None
        alert.triggered_at = None
        alert.status = "PENDING"

        text = handler._build_plain_text(
            alert=alert,
            title="测试标题",
            content="内容详情",
            alert_url="http://example.com",
        )
        assert "ALT-002" in text
        assert "测试标题" in text

# -*- coding: utf-8 -*-
"""EmailNotificationHandler 单元测试"""
from unittest.mock import MagicMock, patch
import pytest

try:
    from app.services.notification_handlers.email_handler import EmailNotificationHandler
    _IMPORT_OK = True
except ImportError:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Circular import in notification_handlers")


class TestEmailNotificationHandler:
    def setup_method(self):
        self.db = MagicMock()
        self.handler = EmailNotificationHandler(db=self.db)

    @patch("app.services.notification_handlers.email_handler.settings")
    def test_send_disabled(self, mock_settings):
        mock_settings.EMAIL_ENABLED = False
        with pytest.raises(ValueError, match="disabled"):
            self.handler.send(MagicMock(), MagicMock())

    @patch("app.services.notification_handlers.email_handler.send_alert_via_unified")
    @patch("app.services.notification_handlers.email_handler.settings")
    def test_send_success(self, mock_settings, mock_send):
        mock_settings.EMAIL_ENABLED = True
        notification = MagicMock()
        notification.notify_target = "test@example.com"
        self.handler.send(notification, MagicMock())
        mock_send.assert_called_once()

    @patch("app.services.notification_handlers.email_handler.settings")
    def test_send_no_recipient(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        notification = MagicMock()
        notification.notify_target = None
        notification.notify_email = None
        notification.notify_user_id = None
        with pytest.raises(ValueError, match="recipient"):
            self.handler.send(notification, MagicMock(), user=None)

    def test_build_plain_text(self):
        alert = MagicMock()
        alert.alert_level = "WARNING"
        alert.alert_no = "A001"
        alert.project = None
        alert.triggered_at = None
        alert.status = "PENDING"
        text = self.handler._build_plain_text(alert, "Title", "Content", "http://example.com")
        assert "Title" in text
        assert "A001" in text

    def test_build_simple_html(self):
        alert = MagicMock()
        alert.alert_level = "CRITICAL"
        alert.alert_no = "A002"
        alert.project = None
        alert.triggered_at = None
        alert.status = "PENDING"
        html = self.handler._build_simple_html(alert, "Title", "Content", "#ff0000", "http://example.com")
        assert "Title" in html
        assert "CRITICAL" in html

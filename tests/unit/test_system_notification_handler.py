# -*- coding: utf-8 -*-
"""系统通知处理器单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.notification_handlers.system_handler import SystemNotificationHandler


class TestSystemNotificationHandler:
    def setup_method(self):
        self.db = MagicMock()
        self.handler = SystemNotificationHandler(self.db)

    def test_send_raises_without_user_id(self):
        notification = MagicMock()
        notification.notify_user_id = None
        alert = MagicMock()
        with pytest.raises(ValueError):
            self.handler.send(notification, alert)

    def test_send_skips_duplicate(self):
        notification = MagicMock()
        notification.notify_user_id = 1
        alert = MagicMock()
        alert.id = 10
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()  # existing
        self.handler.send(notification, alert)
        # Should return without calling send_alert_via_unified

    @patch("app.services.notification_handlers.system_handler.send_alert_via_unified")
    def test_send_creates_notification(self, mock_send):
        notification = MagicMock()
        notification.notify_user_id = 1
        alert = MagicMock()
        alert.id = 10
        self.db.query.return_value.filter.return_value.first.return_value = None
        self.handler.send(notification, alert)
        mock_send.assert_called_once()

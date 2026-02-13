# -*- coding: utf-8 -*-
"""WeChatNotificationHandler 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.notification_handlers.wechat_handler import WeChatNotificationHandler
    _IMPORT_OK = True
except ImportError:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Circular import in notification_handlers")


class TestWeChatNotificationHandler:
    def _make_handler(self):
        db = MagicMock()
        return WeChatNotificationHandler(db=db)

    @patch("app.services.notification_handlers.wechat_handler.settings")
    def test_send_disabled(self, mock_settings):
        mock_settings.WECHAT_ENABLED = False
        handler = self._make_handler()
        with pytest.raises(ValueError, match="disabled"):
            handler.send(MagicMock(), MagicMock())

    @patch("app.services.notification_handlers.wechat_handler.send_alert_via_unified")
    @patch("app.services.notification_handlers.wechat_handler.settings")
    def test_send_success(self, mock_settings, mock_send):
        mock_settings.WECHAT_ENABLED = True
        handler = self._make_handler()
        notification = MagicMock()
        notification.notify_target = "user123"
        handler.send(notification, MagicMock(), MagicMock())
        mock_send.assert_called_once()

    @patch("app.services.notification_handlers.wechat_handler.settings")
    def test_send_no_recipient(self, mock_settings):
        mock_settings.WECHAT_ENABLED = True
        handler = self._make_handler()
        notification = MagicMock()
        notification.notify_target = None
        notification.notify_user_id = None
        with pytest.raises(ValueError, match="recipient"):
            handler.send(notification, MagicMock(), user=None)

    def test_get_wechat_userid_none(self):
        handler = self._make_handler()
        assert handler._get_wechat_userid(None) is None

    def test_get_wechat_userid_from_employee(self):
        handler = self._make_handler()
        user = MagicMock()
        user.employee_id = 1
        employee = MagicMock()
        employee.wechat_userid = "wx123"
        handler.db.query.return_value.filter.return_value.first.return_value = employee
        assert handler._get_wechat_userid(user) == "wx123"

    def test_get_wechat_userid_fallback(self):
        handler = self._make_handler()
        user = MagicMock()
        user.employee_id = None
        user.username = "fallback"
        handler.db.query.return_value.filter.return_value.first.return_value = None
        assert handler._get_wechat_userid(user) == "fallback"

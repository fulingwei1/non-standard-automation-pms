# -*- coding: utf-8 -*-
"""第二十九批 - notification_handlers/wechat_handler.py 单元测试（WeChatNotificationHandler）"""

import sys
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# 预先 mock 可能导致循环导入的模块
_mock_unified = MagicMock()
_mock_unified.NotificationChannel = "wechat"
_mock_unified.send_alert_via_unified = MagicMock()

if "app.services.notification_handlers.unified_adapter" not in sys.modules:
    sys.modules["app.services.notification_handlers.unified_adapter"] = _mock_unified

pytest.importorskip("app.services.notification_handlers.wechat_handler")

from app.services.notification_handlers.wechat_handler import WeChatNotificationHandler


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_notification(**kwargs):
    n = MagicMock()
    n.notify_target = kwargs.get("notify_target", None)
    n.notify_user_id = kwargs.get("notify_user_id", None)
    n.notify_title = kwargs.get("notify_title", "测试标题")
    n.notify_content = kwargs.get("notify_content", "测试内容")
    return n


def _make_alert(**kwargs):
    a = MagicMock()
    a.id = kwargs.get("id", 1)
    a.alert_title = kwargs.get("alert_title", "预警标题")
    a.alert_content = kwargs.get("alert_content", "预警内容")
    a.alert_level = kwargs.get("alert_level", "WARNING")
    a.alert_no = kwargs.get("alert_no", "ALT-001")
    a.status = kwargs.get("status", "OPEN")
    a.triggered_at = None
    a.project = None
    return a


def _make_user(**kwargs):
    u = MagicMock()
    u.id = kwargs.get("id", 10)
    u.wechat_userid = kwargs.get("wechat_userid", "wx_user_1")
    u.username = kwargs.get("username", "testuser")
    u.employee_id = kwargs.get("employee_id", None)
    return u


# ─── 测试类 ────────────────────────────────────────────────

class TestWeChatNotificationHandlerInit:
    """测试初始化"""

    def test_init_with_db(self):
        db = _make_db()
        handler = WeChatNotificationHandler(db=db)
        assert handler.db is db
        assert handler._parent is None

    def test_init_with_parent(self):
        db = _make_db()
        parent = MagicMock()
        handler = WeChatNotificationHandler(db=db, parent=parent)
        assert handler._parent is parent


class TestWeChatNotificationHandlerSend:
    """测试 send 方法"""

    @patch("app.services.notification_handlers.wechat_handler.settings")
    def test_send_raises_when_wechat_disabled(self, mock_settings):
        mock_settings.WECHAT_ENABLED = False
        db = _make_db()
        handler = WeChatNotificationHandler(db=db)
        notification = _make_notification()
        alert = _make_alert()
        with pytest.raises(ValueError, match="disabled"):
            handler.send(notification, alert)

    @patch("app.services.notification_handlers.wechat_handler.settings")
    def test_send_raises_when_no_recipient(self, mock_settings):
        mock_settings.WECHAT_ENABLED = True
        db = _make_db()
        handler = WeChatNotificationHandler(db=db)
        notification = _make_notification(notify_target=None, notify_user_id=None)
        alert = _make_alert()
        user = MagicMock()
        user.wechat_userid = None
        with pytest.raises(ValueError, match="recipient"):
            handler.send(notification, alert, user=user)

    @patch("app.services.notification_handlers.wechat_handler.send_alert_via_unified")
    @patch("app.services.notification_handlers.wechat_handler.settings")
    def test_send_uses_notify_target(self, mock_settings, mock_send_unified):
        mock_settings.WECHAT_ENABLED = True
        mock_send_unified.return_value = None
        db = _make_db()
        handler = WeChatNotificationHandler(db=db)
        notification = _make_notification(notify_target="wx_direct_target")
        alert = _make_alert()
        handler.send(notification, alert)
        mock_send_unified.assert_called_once()

    @patch("app.services.notification_handlers.wechat_handler.send_alert_via_unified")
    @patch("app.services.notification_handlers.wechat_handler.settings")
    def test_send_uses_user_wechat_id(self, mock_settings, mock_send_unified):
        mock_settings.WECHAT_ENABLED = True
        mock_send_unified.return_value = None
        db = _make_db()
        handler = WeChatNotificationHandler(db=db)
        notification = _make_notification(notify_target=None, notify_user_id=5)
        alert = _make_alert()
        user = _make_user(wechat_userid="wx_from_user")
        handler.send(notification, alert, user=user)
        mock_send_unified.assert_called_once()


class TestWeChatNotificationHandlerWebhook:
    """测试 _send_via_webhook 方法"""

    @patch("app.services.notification_handlers.wechat_handler.requests")
    def test_webhook_success(self, mock_requests):
        resp = MagicMock()
        resp.status_code = 200
        mock_requests.post.return_value = resp
        db = _make_db()
        handler = WeChatNotificationHandler(db=db)
        notification = _make_notification(notify_content="内容", notify_title="标题")
        alert = _make_alert()
        handler._send_via_webhook(notification, alert, "https://example.com/webhook")
        mock_requests.post.assert_called_once()

    @patch("app.services.notification_handlers.wechat_handler.requests")
    def test_webhook_raises_on_error_status(self, mock_requests):
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "Bad request"
        mock_requests.post.return_value = resp
        db = _make_db()
        handler = WeChatNotificationHandler(db=db)
        notification = _make_notification()
        alert = _make_alert()
        with pytest.raises(ValueError, match="webhook failed"):
            handler._send_via_webhook(notification, alert, "https://example.com/hook")


class TestWeChatNotificationHandlerGetWeChatUserid:
    """测试 _get_wechat_userid 方法"""

    def test_returns_none_when_user_is_none(self):
        db = _make_db()
        handler = WeChatNotificationHandler(db=db)
        assert handler._get_wechat_userid(None) is None

    def test_returns_employee_wechat_userid(self):
        db = _make_db()
        employee = MagicMock()
        employee.wechat_userid = "emp_wx_id"
        db.query.return_value.filter.return_value.first.return_value = employee
        handler = WeChatNotificationHandler(db=db)
        user = _make_user(employee_id=42, wechat_userid=None)
        result = handler._get_wechat_userid(user)
        assert result == "emp_wx_id"

    def test_falls_back_to_username(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        handler = WeChatNotificationHandler(db=db)
        user = _make_user(employee_id=1, wechat_userid=None, username="fallback_user")
        result = handler._get_wechat_userid(user)
        assert result == "fallback_user"

# -*- coding: utf-8 -*-
"""第二十九批 - notification_handlers/unified_adapter.py 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.notification_handlers.unified_adapter")

from app.services.notification_handlers.unified_adapter import (
    map_alert_level_to_priority,
    resolve_recipient_id,
    send_alert_via_unified,
)
from app.services.channel_handlers.base import NotificationPriority


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_notification(**kwargs):
    n = MagicMock()
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
    a.target_type = "PROJECT"
    a.target_name = "测试项目"
    return a


def _make_user(user_id=10):
    u = MagicMock()
    u.id = user_id
    return u


# ─── 测试：map_alert_level_to_priority ────────────────────────────────────────

class TestMapAlertLevelToPriority:
    """测试预警级别到优先级的映射"""

    def test_urgent_level(self):
        assert map_alert_level_to_priority("URGENT") == NotificationPriority.URGENT

    def test_critical_level(self):
        assert map_alert_level_to_priority("CRITICAL") == NotificationPriority.URGENT

    def test_warning_level(self):
        assert map_alert_level_to_priority("WARNING") == NotificationPriority.HIGH

    def test_warn_level(self):
        assert map_alert_level_to_priority("WARN") == NotificationPriority.HIGH

    def test_info_level(self):
        assert map_alert_level_to_priority("INFO") == NotificationPriority.NORMAL

    def test_none_level(self):
        assert map_alert_level_to_priority(None) == NotificationPriority.NORMAL

    def test_unknown_level_defaults_to_normal(self):
        assert map_alert_level_to_priority("UNKNOWN_LEVEL") == NotificationPriority.NORMAL

    def test_case_insensitive(self):
        assert map_alert_level_to_priority("urgent") == NotificationPriority.URGENT
        assert map_alert_level_to_priority("warning") == NotificationPriority.HIGH


# ─── 测试：resolve_recipient_id ───────────────────────────────────────────────

class TestResolveRecipientId:
    """测试收件人ID解析"""

    def test_returns_notify_user_id_first(self):
        db = _make_db()
        notification = _make_notification(notify_user_id=99)
        user = _make_user(user_id=1)
        result = resolve_recipient_id(db, notification, user)
        assert result == 99

    def test_falls_back_to_user_id(self):
        db = _make_db()
        notification = _make_notification(notify_user_id=None)
        user = _make_user(user_id=42)
        result = resolve_recipient_id(db, notification, user)
        assert result == 42

    def test_falls_back_to_target_field_lookup(self):
        db = _make_db()
        notification = _make_notification(notify_user_id=None)
        found_user = _make_user(user_id=77)
        db.query.return_value.filter.return_value.first.return_value = found_user
        # 使用 User 实际有的字段（username）
        result = resolve_recipient_id(
            db,
            notification,
            user=None,
            target_field="username",
            target_value="testuser_abc",
        )
        assert result == 77

    def test_returns_none_when_all_fallbacks_fail(self):
        db = _make_db()
        notification = _make_notification(notify_user_id=None)
        db.query.return_value.filter.return_value.first.return_value = None
        result = resolve_recipient_id(db, notification, user=None)
        assert result is None

    def test_handles_exception_in_target_lookup_gracefully(self):
        db = _make_db()
        db.query.side_effect = Exception("DB error")
        notification = _make_notification(notify_user_id=None)
        result = resolve_recipient_id(
            db, notification, user=None, target_field="wechat_userid", target_value="wx_x"
        )
        assert result is None


# ─── 测试：send_alert_via_unified ─────────────────────────────────────────────

class TestSendAlertViaUnified:
    """测试统一发送预警通知"""

    @patch("app.services.unified_notification_service.get_notification_service")
    def test_raises_when_no_recipient(self, mock_get_service):
        db = _make_db()
        notification = _make_notification(notify_user_id=None)
        alert = _make_alert()
        with pytest.raises(ValueError, match="recipient"):
            send_alert_via_unified(db, notification, alert, user=None, channel="wechat")

    @patch("app.services.unified_notification_service.get_notification_service")
    def test_sends_notification_with_recipient(self, mock_get_service):
        db = _make_db()
        notification = _make_notification(notify_user_id=10)
        alert = _make_alert()
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_service

        result = send_alert_via_unified(db, notification, alert, user=None, channel="wechat")

        assert result["success"] is True
        mock_service.send_notification.assert_called_once()

    @patch("app.services.unified_notification_service.get_notification_service")
    def test_raises_when_service_returns_failure(self, mock_get_service):
        db = _make_db()
        notification = _make_notification(notify_user_id=10)
        alert = _make_alert()
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {"success": False, "message": "发送失败"}
        mock_get_service.return_value = mock_service

        with pytest.raises(ValueError, match="发送失败"):
            send_alert_via_unified(db, notification, alert, user=None, channel="wechat")

    @patch("app.services.unified_notification_service.get_notification_service")
    def test_request_includes_alert_metadata(self, mock_get_service):
        db = _make_db()
        notification = _make_notification(notify_user_id=5)
        alert = _make_alert(alert_no="ALT-999", alert_level="CRITICAL")
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_service

        send_alert_via_unified(db, notification, alert, user=None, channel="email")

        call_args = mock_service.send_notification.call_args[0][0]
        assert call_args.extra_data.get("alert_no") == "ALT-999"
        assert call_args.extra_data.get("alert_level") == "CRITICAL"

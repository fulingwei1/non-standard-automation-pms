# -*- coding: utf-8 -*-
"""
Tests for app/services/notification_handlers/system_handler.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.notification_handlers.system_handler import SystemNotificationHandler
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def handler(mock_db):
    return SystemNotificationHandler(db=mock_db)


@pytest.fixture
def alert():
    a = MagicMock()
    a.id = 10
    return a


def test_send_raises_when_no_user_id(handler, alert):
    """没有 notify_user_id 时应抛出 ValueError"""
    notification = MagicMock()
    notification.notify_user_id = None
    with pytest.raises(ValueError, match="notify_user_id"):
        handler.send(notification, alert)


def test_send_skips_if_existing(handler, mock_db, alert):
    """已存在相同通知时不重复发送"""
    notification = MagicMock()
    notification.notify_user_id = 1
    existing = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = existing

    with patch("app.services.notification_handlers.system_handler.send_alert_via_unified") as mock_send:
        handler.send(notification, alert)
        mock_send.assert_not_called()


def test_send_calls_unified_when_no_existing(handler, mock_db, alert):
    """无已有通知时应调用 send_alert_via_unified"""
    notification = MagicMock()
    notification.notify_user_id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.notification_handlers.system_handler.send_alert_via_unified") as mock_send:
        handler.send(notification, alert)
        mock_send.assert_called_once()


def test_handler_stores_db(mock_db):
    """确认 db 属性被正确存储"""
    handler = SystemNotificationHandler(db=mock_db)
    assert handler.db is mock_db


def test_handler_stores_parent(mock_db):
    """确认 parent 属性被正确存储"""
    parent = MagicMock()
    handler = SystemNotificationHandler(db=mock_db, parent=parent)
    assert handler._parent is parent


def test_send_passes_correct_channel(handler, mock_db, alert):
    """验证传给 unified 的 channel 参数是 SYSTEM"""
    from app.services.notification_handlers.unified_adapter import NotificationChannel
    notification = MagicMock()
    notification.notify_user_id = 42
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.notification_handlers.system_handler.send_alert_via_unified") as mock_send:
        handler.send(notification, alert)
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs.get("channel") == NotificationChannel.SYSTEM

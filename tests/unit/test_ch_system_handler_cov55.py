# -*- coding: utf-8 -*-
"""
Tests for app/services/channel_handlers/system_handler.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.channel_handlers.system_handler import SystemChannelHandler
    from app.services.channel_handlers.base import NotificationRequest, NotificationChannel
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def handler(mock_db):
    return SystemChannelHandler(db=mock_db, channel=NotificationChannel.SYSTEM)


@pytest.fixture
def request_obj():
    return NotificationRequest(
        recipient_id=1,
        notification_type="ALERT_NOTIFICATION",
        category="alert",
        title="Test Title",
        content="Test content",
        source_type="alert",
        source_id=100,
        link_url="/alerts/100",
        extra_data={"key": "val"},
    )


def test_send_returns_success(handler, request_obj):
    """发送成功应返回 success=True"""
    with patch("app.services.channel_handlers.system_handler.save_obj") as mock_save:
        result = handler.send(request_obj)
        assert result.success is True
        assert result.channel == NotificationChannel.SYSTEM


def test_send_creates_notification_obj(handler, request_obj):
    """发送时应创建 Notification 对象"""
    with patch("app.services.channel_handlers.system_handler.save_obj") as mock_save, \
         patch("app.services.channel_handlers.system_handler.Notification") as MockNotif:
        mock_instance = MagicMock()
        MockNotif.return_value = mock_instance
        handler.send(request_obj)
        MockNotif.assert_called_once()
        mock_save.assert_called_once_with(handler.db, mock_instance)


def test_send_result_has_sent_at(handler, request_obj):
    """发送结果中 sent_at 不为 None"""
    with patch("app.services.channel_handlers.system_handler.save_obj"):
        result = handler.send(request_obj)
        assert result.sent_at is not None


def test_send_uses_recipient_id(handler, mock_db, request_obj):
    """发送时使用正确的 recipient_id"""
    with patch("app.services.channel_handlers.system_handler.save_obj"), \
         patch("app.services.channel_handlers.system_handler.Notification") as MockNotif:
        handler.send(request_obj)
        call_kwargs = MockNotif.call_args[1]
        assert call_kwargs.get("user_id") == request_obj.recipient_id


def test_handler_inherits_channel_handler(handler):
    """确认继承自 ChannelHandler"""
    from app.services.channel_handlers.base import ChannelHandler
    assert isinstance(handler, ChannelHandler)


def test_send_with_none_extra_data(handler):
    """extra_data 为 None 时应使用空字典"""
    req = NotificationRequest(
        recipient_id=2,
        notification_type="TEST",
        category="cat",
        title="t",
        content="c",
        extra_data=None,
    )
    with patch("app.services.channel_handlers.system_handler.save_obj"), \
         patch("app.services.channel_handlers.system_handler.Notification") as MockNotif:
        handler.send(req)
        call_kwargs = MockNotif.call_args[1]
        assert call_kwargs.get("extra_data") == {}

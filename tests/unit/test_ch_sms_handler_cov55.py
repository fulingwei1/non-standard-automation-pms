# -*- coding: utf-8 -*-
"""
Tests for app/services/channel_handlers/sms_handler.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.channel_handlers.sms_handler import SMSChannelHandler
    from app.services.channel_handlers.base import NotificationRequest, NotificationChannel
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def handler(mock_db):
    return SMSChannelHandler(db=mock_db, channel=NotificationChannel.SMS)


@pytest.fixture
def request_obj():
    return NotificationRequest(
        recipient_id=5,
        notification_type="ALERT",
        category="alert",
        title="SMS Test",
        content="content",
    )


def test_send_disabled_returns_failure(handler, request_obj):
    """SMS未启用时返回 success=False"""
    with patch("app.services.channel_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = False
        result = handler.send(request_obj)
        assert result.success is False
        assert "未启用" in result.error_message


def test_send_no_user_returns_failure(handler, mock_db, request_obj):
    """用户不存在时返回 success=False"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    with patch("app.services.channel_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = True
        result = handler.send(request_obj)
        assert result.success is False


def test_send_no_phone_returns_failure(handler, mock_db, request_obj):
    """用户无手机号时返回 success=False"""
    user = MagicMock()
    user.phone = None
    mock_db.query.return_value.filter.return_value.first.return_value = user
    with patch("app.services.channel_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = True
        result = handler.send(request_obj)
        assert result.success is False
        assert "手机号" in result.error_message


def test_send_success(handler, mock_db, request_obj):
    """正常情况下返回 success=True"""
    user = MagicMock()
    user.phone = "13800138000"
    mock_db.query.return_value.filter.return_value.first.return_value = user
    with patch("app.services.channel_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = True
        result = handler.send(request_obj)
        assert result.success is True


def test_is_enabled_true(handler):
    """SMS_ENABLED=True 时 is_enabled 返回 True"""
    with patch("app.services.channel_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = True
        assert handler.is_enabled() is True


def test_is_enabled_false(handler):
    """SMS_ENABLED=False 时 is_enabled 返回 False"""
    with patch("app.services.channel_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = False
        assert handler.is_enabled() is False


def test_result_channel_is_sms(handler, mock_db, request_obj):
    """返回结果的 channel 应是 sms"""
    user = MagicMock()
    user.phone = "13900139000"
    mock_db.query.return_value.filter.return_value.first.return_value = user
    with patch("app.services.channel_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = True
        result = handler.send(request_obj)
        assert result.channel == NotificationChannel.SMS

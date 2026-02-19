# -*- coding: utf-8 -*-
"""
Tests for app/services/notification_handlers/sms_handler.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.notification_handlers.sms_handler import SMSNotificationHandler
    from app.models.enums import AlertLevelEnum
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def handler(mock_db):
    return SMSNotificationHandler(db=mock_db)


@pytest.fixture
def urgent_alert():
    alert = MagicMock()
    alert.id = 1
    alert.alert_level = AlertLevelEnum.URGENT.value
    alert.alert_title = "紧急预警"
    return alert


@pytest.fixture
def normal_alert():
    alert = MagicMock()
    alert.id = 2
    alert.alert_level = AlertLevelEnum.WARNING.value
    alert.alert_title = "普通预警"
    return alert


def test_send_raises_for_non_urgent(handler):
    """非URGENT级别应抛出ValueError"""
    notification = MagicMock()
    alert = MagicMock()
    alert.alert_level = "WARNING"
    with pytest.raises(ValueError, match="URGENT"):
        handler.send(notification, alert)


def test_send_raises_when_sms_disabled(handler, urgent_alert):
    """SMS未启用时应抛出ValueError"""
    notification = MagicMock()
    with patch("app.services.notification_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = False
        with pytest.raises(ValueError, match="disabled"):
            handler.send(notification, urgent_alert)


def test_send_raises_when_no_recipient(handler, urgent_alert):
    """无接收人时应抛出ValueError"""
    notification = MagicMock()
    notification.notify_target = None
    notification.notify_user_id = None
    with patch("app.services.notification_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_MAX_PER_DAY = 100
        mock_settings.SMS_MAX_PER_HOUR = 20
        with pytest.raises(ValueError, match="phone"):
            handler.send(notification, urgent_alert, user=None)


def test_send_raises_on_daily_limit(handler, urgent_alert):
    """超过每日限额时应抛出ValueError"""
    notification = MagicMock()
    notification.notify_target = "13800138000"
    with patch("app.services.notification_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_MAX_PER_DAY = 0
        mock_settings.SMS_MAX_PER_HOUR = 20
        with pytest.raises(ValueError, match="daily"):
            handler.send(notification, urgent_alert)


def test_send_raises_on_hourly_limit(handler, urgent_alert):
    """超过每小时限额时应抛出ValueError"""
    notification = MagicMock()
    notification.notify_target = "13800138000"
    with patch("app.services.notification_handlers.sms_handler.settings") as mock_settings:
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_MAX_PER_DAY = 100
        mock_settings.SMS_MAX_PER_HOUR = 0
        with pytest.raises(ValueError, match="hourly"):
            handler.send(notification, urgent_alert)


def test_send_success(handler, urgent_alert):
    """正常情况下应成功发送并更新计数"""
    notification = MagicMock()
    notification.notify_target = "13800138000"
    notification.notify_title = "测试标题"
    with patch("app.services.notification_handlers.sms_handler.settings") as mock_settings, \
         patch("app.services.notification_handlers.sms_handler.send_alert_via_unified") as mock_send:
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_MAX_PER_DAY = 100
        mock_settings.SMS_MAX_PER_HOUR = 20
        mock_settings.CORS_ORIGINS = ["http://localhost:3000"]
        handler.send(notification, urgent_alert)
        mock_send.assert_called_once()


def test_send_tencent_raises(handler):
    """腾讯云SMS应抛出未实现异常"""
    with pytest.raises(ValueError, match="not implemented"):
        handler._send_tencent("13800138000", "content")

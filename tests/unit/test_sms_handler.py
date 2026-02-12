# -*- coding: utf-8 -*-
"""短信通知处理器 单元测试"""
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import AlertLevelEnum
from app.services.notification_handlers.sms_handler import SMSNotificationHandler


def _make_handler():
    db = MagicMock()
    h = SMSNotificationHandler(db)
    return h


def _make_notification(**kw):
    n = MagicMock()
    n.notify_target = kw.get("notify_target", "13800138000")
    n.notify_title = kw.get("notify_title", "测试通知")
    n.notify_user_id = kw.get("notify_user_id", None)
    return n


def _make_alert(**kw):
    a = MagicMock()
    a.id = kw.get("id", 1)
    a.alert_level = kw.get("alert_level", AlertLevelEnum.URGENT.value)
    a.alert_title = kw.get("alert_title", "紧急预警")
    return a


class TestSMSSend:
    @patch("app.services.notification_handlers.sms_handler.settings")
    @patch("app.services.notification_handlers.sms_handler.send_alert_via_unified")
    def test_send_success(self, mock_send, mock_settings):
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_MAX_PER_DAY = 100
        mock_settings.SMS_MAX_PER_HOUR = 20
        mock_settings.CORS_ORIGINS = ["http://localhost:3000"]

        h = _make_handler()
        notification = _make_notification()
        alert = _make_alert()
        h.send(notification, alert)
        mock_send.assert_called_once()

    def test_non_urgent_rejected(self):
        h = _make_handler()
        notification = _make_notification()
        alert = _make_alert(alert_level="WARNING")
        with pytest.raises(ValueError, match="URGENT"):
            h.send(notification, alert)

    @patch("app.services.notification_handlers.sms_handler.settings")
    def test_sms_disabled(self, mock_settings):
        mock_settings.SMS_ENABLED = False
        h = _make_handler()
        notification = _make_notification()
        alert = _make_alert()
        with pytest.raises(ValueError, match="disabled"):
            h.send(notification, alert)

    @patch("app.services.notification_handlers.sms_handler.settings")
    def test_no_recipient(self, mock_settings):
        mock_settings.SMS_ENABLED = True
        h = _make_handler()
        notification = _make_notification(notify_target=None, notify_user_id=None)
        alert = _make_alert()
        with pytest.raises(ValueError, match="phone"):
            h.send(notification, alert, user=None)

    @patch("app.services.notification_handlers.sms_handler.settings")
    def test_daily_limit(self, mock_settings):
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_MAX_PER_DAY = 0
        mock_settings.SMS_MAX_PER_HOUR = 20
        h = _make_handler()
        notification = _make_notification()
        alert = _make_alert()
        with pytest.raises(ValueError, match="daily limit"):
            h.send(notification, alert)


class TestRetrySchedule:
    def test_retry_schedule_defined(self):
        assert SMSNotificationHandler.RETRY_SCHEDULE == [5, 15, 30, 60]

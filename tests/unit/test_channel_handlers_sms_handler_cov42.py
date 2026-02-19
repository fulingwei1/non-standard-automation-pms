# -*- coding: utf-8 -*-
"""第四十二批：channel_handlers/sms_handler.py 单元测试"""
import pytest

pytest.importorskip("app.services.channel_handlers.sms_handler")

from unittest.mock import MagicMock, patch
from app.services.channel_handlers.sms_handler import SMSChannelHandler
from app.services.channel_handlers.base import NotificationRequest, NotificationPriority


def make_request(**kwargs):
    defaults = dict(
        recipient_id=1, notification_type="ALERT", category="test",
        title="短信标题", content="短信内容",
    )
    defaults.update(kwargs)
    return NotificationRequest(**defaults)


def make_handler(sms_enabled=True):
    db = MagicMock()
    handler = SMSChannelHandler(db, "sms")
    return handler, db


# ------------------------------------------------------------------ tests ---

def test_is_enabled_when_setting_true():
    handler, _ = make_handler()
    with patch("app.services.channel_handlers.sms_handler.settings") as ms:
        ms.SMS_ENABLED = True
        assert handler.is_enabled() is True


def test_is_enabled_when_setting_false():
    handler, _ = make_handler()
    with patch("app.services.channel_handlers.sms_handler.settings") as ms:
        ms.SMS_ENABLED = False
        assert handler.is_enabled() is False


def test_send_fails_when_disabled():
    handler, _ = make_handler()
    with patch("app.services.channel_handlers.sms_handler.settings") as ms:
        ms.SMS_ENABLED = False
        result = handler.send(make_request())
    assert result.success is False
    assert "未启用" in result.error_message


def test_send_fails_when_no_recipient():
    handler, db = make_handler()
    db.query.return_value.filter.return_value.first.return_value = None
    with patch("app.services.channel_handlers.sms_handler.settings") as ms:
        ms.SMS_ENABLED = True
        result = handler.send(make_request())
    assert result.success is False
    assert "用户" in result.error_message


def test_send_fails_when_no_phone():
    handler, db = make_handler()
    user = MagicMock()
    user.phone = None
    db.query.return_value.filter.return_value.first.return_value = user
    with patch("app.services.channel_handlers.sms_handler.settings") as ms:
        ms.SMS_ENABLED = True
        result = handler.send(make_request())
    assert result.success is False
    assert "手机号" in result.error_message


def test_send_succeeds_with_valid_user():
    handler, db = make_handler()
    user = MagicMock()
    user.phone = "13800138000"
    db.query.return_value.filter.return_value.first.return_value = user
    with patch("app.services.channel_handlers.sms_handler.settings") as ms:
        ms.SMS_ENABLED = True
        result = handler.send(make_request())
    assert result.success is True
    assert result.channel == "sms"


def test_channel_attribute():
    handler, _ = make_handler()
    assert handler.channel == "sms"

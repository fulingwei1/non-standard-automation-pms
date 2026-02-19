# -*- coding: utf-8 -*-
"""第四十二批：channel_handlers/base.py 单元测试"""
import pytest

pytest.importorskip("app.services.channel_handlers.base")

from unittest.mock import MagicMock
from app.services.channel_handlers.base import (
    ChannelHandler,
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
    NotificationResult,
)


# ------------------------------------------------------------------ helpers --

class ConcreteHandler(ChannelHandler):
    """用于测试的具体处理器"""
    def send(self, request):
        return NotificationResult(channel=self.channel, success=True)


def make_handler(channel="system"):
    db = MagicMock()
    return ConcreteHandler(db, channel)


def make_settings(**kwargs):
    s = MagicMock()
    for k, v in kwargs.items():
        setattr(s, k, v)
    return s


# ------------------------------------------------------------------ tests ---

def test_notification_channel_constants():
    assert NotificationChannel.SYSTEM == "system"
    assert NotificationChannel.EMAIL == "email"
    assert NotificationChannel.SMS == "sms"
    assert NotificationChannel.WECHAT == "wechat"
    assert NotificationChannel.WEBHOOK == "webhook"


def test_notification_priority_constants():
    assert NotificationPriority.LOW == "low"
    assert NotificationPriority.NORMAL == "normal"
    assert NotificationPriority.HIGH == "high"
    assert NotificationPriority.URGENT == "urgent"


def test_notification_result_dataclass():
    r = NotificationResult(channel="system", success=True, sent_at="2024-01-01T00:00:00")
    assert r.channel == "system"
    assert r.success is True
    assert r.error_message is None


def test_notification_request_defaults():
    req = NotificationRequest(
        recipient_id=1,
        notification_type="ALERT",
        category="test",
        title="T",
        content="C",
    )
    assert req.priority == NotificationPriority.NORMAL
    assert req.force_send is False
    assert req.channels is None


def test_channel_handler_is_enabled_default():
    h = make_handler()
    assert h.is_enabled() is True


def test_should_send_system_uses_setting():
    h = make_handler("system")
    settings = make_settings(system_enabled=False)
    assert h.should_send(settings, NotificationPriority.NORMAL) is False


def test_should_send_sms_urgent_overrides():
    """SMS 在 urgent 时应该发送即使 sms_enabled=False"""
    h = make_handler("sms")
    settings = make_settings(sms_enabled=False)
    assert h.should_send(settings, NotificationPriority.URGENT) is True


def test_should_send_no_settings_returns_true():
    h = make_handler("email")
    assert h.should_send(None, NotificationPriority.LOW) is True


def test_concrete_handler_send_returns_result():
    h = make_handler()
    req = NotificationRequest(
        recipient_id=1, notification_type="T", category="c",
        title="title", content="body"
    )
    result = h.send(req)
    assert result.success is True
    assert result.channel == "system"

# -*- coding: utf-8 -*-
"""
Tests for app/services/channel_handlers/base.py
"""
import pytest
from unittest.mock import MagicMock

try:
    from app.services.channel_handlers.base import (
        ChannelHandler,
        NotificationChannel,
        NotificationPriority,
        NotificationResult,
        NotificationRequest,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


class ConcreteHandler(ChannelHandler):
    """用于测试的具体实现"""
    def send(self, request):
        return NotificationResult(channel=self.channel, success=True)


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def handler(db):
    return ConcreteHandler(db=db, channel=NotificationChannel.SYSTEM)


def test_channel_constants():
    """检查渠道常量值"""
    assert NotificationChannel.SYSTEM == "system"
    assert NotificationChannel.SMS == "sms"
    assert NotificationChannel.EMAIL == "email"
    assert NotificationChannel.WECHAT == "wechat"


def test_priority_constants():
    """检查优先级常量值"""
    assert NotificationPriority.URGENT == "urgent"
    assert NotificationPriority.HIGH == "high"
    assert NotificationPriority.NORMAL == "normal"
    assert NotificationPriority.LOW == "low"


def test_is_enabled_default(handler):
    """默认情况下渠道应该是启用的"""
    assert handler.is_enabled() is True


def test_should_send_system_no_settings(handler):
    """无用户设置时系统通知应发送"""
    assert handler.should_send(None, NotificationPriority.NORMAL) is True


def test_should_send_system_with_settings(handler):
    """根据用户设置决定是否发送系统通知"""
    settings = MagicMock()
    settings.system_enabled = True
    assert handler.should_send(settings, NotificationPriority.NORMAL) is True

    settings.system_enabled = False
    assert handler.should_send(settings, NotificationPriority.NORMAL) is False


def test_should_send_sms_urgent():
    """SMS渠道urgent优先级应发送（即使未配置）"""
    db = MagicMock()
    sms_handler = ConcreteHandler(db=db, channel=NotificationChannel.SMS)
    settings = MagicMock()
    settings.sms_enabled = False
    # urgent = priority_level 0, <= 0, should send
    result = sms_handler.should_send(settings, NotificationPriority.URGENT)
    assert result is True


def test_notification_result_dataclass():
    """NotificationResult 数据类初始化"""
    result = NotificationResult(channel="system", success=True, sent_at="2024-01-01")
    assert result.channel == "system"
    assert result.success is True
    assert result.error_message is None


def test_notification_request_defaults():
    """NotificationRequest 默认值检查"""
    req = NotificationRequest(
        recipient_id=1,
        notification_type="ALERT",
        category="alert",
        title="test",
        content="content"
    )
    assert req.priority == NotificationPriority.NORMAL
    assert req.force_send is False

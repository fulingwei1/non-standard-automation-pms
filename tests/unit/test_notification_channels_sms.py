# -*- coding: utf-8 -*-
"""短信通知通道处理器 (SMSChannelHandler) 单元测试"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.channel_handlers.base import NotificationRequest, NotificationResult
from app.services.notification.channels.sms_handler import SMSChannelHandler


@pytest.fixture
def mock_db():
    """创建模拟的数据库会话"""
    return MagicMock()


@pytest.fixture
def handler(mock_db):
    """创建短信通道处理器"""
    return SMSChannelHandler(db=mock_db, channel="sms")


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = MagicMock()
    user.id = 1
    user.phone = "13800138000"
    return user


class TestSMSChannelHandler:
    """SMSChannelHandler 测试类"""

    @patch("app.services.notification.channels.sms_handler.settings")
    def test_send_sms_disabled(self, mock_settings, handler):
        """测试短信功能未启用时返回失败"""
        mock_settings.SMS_ENABLED = False
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="测试短信",
            content="测试内容",
        )
        result = handler.send(request)
        assert result.success is False
        assert "未启用" in result.error_message

    @patch("app.services.notification.channels.sms_handler.settings")
    def test_send_user_not_found(self, mock_settings, handler, mock_db):
        """测试用户不存在时返回失败"""
        mock_settings.SMS_ENABLED = True
        mock_db.query.return_value.filter.return_value.first.return_value = None
        request = NotificationRequest(
            recipient_id=999,
            notification_type="alert",
            category="system",
            title="测试短信",
            content="测试内容",
        )
        result = handler.send(request)
        assert result.success is False
        assert "用户未配置手机号" in result.error_message

    @patch("app.services.notification.channels.sms_handler.settings")
    def test_send_user_no_phone(self, mock_settings, handler, mock_db):
        """测试用户没有配置手机号时返回失败"""
        mock_settings.SMS_ENABLED = True
        user = MagicMock()
        user.id = 1
        user.phone = None
        mock_db.query.return_value.filter.return_value.first.return_value = user
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="测试短信",
            content="测试内容",
        )
        result = handler.send(request)
        assert result.success is False
        assert "用户未配置手机号" in result.error_message

    @patch("app.services.notification.channels.sms_handler.settings")
    def test_send_success(self, mock_settings, handler, mock_db, mock_user):
        """测试发送短信成功"""
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_PROVIDER = "aliyun"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_ID = "key-id"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_SECRET = "key-secret"
        mock_settings.SMS_ALIYUN_SIGN_NAME = "签名"
        mock_settings.SMS_ALIYUN_TEMPLATE_CODE = "SMS_001"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="测试短信",
            content="测试内容",
        )
        with patch.object(SMSChannelHandler, "_send_aliyun") as mock_send_aliyun:
            result = handler.send(request)
        assert result.success is True
        assert result.channel == "sms"
        mock_send_aliyun.assert_called_once()

    @patch("app.services.notification.channels.sms_handler.settings")
    def test_send_missing_gateway_config_fails(self, mock_settings, handler, mock_db, mock_user):
        """测试缺少短信网关配置时返回失败"""
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_PROVIDER = "aliyun"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_ID = None
        mock_settings.SMS_ALIYUN_ACCESS_KEY_SECRET = None
        mock_settings.SMS_ALIYUN_SIGN_NAME = None
        mock_settings.SMS_ALIYUN_TEMPLATE_CODE = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="测试短信",
            content="测试内容",
        )
        result = handler.send(request)
        assert result.success is False
        assert "短信网关配置不完整" in result.error_message

    def test_is_enabled_when_sms_disabled(self, handler):
        """测试 is_enabled 返回正确状态 - 禁用"""
        with patch("app.services.notification.channels.sms_handler.settings") as mock_settings:
            mock_settings.SMS_ENABLED = False
            assert handler.is_enabled() is False

    def test_is_enabled_when_sms_enabled(self, handler):
        """测试 is_enabled 返回正确状态 - 启用"""
        with patch("app.services.notification.channels.sms_handler.settings") as mock_settings:
            mock_settings.SMS_ENABLED = True
            assert handler.is_enabled() is True

    @patch("app.services.notification.channels.sms_handler.settings")
    def test_send_with_priority(self, mock_settings, handler, mock_db, mock_user):
        """测试带优先级的短信发送"""
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_PROVIDER = "aliyun"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_ID = "key-id"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_SECRET = "key-secret"
        mock_settings.SMS_ALIYUN_SIGN_NAME = "签名"
        mock_settings.SMS_ALIYUN_TEMPLATE_CODE = "SMS_001"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="紧急短信",
            content="测试内容",
            priority="urgent",
        )
        with patch.object(SMSChannelHandler, "_send_aliyun"):
            result = handler.send(request)
        assert result.success is True

    @patch("app.services.notification.channels.sms_handler.settings")
    def test_send_logging(self, mock_settings, handler, mock_db, mock_user, caplog):
        """测试短信发送日志"""
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_PROVIDER = "aliyun"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_ID = "key-id"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_SECRET = "key-secret"
        mock_settings.SMS_ALIYUN_SIGN_NAME = "签名"
        mock_settings.SMS_ALIYUN_TEMPLATE_CODE = "SMS_001"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="测试短信",
            content="测试内容",
        )
        with patch.object(SMSChannelHandler, "_send_aliyun"):
            handler.send(request)
        # 验证日志被记录
        assert "短信通知" in caplog.text
        assert "13800138000" in caplog.text

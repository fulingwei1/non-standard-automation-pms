# -*- coding: utf-8 -*-
"""
短信通知处理器测试
"""
from unittest.mock import Mock, patch
import pytest

from app.services.notification.channels.sms_handler import SMSChannelHandler
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationChannel,
    NotificationPriority,
)
from app.models.user import User


class TestSMSChannelHandler:
    """SMSChannelHandler 测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = Mock()
        return db

    @pytest.fixture
    def sms_handler(self, mock_db):
        """创建短信处理器实例"""
        return SMSChannelHandler(mock_db, NotificationChannel.SMS)

    @pytest.fixture
    def mock_user_with_phone(self):
        """创建带手机号的用户"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.phone = "13800138000"
        return user

    @pytest.fixture
    def mock_user_without_phone(self):
        """创建不带手机号的用户"""
        user = Mock(spec=User)
        user.id = 2
        user.email = "test@example.com"
        user.phone = None
        return user

    @patch('app.services.notification.channels.sms_handler.settings')
    def test_send_sms_success(self, mock_settings, sms_handler, mock_db, mock_user_with_phone):
        """测试短信发送成功"""
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_PROVIDER = "aliyun"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_ID = "key-id"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_SECRET = "key-secret"
        mock_settings.SMS_ALIYUN_SIGN_NAME = "签名"
        mock_settings.SMS_ALIYUN_TEMPLATE_CODE = "SMS_001"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user_with_phone
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试短信",
            content="这是测试内容",
            priority=NotificationPriority.NORMAL,
        )

        with patch.object(SMSChannelHandler, "_send_aliyun") as mock_send_aliyun:
            result = sms_handler.send(request)

        assert result.success is True
        assert result.channel == NotificationChannel.SMS
        mock_send_aliyun.assert_called_once()

    @patch('app.services.notification.channels.sms_handler.settings')
    def test_send_sms_user_not_found(self, mock_settings, sms_handler, mock_db):
        """测试用户不存在"""
        mock_settings.SMS_ENABLED = True
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=999,
            notification_type="TEST",
            category="test",
            title="测试短信",
            content="这是测试内容",
        )

        result = sms_handler.send(request)

        assert result.success is False
        assert "未找到" in result.error_message or "不存在" in result.error_message or "用户" in result.error_message

    @patch('app.services.notification.channels.sms_handler.settings')
    def test_send_sms_user_without_phone(self, mock_settings, sms_handler, mock_db, mock_user_without_phone):
        """测试用户未配置手机号"""
        mock_settings.SMS_ENABLED = True
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user_without_phone
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=2,
            notification_type="TEST",
            category="test",
            title="测试短信",
            content="这是测试内容",
        )

        result = sms_handler.send(request)

        assert result.success is False
        assert "手机" in result.error_message or "电话" in result.error_message

    @patch('app.services.notification.channels.sms_handler.settings')
    def test_send_sms_missing_gateway_config_fails(
        self, mock_settings, sms_handler, mock_db, mock_user_with_phone
    ):
        """测试缺少短信网关配置时不能假报发送成功"""
        mock_settings.SMS_ENABLED = True
        mock_settings.SMS_PROVIDER = "aliyun"
        mock_settings.SMS_ALIYUN_ACCESS_KEY_ID = None
        mock_settings.SMS_ALIYUN_ACCESS_KEY_SECRET = None
        mock_settings.SMS_ALIYUN_SIGN_NAME = None
        mock_settings.SMS_ALIYUN_TEMPLATE_CODE = None

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user_with_phone
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试短信",
            content="这是测试内容",
        )

        result = sms_handler.send(request)

        assert result.success is False
        assert "短信网关配置不完整" in result.error_message

    @patch('app.services.notification.channels.sms_handler.settings')
    def test_send_sms_disabled(self, mock_settings, sms_handler, mock_db):
        """测试短信功能未启用"""
        mock_settings.SMS_ENABLED = False

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试短信",
            content="这是测试内容",
        )

        result = sms_handler.send(request)

        assert result.success is False
        assert "未启用" in result.error_message


class TestSMSChannelHandlerEdgeCases:
    """SMSChannelHandler 边界情况测试"""

    @pytest.fixture
    def mock_db(self):
        db = Mock()
        return db

    @pytest.fixture
    def sms_handler(self, mock_db):
        return SMSChannelHandler(mock_db, NotificationChannel.SMS)

    @patch('app.services.notification.channels.sms_handler.settings')
    def test_is_enabled_returns_true_by_default(self, mock_settings, sms_handler):
        """测试默认启用状态"""
        mock_settings.SMS_ENABLED = True
        assert sms_handler.is_enabled() is True

    @patch('app.services.notification.channels.sms_handler.settings')
    def test_is_enabled_respects_settings(self, mock_settings, sms_handler):
        """测试is_enabled正确读取配置"""
        mock_settings.SMS_ENABLED = True
        assert sms_handler.is_enabled() is True

        mock_settings.SMS_ENABLED = False
        assert sms_handler.is_enabled() is False

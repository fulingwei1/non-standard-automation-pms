# -*- coding: utf-8 -*-
"""
邮件通知处理器测试
"""
from unittest.mock import Mock, patch
import pytest

from app.services.notification.channels.email_handler import EmailChannelHandler
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationChannel,
    NotificationPriority,
)
from app.models.user import User


class TestEmailChannelHandler:
    """EmailChannelHandler 测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = Mock()
        return db

    @pytest.fixture
    def email_handler(self, mock_db):
        """创建邮件处理器实例"""
        return EmailChannelHandler(mock_db, NotificationChannel.EMAIL)

    @pytest.fixture
    def mock_user_with_email(self):
        """创建带邮箱的用户"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.phone = "13800138000"
        return user

    @pytest.fixture
    def mock_user_without_email(self):
        """创建不带邮箱的用户"""
        user = Mock(spec=User)
        user.id = 2
        user.email = None
        user.phone = "13800138000"
        return user

    @patch('app.services.notification.channels.email_handler.settings')
    def test_send_email_success(self, mock_settings, email_handler, mock_db, mock_user_with_email):
        """测试邮件发送成功"""
        mock_settings.EMAIL_ENABLED = True
        mock_settings.EMAIL_FROM = "noreply@example.com"
        mock_settings.EMAIL_SMTP_SERVER = "smtp.example.com"
        mock_settings.EMAIL_SMTP_PORT = 587
        
        # Mock查询返回用户
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user_with_email
        mock_db.query.return_value = mock_query

        # 创建通知请求
        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试邮件",
            content="这是测试内容",
            priority=NotificationPriority.NORMAL,
        )

        with patch("app.services.notification.channels.email_handler.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = Mock()
            mock_smtp_cls.return_value = mock_smtp

            # 执行发送
            result = email_handler.send(request)

        # 验证结果
        assert result.success is True
        assert result.channel == NotificationChannel.EMAIL
        assert result.sent_at is not None
        mock_smtp.send_message.assert_called_once()
        mock_db.query.assert_called_once()

    @patch('app.services.notification.channels.email_handler.settings')
    def test_send_email_user_not_found(self, mock_settings, email_handler, mock_db):
        """测试用户不存在"""
        mock_settings.EMAIL_ENABLED = True
        
        # Mock查询返回None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=999,
            notification_type="TEST",
            category="test",
            title="测试邮件",
            content="这是测试内容",
        )

        result = email_handler.send(request)

        assert result.success is False
        assert "未找到" in result.error_message or "不存在" in result.error_message or "用户" in result.error_message

    @patch('app.services.notification.channels.email_handler.settings')
    def test_send_email_user_without_email(self, mock_settings, email_handler, mock_db, mock_user_without_email):
        """测试用户未配置邮箱"""
        mock_settings.EMAIL_ENABLED = True
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user_without_email
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=2,
            notification_type="TEST",
            category="test",
            title="测试邮件",
            content="这是测试内容",
        )

        result = email_handler.send(request)

        assert result.success is False
        assert "邮箱" in result.error_message

    @patch('app.services.notification.channels.email_handler.settings')
    def test_send_email_missing_smtp_config_fails(
        self, mock_settings, email_handler, mock_db, mock_user_with_email
    ):
        """测试缺少SMTP配置时不能假报发送成功"""
        mock_settings.EMAIL_ENABLED = True
        mock_settings.EMAIL_FROM = None
        mock_settings.EMAIL_SMTP_SERVER = None

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user_with_email
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试邮件",
            content="这是测试内容",
        )

        result = email_handler.send(request)

        assert result.success is False
        assert "SMTP配置不完整" in result.error_message

    @patch('app.services.notification.channels.email_handler.settings')
    def test_send_email_disabled(self, mock_settings, email_handler, mock_db):
        """测试邮件功能未启用"""
        mock_settings.EMAIL_ENABLED = False

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试邮件",
            content="这是测试内容",
        )

        result = email_handler.send(request)

        assert result.success is False
        assert "未启用" in result.error_message

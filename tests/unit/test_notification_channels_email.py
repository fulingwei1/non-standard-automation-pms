# -*- coding: utf-8 -*-
"""邮件通知通道处理器 (EmailChannelHandler) 单元测试"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.channel_handlers.base import NotificationRequest, NotificationResult
from app.services.notification.channels.email_handler import EmailChannelHandler


@pytest.fixture
def mock_db():
    """创建模拟的数据库会话"""
    return MagicMock()


@pytest.fixture
def handler(mock_db):
    """创建邮件通道处理器"""
    return EmailChannelHandler(db=mock_db, channel="email")


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    return user


class TestEmailChannelHandler:
    """EmailChannelHandler 测试类"""

    @patch("app.services.notification.channels.email_handler.settings")
    def test_send_email_disabled(self, mock_settings, handler):
        """测试邮件功能未启用时返回失败"""
        mock_settings.EMAIL_ENABLED = False
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="测试邮件",
            content="测试内容",
        )
        result = handler.send(request)
        assert result.success is False
        assert "未启用" in result.error_message

    @patch("app.services.notification.channels.email_handler.settings")
    def test_send_user_not_found(self, mock_settings, handler, mock_db):
        """测试用户不存在时返回失败"""
        mock_settings.EMAIL_ENABLED = True
        mock_db.query.return_value.filter.return_value.first.return_value = None
        request = NotificationRequest(
            recipient_id=999,
            notification_type="alert",
            category="system",
            title="测试邮件",
            content="测试内容",
        )
        result = handler.send(request)
        assert result.success is False
        assert "未配置邮箱" in result.error_message

    @patch("app.services.notification.channels.email_handler.settings")
    def test_send_user_no_email(self, mock_settings, handler, mock_db):
        """测试用户没有配置邮箱时返回失败"""
        mock_settings.EMAIL_ENABLED = True
        user = MagicMock()
        user.id = 1
        user.email = None
        mock_db.query.return_value.filter.return_value.first.return_value = user
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="测试邮件",
            content="测试内容",
        )
        result = handler.send(request)
        assert result.success is False
        assert "未配置邮箱" in result.error_message

    @patch("app.services.notification.channels.email_handler.settings")
    def test_send_success(self, mock_settings, handler, mock_db, mock_user):
        """测试发送邮件成功"""
        mock_settings.EMAIL_ENABLED = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        request = NotificationRequest(
            recipient_id=1,
            notification_type="alert",
            category="system",
            title="测试邮件",
            content="测试内容",
        )
        result = handler.send(request)
        assert result.success is True
        assert result.channel == "email"
        assert result.sent_at is not None

    def test_is_enabled_when_email_disabled(self, handler):
        """测试 is_enabled 返回正确状态 - 禁用"""
        with patch("app.services.notification.channels.email_handler.settings") as mock_settings:
            mock_settings.EMAIL_ENABLED = False
            assert handler.is_enabled() is False

    def test_is_enabled_when_email_enabled(self, handler):
        """测试 is_enabled 返回正确状态 - 启用"""
        with patch("app.services.notification.channels.email_handler.settings") as mock_settings:
            mock_settings.EMAIL_ENABLED = True
            assert handler.is_enabled() is True
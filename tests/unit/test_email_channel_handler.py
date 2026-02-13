# -*- coding: utf-8 -*-
"""邮件通知处理器单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.channel_handlers.email_handler import EmailChannelHandler
from app.services.channel_handlers.base import NotificationRequest, NotificationResult


class TestEmailChannelHandler:
    def setup_method(self):
        self.db = MagicMock()
        self.handler = EmailChannelHandler(self.db, "email")

    @patch("app.services.channel_handlers.email_handler.settings")
    def test_send_disabled(self, mock_settings):
        mock_settings.EMAIL_ENABLED = False
        request = MagicMock(spec=NotificationRequest)
        result = self.handler.send(request)
        assert result.success is False

    @patch("app.services.channel_handlers.email_handler.settings")
    def test_send_no_email(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        user = MagicMock()
        user.email = None
        self.db.query.return_value.filter.return_value.first.return_value = user
        request = MagicMock(spec=NotificationRequest)
        request.recipient_id = 1
        result = self.handler.send(request)
        assert result.success is False

    @patch("app.services.channel_handlers.email_handler.settings")
    def test_send_success(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        user = MagicMock()
        user.email = "test@example.com"
        self.db.query.return_value.filter.return_value.first.return_value = user
        request = MagicMock(spec=NotificationRequest)
        request.recipient_id = 1
        request.title = "测试"
        result = self.handler.send(request)
        assert result.success is True

    @patch("app.services.channel_handlers.email_handler.settings")
    def test_is_enabled(self, mock_settings):
        mock_settings.EMAIL_ENABLED = True
        assert self.handler.is_enabled() is True

# -*- coding: utf-8 -*-
"""Webhook通知处理器单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.channel_handlers.webhook_handler import WebhookChannelHandler
from app.services.channel_handlers.base import NotificationRequest, NotificationResult


class TestWebhookChannelHandler:
    def setup_method(self):
        self.db = MagicMock()
        self.handler = WebhookChannelHandler(self.db, "webhook")

    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_send_disabled(self, mock_settings):
        mock_settings.WECHAT_WEBHOOK_URL = ""
        request = MagicMock(spec=NotificationRequest)
        result = self.handler.send(request)
        assert result.success is False

    @patch("app.services.channel_handlers.webhook_handler.requests")
    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_send_success(self, mock_settings, mock_requests):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/hook"
        mock_requests.post.return_value.status_code = 200
        request = MagicMock(spec=NotificationRequest)
        request.title = "测试"
        request.content = "内容"
        request.wechat_template = None
        result = self.handler.send(request)
        assert result.success is True

    @patch("app.services.channel_handlers.webhook_handler.requests")
    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_send_failure(self, mock_settings, mock_requests):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/hook"
        mock_requests.post.side_effect = Exception("timeout")
        request = MagicMock(spec=NotificationRequest)
        request.wechat_template = None
        request.title = "测试"
        request.content = "内容"
        result = self.handler.send(request)
        assert result.success is False

    def test_build_message_with_template(self):
        request = MagicMock(spec=NotificationRequest)
        request.wechat_template = {"msgtype": "markdown", "markdown": {"content": "test"}}
        result = self.handler._build_message(request)
        assert result == request.wechat_template

    def test_build_message_without_template(self):
        request = MagicMock(spec=NotificationRequest)
        request.wechat_template = None
        request.title = "标题"
        request.content = "内容"
        result = self.handler._build_message(request)
        assert result["msgtype"] == "text"

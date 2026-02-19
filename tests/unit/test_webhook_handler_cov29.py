# -*- coding: utf-8 -*-
"""第二十九批 - channel_handlers/webhook_handler.py 单元测试（WebhookChannelHandler）"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.channel_handlers.webhook_handler")

from app.services.channel_handlers.webhook_handler import WebhookChannelHandler
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationPriority,
    NotificationChannel,
)


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_request(**kwargs):
    return NotificationRequest(
        recipient_id=kwargs.get("recipient_id", 1),
        notification_type=kwargs.get("notification_type", "TEST"),
        category=kwargs.get("category", "alert"),
        title=kwargs.get("title", "测试标题"),
        content=kwargs.get("content", "测试内容"),
        priority=kwargs.get("priority", NotificationPriority.NORMAL),
        wechat_template=kwargs.get("wechat_template", None),
    )


# ─── 测试：is_enabled ─────────────────────────────────────────────────────────

class TestWebhookHandlerIsEnabled:
    """测试 is_enabled 方法"""

    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_enabled_when_webhook_url_set(self, mock_settings):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/webhook"
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        assert handler.is_enabled() is True

    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_disabled_when_no_webhook_url(self, mock_settings):
        mock_settings.WECHAT_WEBHOOK_URL = ""
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        assert handler.is_enabled() is False

    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_disabled_when_webhook_url_is_none(self, mock_settings):
        mock_settings.WECHAT_WEBHOOK_URL = None
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        assert handler.is_enabled() is False


# ─── 测试：_build_message ─────────────────────────────────────────────────────

class TestWebhookHandlerBuildMessage:
    """测试消息构建"""

    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_uses_wechat_template_when_present(self, mock_settings):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/hook"
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        template = {"msgtype": "markdown", "markdown": {"content": "# 标题"}}
        request = _make_request(wechat_template=template)
        msg = handler._build_message(request)
        assert msg == template

    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_builds_text_message_when_no_template(self, mock_settings):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/hook"
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        request = _make_request(title="通知标题", content="通知内容")
        msg = handler._build_message(request)
        assert msg["msgtype"] == "text"
        assert "通知标题" in msg["text"]["content"]
        assert "通知内容" in msg["text"]["content"]


# ─── 测试：send ───────────────────────────────────────────────────────────────

class TestWebhookHandlerSend:
    """测试 send 方法"""

    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_returns_failure_when_disabled(self, mock_settings):
        mock_settings.WECHAT_WEBHOOK_URL = None
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        result = handler.send(_make_request())
        assert result.success is False
        assert "未配置" in result.error_message

    @patch("app.services.channel_handlers.webhook_handler.requests")
    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_send_success_on_200(self, mock_settings, mock_requests):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/hook"
        resp = MagicMock()
        resp.status_code = 200
        mock_requests.post.return_value = resp
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        result = handler.send(_make_request())
        assert result.success is True
        mock_requests.post.assert_called_once_with(
            "https://example.com/hook",
            json=handler._build_message(_make_request()),
            timeout=10,
        )

    @patch("app.services.channel_handlers.webhook_handler.requests")
    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_send_failure_on_non_200(self, mock_settings, mock_requests):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/hook"
        resp = MagicMock()
        resp.status_code = 500
        mock_requests.post.return_value = resp
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        result = handler.send(_make_request())
        assert result.success is False
        assert "500" in result.error_message

    @patch("app.services.channel_handlers.webhook_handler.requests")
    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_handles_exception_gracefully(self, mock_settings, mock_requests):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/hook"
        mock_requests.post.side_effect = Exception("连接超时")
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        result = handler.send(_make_request())
        assert result.success is False
        assert "连接超时" in result.error_message

    @patch("app.services.channel_handlers.webhook_handler.settings")
    def test_returns_failure_when_requests_is_none(self, mock_settings):
        mock_settings.WECHAT_WEBHOOK_URL = "https://example.com/hook"
        db = _make_db()
        handler = WebhookChannelHandler(db=db, channel=NotificationChannel.WEBHOOK)
        with patch("app.services.channel_handlers.webhook_handler.requests", None):
            result = handler.send(_make_request())
        assert result.success is False
        assert "requests" in result.error_message

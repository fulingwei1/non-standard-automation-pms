# -*- coding: utf-8 -*-
"""webhook_handler单元测试"""
from unittest.mock import Mock, patch

from app.services.notification.channels.base import NotificationChannel, NotificationRequest
from app.services.notification.channels.webhook_handler import WebhookChannelHandler


class TestWebhookChannelHandlerInit:
    def test_init(self):
        service = WebhookChannelHandler(Mock(), NotificationChannel.WEBHOOK)
        assert service is not None
        assert service.channel == NotificationChannel.WEBHOOK

    def test_generic_webhook_url_is_used_without_wechat_url(self):
        """AS-25: generic webhook channel should not be tied only to WECHAT_WEBHOOK_URL."""
        service = WebhookChannelHandler(Mock(), NotificationChannel.WEBHOOK)
        request = NotificationRequest(
            recipient_id=1,
            notification_type="ALERT",
            category="alert",
            title="测试预警",
            content="内容",
        )
        settings = Mock(WEBHOOK_URL="https://webhook.example/send", WECHAT_WEBHOOK_URL=None)
        response = Mock(status_code=200)

        with (
            patch("app.services.notification.channels.webhook_handler.settings", settings),
            patch("app.services.notification.channels.webhook_handler.requests") as requests,
        ):
            requests.post.return_value = response
            result = service.send(request)

        assert result.success is True
        requests.post.assert_called_once()
        assert requests.post.call_args.args[0] == "https://webhook.example/send"

# -*- coding: utf-8 -*-
"""webhook_handler单元测试"""
from unittest.mock import Mock

from app.services.notification.channels.base import NotificationChannel
from app.services.notification.channels.webhook_handler import WebhookChannelHandler


class TestWebhookChannelHandlerInit:
    def test_init(self):
        service = WebhookChannelHandler(Mock(), NotificationChannel.WEBHOOK)
        assert service is not None
        assert service.channel == NotificationChannel.WEBHOOK

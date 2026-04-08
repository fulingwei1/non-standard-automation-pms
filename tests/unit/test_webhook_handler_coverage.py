# -*- coding: utf-8 -*-
"""webhook_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.notification.channels.webhook_handler import WebhookChannelHandler

class TestWebhookChannelHandlerInit:
    def test_init(self):
        service = WebhookChannelHandler(Mock())
        assert service is not None

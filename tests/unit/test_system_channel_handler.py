# -*- coding: utf-8 -*-
"""站内通知处理器单元测试"""
import pytest
from unittest.mock import MagicMock
from app.services.channel_handlers.system_handler import SystemChannelHandler
from app.services.channel_handlers.base import NotificationRequest


class TestSystemChannelHandler:
    def setup_method(self):
        self.db = MagicMock()
        self.handler = SystemChannelHandler(self.db, "system")

    def test_send_creates_notification(self):
        request = MagicMock(spec=NotificationRequest)
        request.recipient_id = 1
        request.notification_type = "TEST"
        request.title = "测试"
        request.content = "内容"
        request.source_type = "test"
        request.source_id = 1
        request.link_url = "/test"
        request.priority = "NORMAL"
        request.extra_data = {}
        result = self.handler.send(request)
        assert result.success is True
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

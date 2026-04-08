# -*- coding: utf-8 -*-
"""wechat_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.notification.handlers.wechat_handler import WeChatNotificationHandler

class TestWeChatNotificationHandlerInit:
    def test_init(self):
        service = WeChatNotificationHandler(Mock())
        assert service is not None

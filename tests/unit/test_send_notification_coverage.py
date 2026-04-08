# -*- coding: utf-8 -*-
"""send_notification单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.notify.send_notification import SendNotificationMixin

class TestSendNotificationMixinInit:
    def test_init(self):
        service = SendNotificationMixin(Mock())
        assert service is not None

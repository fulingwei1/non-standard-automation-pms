# -*- coding: utf-8 -*-
"""system_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.notification.handlers.system_handler import SystemNotificationHandler

class TestSystemNotificationHandlerInit:
    def test_init(self):
        service = SystemNotificationHandler(Mock())
        assert service is not None

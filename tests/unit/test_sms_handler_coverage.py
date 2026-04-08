# -*- coding: utf-8 -*-
"""sms_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.notification.handlers.sms_handler import SMSNotificationHandler

class TestSMSNotificationHandlerInit:
    def test_init(self):
        service = SMSNotificationHandler(Mock())
        assert service is not None

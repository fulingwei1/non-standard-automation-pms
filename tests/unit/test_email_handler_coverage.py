# -*- coding: utf-8 -*-
"""email_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.notification.handlers.email_handler import EmailNotificationHandler

class TestEmailNotificationHandlerInit:
    def test_init(self):
        service = EmailNotificationHandler(Mock())
        assert service is not None

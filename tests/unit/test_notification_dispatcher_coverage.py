# -*- coding: utf-8 -*-
"""notification_dispatcher单元测试"""
import pytest
from unittest.mock import Mock
from app.services.notification.notification_dispatcher import NotificationDispatcher

class TestNotificationDispatcherInit:
    def test_init(self):
        service = NotificationDispatcher(Mock())
        assert service is not None

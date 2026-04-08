# -*- coding: utf-8 -*-
"""unified_notification_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.notification.unified_notification_service import NotificationService

class TestNotificationServiceInit:
    def test_init(self):
        service = NotificationService(Mock())
        assert service is not None

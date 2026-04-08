# -*- coding: utf-8 -*-
"""notification_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.notification.notification_service import AlertNotificationService

class TestAlertNotificationServiceInit:
    def test_init(self):
        service = AlertNotificationService(Mock())
        assert service is not None

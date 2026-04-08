# -*- coding: utf-8 -*-
"""notification_sender单元测试"""
import pytest
from unittest.mock import Mock
from app.services.timesheet.reminder.notification_sender import NotificationSender

class TestNotificationSenderInit:
    def test_init(self):
        service = NotificationSender(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""reminder_notifications单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.notify.reminder_notifications import ReminderNotificationsMixin

class TestReminderNotificationsMixinInit:
    def test_init(self):
        service = ReminderNotificationsMixin(Mock())
        assert service is not None

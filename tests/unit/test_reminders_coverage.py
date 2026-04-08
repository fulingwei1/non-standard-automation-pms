# -*- coding: utf-8 -*-
"""reminders单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_integrity.reminders import RemindersMixin

class TestRemindersMixinInit:
    def test_init(self):
        service = RemindersMixin(Mock())
        assert service is not None

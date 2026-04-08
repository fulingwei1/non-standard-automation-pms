# -*- coding: utf-8 -*-
"""reminder_manager单元测试"""
import pytest
from unittest.mock import Mock
from app.services.timesheet.reminder.reminder_manager import TimesheetReminderManager

class TestTimesheetReminderManagerInit:
    def test_init(self):
        service = TimesheetReminderManager(Mock())
        assert service is not None

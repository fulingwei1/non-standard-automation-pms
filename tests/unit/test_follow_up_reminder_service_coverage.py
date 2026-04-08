# -*- coding: utf-8 -*-
"""follow_up_reminder_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/follow_up_reminder_service import ReminderType

class TestReminderTypeInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ReminderType(mock_db)
        assert hasattr(service, 'db')

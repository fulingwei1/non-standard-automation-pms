# -*- coding: utf-8 -*-
"""dwell_time_monitor单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/dwell_time_monitor import DwellTimeMonitorService

class TestDwellTimeMonitorServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = DwellTimeMonitorService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""engineer_performance_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.engineer_performance.engineer_performance_service import EngineerPerformanceService

class TestEngineerPerformanceServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = EngineerPerformanceService(mock_db)
        assert hasattr(service, 'db')

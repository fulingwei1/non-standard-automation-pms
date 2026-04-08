# -*- coding: utf-8 -*-
"""schedule_optimization_service单元测试"""
import pytest
from unittest.mock import Mock
from services/schedule_optimization_service import ScheduleOptimizationService

class TestScheduleOptimizationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ScheduleOptimizationService(mock_db)
        assert hasattr(service, 'db')

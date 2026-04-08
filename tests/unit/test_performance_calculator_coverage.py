# -*- coding: utf-8 -*-
"""performance_calculator单元测试"""
import pytest
from unittest.mock import Mock
from services/engineer_performance/performance_calculator import PerformanceCalculator

class TestPerformanceCalculatorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PerformanceCalculator(mock_db)
        assert hasattr(service, 'db')

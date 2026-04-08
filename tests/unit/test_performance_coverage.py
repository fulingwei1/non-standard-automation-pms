# -*- coding: utf-8 -*-
"""performance单元测试"""
import pytest
from unittest.mock import Mock
from services/bonus/performance import PerformanceBonusCalculator

class TestPerformanceBonusCalculatorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PerformanceBonusCalculator(mock_db)
        assert hasattr(service, 'db')

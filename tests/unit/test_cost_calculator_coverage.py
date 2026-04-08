# -*- coding: utf-8 -*-
"""cost_calculator单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/cost/cost_calculator import CostCalculator

class TestCostCalculatorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = CostCalculator(mock_db)
        assert hasattr(service, 'db')

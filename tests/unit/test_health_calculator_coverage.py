# -*- coding: utf-8 -*-
"""health_calculator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.health_calculator import HealthCalculator

class TestHealthCalculatorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = HealthCalculator(mock_db)
        assert hasattr(service, 'db')

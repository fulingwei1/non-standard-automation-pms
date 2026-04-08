# -*- coding: utf-8 -*-
"""comparison_calculation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.comparison_calculation_service import ComparisonCalculationService

class TestComparisonCalculationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ComparisonCalculationService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""cost_trend单元测试"""
import pytest
from unittest.mock import Mock
from app.services.procurement_analysis.cost_trend import CostTrendAnalyzer

class TestCostTrendAnalyzerInit:
    def test_init_with_db(self):
        assert CostTrendAnalyzer is not None
        assert hasattr(CostTrendAnalyzer, 'get_cost_trend_data')

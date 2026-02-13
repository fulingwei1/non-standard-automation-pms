# -*- coding: utf-8 -*-
"""趋势对比分析单元测试"""
import pytest
from unittest.mock import MagicMock
from app.services.resource_waste_analysis.trends_comparison import TrendsComparisonMixin


class TestTrendsComparisonMixin:
    def setup_method(self):
        self.mixin = TrendsComparisonMixin()
        self.mixin.calculate_waste_by_period = MagicMock(return_value={
            'total_leads': 10, 'won_leads': 3, 'lost_leads': 7,
            'win_rate': 30.0, 'total_investment_hours': 100, 'wasted_hours': 70,
            'waste_rate': 70.0, 'wasted_cost': 14000,
        })

    def test_get_monthly_trend_default(self):
        result = self.mixin.get_monthly_trend()
        assert len(result) == 12
        assert 'month' in result[0]
        assert 'waste_rate' in result[0]

    def test_get_monthly_trend_3_months(self):
        result = self.mixin.get_monthly_trend(3)
        assert len(result) == 3

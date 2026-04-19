# -*- coding: utf-8 -*-
"""trends_comparison单元测试"""
from app.services.resource_waste_analysis.trends_comparison import TrendsComparisonMixin


class TestTrendsComparisonMixinInit:
    def test_init(self):
        assert hasattr(TrendsComparisonMixin, "get_monthly_trend")

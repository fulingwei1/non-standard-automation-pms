# -*- coding: utf-8 -*-
"""成本趋势分析器别名单元测试"""
import pytest
from app.services.procurement_analysis.cost_trend_analyzer import CostTrendAnalyzer


class TestCostTrendAnalyzerAlias:
    def test_import(self):
        assert CostTrendAnalyzer is not None

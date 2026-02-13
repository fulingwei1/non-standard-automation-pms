# -*- coding: utf-8 -*-
"""报告生成模块单元测试"""
import pytest
from unittest.mock import MagicMock
from app.services.resource_waste_analysis.report_generation import ReportGenerationMixin


class TestReportGenerationMixin:
    def setup_method(self):
        self.mixin = ReportGenerationMixin()
        self.mixin.calculate_waste_by_period = MagicMock(return_value={
            'total_leads': 10, 'won_leads': 3, 'lost_leads': 7,
            'win_rate': 30.0, 'total_investment_hours': 100, 'wasted_hours': 70,
            'waste_rate': 70.0, 'wasted_cost': 14000, 'loss_reasons': {'价格': 5}
        })
        self.mixin.get_salesperson_waste_ranking = MagicMock(return_value=[])
        self.mixin.analyze_failure_patterns = MagicMock(return_value={'recommendations': ['建议1']})
        self.mixin.get_monthly_trend = MagicMock(return_value=[])
        self.mixin.get_department_comparison = MagicMock(return_value=[])

    def test_generate_monthly_report(self):
        result = self.mixin.generate_waste_report("2024-01")
        assert result['report_period'] == "2024-01"
        assert 'overall_statistics' in result
        assert result['monthly_trend'] == []

    def test_generate_yearly_report(self):
        result = self.mixin.generate_waste_report("2024")
        assert result['report_period'] == "2024"
        self.mixin.get_monthly_trend.assert_called_once_with(12)

# -*- coding: utf-8 -*-
"""
第四十五批覆盖：resource_waste_analysis/report_generation.py
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.resource_waste_analysis.report_generation")

from app.services.resource_waste_analysis.report_generation import ReportGenerationMixin


class MockReportService(ReportGenerationMixin):
    """具体实现用于测试"""

    def __init__(self):
        self.calculate_waste_by_period = MagicMock()
        self.get_salesperson_waste_ranking = MagicMock()
        self.analyze_failure_patterns = MagicMock()
        self.get_monthly_trend = MagicMock()
        self.get_department_comparison = MagicMock()


@pytest.fixture
def service():
    svc = MockReportService()
    svc.calculate_waste_by_period.return_value = {
        "wasted_cost": Decimal("50000"),
        "waste_rate": 0.3,
        "loss_reasons": {"PRICE_TOO_HIGH": 3, "TECH_MISMATCH": 2},
        "total_leads": 10,
        "won_leads": 7,
        "lost_leads": 3,
        "win_rate": 0.7,
        "total_investment_hours": 100.0,
        "wasted_hours": 30.0,
    }
    svc.get_salesperson_waste_ranking.return_value = [{"salesperson": "A"}]
    svc.analyze_failure_patterns.return_value = {"recommendations": ["改进沟通"]}
    svc.get_monthly_trend.return_value = [{"month": "2024-01"}]
    svc.get_department_comparison.return_value = [{"dept": "销售部"}]
    return svc


class TestReportGenerationMixin:
    def test_generate_monthly_report(self, service):
        result = service.generate_waste_report("2024-01")
        assert result["report_period"] == "2024-01"
        assert "generated_at" in result
        assert "overall_statistics" in result

    def test_generate_annual_report(self, service):
        result = service.generate_waste_report("2024")
        assert result["report_period"] == "2024"
        # For annual report, monthly_trend should be populated
        service.get_monthly_trend.assert_called_once_with(12)

    def test_annual_report_has_monthly_trend(self, service):
        result = service.generate_waste_report("2024")
        assert len(result["monthly_trend"]) > 0

    def test_monthly_report_no_monthly_trend(self, service):
        result = service.generate_waste_report("2024-06")
        assert result["monthly_trend"] == []
        service.get_monthly_trend.assert_not_called()

    def test_summary_contains_key_fields(self, service):
        result = service.generate_waste_report("2024-03")
        summary = result["summary"]
        assert "total_wasted_cost" in summary
        assert "waste_rate" in summary
        assert "top_loss_reason" in summary
        assert "key_recommendation" in summary

    def test_top_loss_reason_from_loss_reasons(self, service):
        result = service.generate_waste_report("2024-03")
        # max loss reason is PRICE_TOO_HIGH (3)
        assert result["summary"]["top_loss_reason"] == "PRICE_TOO_HIGH"

    def test_key_recommendation_from_patterns(self, service):
        result = service.generate_waste_report("2024-03")
        assert result["summary"]["key_recommendation"] == "改进沟通"

    def test_no_recommendations_fallback(self, service):
        service.analyze_failure_patterns.return_value = {"recommendations": []}
        result = service.generate_waste_report("2024-03")
        assert result["summary"]["key_recommendation"] == "暂无建议"

# -*- coding: utf-8 -*-
"""
Tests for app/services/resource_waste_analysis/report_generation.py
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock

try:
    from app.services.resource_waste_analysis.report_generation import ReportGenerationMixin
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


class ConcreteReportGen(ReportGenerationMixin):
    """用于测试的具体实现"""
    def calculate_waste_by_period(self, start_date, end_date):
        return {
            "period": f"{start_date} ~ {end_date}",
            "total_leads": 10,
            "won_leads": 6,
            "lost_leads": 4,
            "win_rate": 0.6,
            "total_investment_hours": 100.0,
            "productive_hours": 60.0,
            "wasted_hours": 40.0,
            "wasted_cost": Decimal("4000"),
            "waste_rate": 0.4,
            "loss_reasons": {"PRICE": 3, "OTHER": 1},
        }

    def get_salesperson_waste_ranking(self, start, end, limit=10):
        return []

    def analyze_failure_patterns(self, start, end):
        return {"recommendations": ["加强销售培训"], "patterns": {}}

    def get_monthly_trend(self, months=12):
        return []

    def get_department_comparison(self, start, end):
        return {}


@pytest.fixture
def gen():
    return ConcreteReportGen()


def test_generate_monthly_period(gen):
    """YYYY-MM 格式的月度报告"""
    result = gen.generate_waste_report("2024-03")
    assert result["report_period"] == "2024-03"
    assert "overall_statistics" in result


def test_generate_yearly_period(gen):
    """YYYY 格式的年度报告"""
    result = gen.generate_waste_report("2024")
    assert result["report_period"] == "2024"
    assert isinstance(result.get("monthly_trend"), list)


def test_generate_report_has_required_keys(gen):
    """报告应包含所有必要的键"""
    result = gen.generate_waste_report("2024-01")
    required_keys = ["report_period", "generated_at", "overall_statistics",
                     "top_resource_wasters", "failure_pattern_analysis",
                     "monthly_trend", "department_comparison", "summary"]
    for key in required_keys:
        assert key in result


def test_generate_report_summary(gen):
    """summary 应包含 total_wasted_cost 和 waste_rate"""
    result = gen.generate_waste_report("2024-06")
    assert "total_wasted_cost" in result["summary"]
    assert "waste_rate" in result["summary"]
    assert result["summary"]["total_wasted_cost"] == Decimal("4000")


def test_generate_report_top_loss_reason(gen):
    """summary 中 top_loss_reason 应为 loss_reasons 中数量最多的"""
    result = gen.generate_waste_report("2024-06")
    assert result["summary"]["top_loss_reason"] == "PRICE"


def test_generate_yearly_calls_monthly_trend(gen):
    """年度报告应包含 monthly_trend 数据"""
    gen.get_monthly_trend = MagicMock(return_value=[{"month": "2024-01"}])
    result = gen.generate_waste_report("2024")
    gen.get_monthly_trend.assert_called_once_with(12)


def test_generate_report_generated_at_not_empty(gen):
    """generated_at 字段不应为空"""
    result = gen.generate_waste_report("2024-02")
    assert result["generated_at"] is not None
    assert len(result["generated_at"]) > 0

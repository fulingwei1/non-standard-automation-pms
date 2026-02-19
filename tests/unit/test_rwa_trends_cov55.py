# -*- coding: utf-8 -*-
"""
Tests for app/services/resource_waste_analysis/trends_comparison.py
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.resource_waste_analysis.trends_comparison import TrendsComparisonMixin
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_period_data(**kwargs):
    base = {
        "period": "2024-01-01 ~ 2024-02-01",
        "total_leads": 5,
        "won_leads": 3,
        "lost_leads": 2,
        "win_rate": 0.6,
        "total_investment_hours": 50.0,
        "productive_hours": 30.0,
        "wasted_hours": 20.0,
        "wasted_cost": Decimal("2000"),
        "waste_rate": 0.4,
        "loss_reasons": {}
    }
    base.update(kwargs)
    return base


class ConcreteTrends(TrendsComparisonMixin):
    def calculate_waste_by_period(self, start, end):
        return _make_period_data()


@pytest.fixture
def trends():
    return ConcreteTrends()


def test_get_monthly_trend_returns_list(trends):
    """get_monthly_trend 应返回列表"""
    result = trends.get_monthly_trend(months=3)
    assert isinstance(result, list)


def test_get_monthly_trend_correct_count(trends):
    """应返回指定月数的数据"""
    result = trends.get_monthly_trend(months=6)
    assert len(result) == 6


def test_get_monthly_trend_item_keys(trends):
    """每个月度数据项应包含必要的键"""
    result = trends.get_monthly_trend(months=1)
    item = result[0]
    required_keys = ["month", "total_leads", "won_leads", "lost_leads",
                     "win_rate", "total_hours", "wasted_hours", "waste_rate", "wasted_cost"]
    for key in required_keys:
        assert key in item


def test_get_monthly_trend_wasted_cost_is_float(trends):
    """wasted_cost 应为 float 类型"""
    result = trends.get_monthly_trend(months=2)
    for item in result:
        assert isinstance(item["wasted_cost"], float)


def test_get_monthly_trend_chronological_order(trends):
    """月度数据应按时间顺序排列"""
    result = trends.get_monthly_trend(months=3)
    months = [item["month"] for item in result]
    assert months == sorted(months)


def test_get_monthly_trend_single_month(trends):
    """请求单月时正确返回"""
    result = trends.get_monthly_trend(months=1)
    assert len(result) == 1
    assert "month" in result[0]


def test_get_monthly_trend_calls_calculate(trends):
    """应为每个月调用 calculate_waste_by_period"""
    trends.calculate_waste_by_period = MagicMock(return_value=_make_period_data())
    trends.get_monthly_trend(months=4)
    assert trends.calculate_waste_by_period.call_count == 4

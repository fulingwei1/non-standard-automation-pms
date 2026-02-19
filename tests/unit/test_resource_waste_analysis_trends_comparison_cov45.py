# -*- coding: utf-8 -*-
"""
第四十五批覆盖：resource_waste_analysis/trends_comparison.py
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

pytest.importorskip("app.services.resource_waste_analysis.trends_comparison")

from app.services.resource_waste_analysis.trends_comparison import TrendsComparisonMixin


def _make_month_data(month_offset=0):
    return {
        "total_leads": 10,
        "won_leads": 7,
        "lost_leads": 3,
        "win_rate": 0.7,
        "total_investment_hours": 100.0,
        "wasted_hours": 30.0,
        "waste_rate": 0.3,
        "wasted_cost": Decimal("5000"),
    }


class MockTrendsService(TrendsComparisonMixin):
    def __init__(self):
        self.calculate_waste_by_period = MagicMock(side_effect=lambda s, e: _make_month_data())


@pytest.fixture
def service():
    return MockTrendsService()


class TestTrendsComparisonMixin:
    def test_get_monthly_trend_default_12_months(self, service):
        result = service.get_monthly_trend()
        assert len(result) == 12

    def test_get_monthly_trend_custom_months(self, service):
        result = service.get_monthly_trend(months=6)
        assert len(result) == 6

    def test_monthly_trend_item_structure(self, service):
        result = service.get_monthly_trend(months=3)
        for item in result:
            assert "month" in item
            assert "total_leads" in item
            assert "won_leads" in item
            assert "lost_leads" in item
            assert "win_rate" in item
            assert "total_hours" in item
            assert "wasted_hours" in item
            assert "waste_rate" in item
            assert "wasted_cost" in item

    def test_monthly_trend_month_format(self, service):
        result = service.get_monthly_trend(months=1)
        assert len(result[0]["month"]) == 7  # YYYY-MM

    def test_wasted_cost_is_float(self, service):
        result = service.get_monthly_trend(months=1)
        assert isinstance(result[0]["wasted_cost"], float)

    def test_calculate_called_once_per_month(self, service):
        service.get_monthly_trend(months=4)
        assert service.calculate_waste_by_period.call_count == 4

    def test_months_in_chronological_order(self, service):
        result = service.get_monthly_trend(months=3)
        months = [r["month"] for r in result]
        assert months == sorted(months)

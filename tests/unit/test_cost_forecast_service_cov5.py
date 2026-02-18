# -*- coding: utf-8 -*-
"""第五批：cost_forecast_service.py 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

try:
    from app.services.cost_forecast_service import CostForecastService
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="cost_forecast_service not importable")


def make_service(db=None):
    if db is None:
        db = MagicMock()
    return CostForecastService(db)


def make_project(project_id=1, name="Test Project", budget=Decimal("100000")):
    p = MagicMock()
    p.id = project_id
    p.project_name = name
    p.budget = budget
    p.start_date = date(2024, 1, 1)
    p.end_date = date(2024, 12, 31)
    return p


class TestLinearForecast:
    def test_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.linear_forecast(999)
        assert "error" in result

    def test_insufficient_data(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = make_project()
        svc = make_service(db)
        # Mock _get_monthly_costs to return only 1 item
        with patch.object(svc, "_get_monthly_costs", return_value=[
            {"month": "2024-01", "monthly_cost": Decimal("5000"), "cumulative_cost": Decimal("5000")}
        ]):
            result = svc.linear_forecast(1)
            assert "error" in result


class TestHistoricalAverageForecast:
    def test_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.historical_average_forecast(999)
        assert "error" in result

    def test_no_historical_data(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = make_project()
        svc = make_service(db)
        with patch.object(svc, "_get_monthly_costs", return_value=[]):
            result = svc.historical_average_forecast(1)
            assert "error" in result


class TestGetCostTrend:
    def test_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.get_cost_trend(999)
        assert "error" in result

    def test_empty_monthly_costs(self):
        db = MagicMock()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = make_service(db)
        with patch.object(svc, "_get_monthly_costs", return_value=[]):
            result = svc.get_cost_trend(1)
            assert result["monthly_trend"] == []
            assert result["summary"]["total_months"] == 0

    def test_with_data(self):
        db = MagicMock()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = make_service(db)
        monthly = [
            {"month": "2024-01", "monthly_cost": Decimal("5000"), "cumulative_cost": Decimal("5000")},
            {"month": "2024-02", "monthly_cost": Decimal("6000"), "cumulative_cost": Decimal("11000")},
        ]
        with patch.object(svc, "_get_monthly_costs", return_value=monthly):
            result = svc.get_cost_trend(1)
            assert result["summary"]["total_months"] == 2
            assert result["summary"]["total_cost"] == 11000.0


class TestExponentialForecast:
    def test_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.exponential_forecast(999)
        assert "error" in result


class TestCheckCostAlerts:
    def test_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.check_cost_alerts(999)
        assert isinstance(result, (dict, list))

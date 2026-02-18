# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - cost_forecast_service"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date, datetime
from decimal import Decimal

pytest.importorskip("app.services.cost_forecast_service")

from app.services.cost_forecast_service import CostForecastService


def make_db():
    return MagicMock()


def make_project(**kw):
    p = MagicMock()
    p.id = kw.get("id", 1)
    p.project_name = kw.get("project_name", "TestProject")
    p.project_code = kw.get("project_code", "TP-001")
    p.budget_amount = kw.get("budget_amount", Decimal("100000"))
    p.actual_cost = kw.get("actual_cost", Decimal("60000"))
    p.progress_pct = kw.get("progress_pct", 50.0)
    p.planned_start_date = kw.get("planned_start_date", None)
    p.planned_end_date = kw.get("planned_end_date", None)
    return p


class TestCostForecastServiceProjectNotFound:
    def test_linear_forecast_project_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.linear_forecast(999)
        assert result.get("error") == "项目不存在"

    def test_exponential_forecast_project_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.exponential_forecast(999)
        assert "error" in result

    def test_historical_average_project_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.historical_average_forecast(999)
        assert "error" in result


class TestGetCostTrend:
    def test_project_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.get_cost_trend(999)
        assert "error" in result

    def test_empty_monthly_costs(self):
        db = make_db()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        with patch.object(svc, "_get_monthly_costs", return_value=[]):
            result = svc.get_cost_trend(1)
        assert result["summary"]["total_months"] == 0

    def test_with_monthly_costs(self):
        db = make_db()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        monthly_costs = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 12000, "cumulative_cost": 22000},
        ]
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.get_cost_trend(1)
        assert result["summary"]["total_months"] == 2
        assert result["summary"]["total_cost"] == 22000


class TestGetBurnDownData:
    def test_project_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.get_burn_down_data(999)
        assert "error" in result

    def test_no_budget(self):
        db = make_db()
        project = make_project(budget_amount=Decimal("0"))
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        result = svc.get_burn_down_data(1)
        assert "error" in result

    def test_with_budget(self):
        db = make_db()
        project = make_project(budget_amount=Decimal("100000"), actual_cost=Decimal("40000"), progress_pct=40.0)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        monthly_costs = [
            {"month": "2024-01", "monthly_cost": 20000, "cumulative_cost": 20000},
            {"month": "2024-02", "monthly_cost": 20000, "cumulative_cost": 40000},
        ]
        with patch.object(svc, "_get_monthly_costs", return_value=monthly_costs):
            result = svc.get_burn_down_data(1)
        assert result["budget"] == 100000.0
        assert "burn_down_data" in result


class TestCheckCostAlerts:
    def test_project_not_found_returns_empty(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.check_cost_alerts(999)
        assert result == []

    def test_overspend_alert_triggered(self):
        db = make_db()
        project = make_project(budget_amount=Decimal("100000"), actual_cost=Decimal("90000"), progress_pct=50.0)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        rules = {
            "OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100},
            "PROGRESS_MISMATCH": {"deviation_threshold": 15},
            "TREND_ANOMALY": {"growth_rate_threshold": 0.3},
        }
        with patch.object(svc, "_get_alert_rules", return_value=rules), \
             patch.object(svc, "_get_monthly_costs", return_value=[]), \
             patch.object(svc, "_create_alert_record"):
            alerts = svc.check_cost_alerts(1, auto_create=False)
        assert any(a["alert_type"] == "OVERSPEND" for a in alerts)

    def test_no_alerts_when_within_budget(self):
        db = make_db()
        project = make_project(budget_amount=Decimal("100000"), actual_cost=Decimal("30000"), progress_pct=30.0)
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        rules = {
            "OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100},
            "PROGRESS_MISMATCH": {"deviation_threshold": 15},
            "TREND_ANOMALY": {"growth_rate_threshold": 0.3},
        }
        with patch.object(svc, "_get_alert_rules", return_value=rules), \
             patch.object(svc, "_get_monthly_costs", return_value=[]):
            alerts = svc.check_cost_alerts(1, auto_create=False)
        assert len(alerts) == 0


class TestSaveForecast:
    def test_project_not_found_raises(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        with pytest.raises(ValueError, match="项目不存在"):
            svc.save_forecast(999, {}, 1)

    def test_saves_forecast(self):
        db = make_db()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)

        forecast_result = {
            "method": "LINEAR",
            "forecast_date": date.today(),
            "forecasted_completion_cost": 120000.0,
            "current_progress_pct": 50.0,
            "current_actual_cost": 60000.0,
            "current_budget": 100000.0,
            "monthly_forecast_data": [],
            "trend_data": {},
        }
        with patch("app.services.cost_forecast_service.save_obj"):
            result = svc.save_forecast(1, forecast_result, 1)
        assert result is not None


class TestHistoricalAverageForecastInsufficientData:
    def test_insufficient_data(self):
        db = make_db()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        with patch.object(svc, "_get_monthly_costs", return_value=[]):
            result = svc.historical_average_forecast(1)
        assert "error" in result

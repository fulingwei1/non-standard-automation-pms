# -*- coding: utf-8 -*-
"""成本预测服务单元测试 (CostForecastService)"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock


def _make_db():
    return MagicMock()


def _make_project(**kw):
    p = MagicMock()
    defaults = dict(
        id=1,
        project_name="比亚迪ADAS ICT测试系统",
        project_code="BYD-2024-001",
        progress_pct=Decimal("0.5"),
        budget_amount=Decimal("500000"),
        actual_cost=Decimal("200000"),
        planned_start_date=date(2024, 1, 1),
        planned_end_date=date(2024, 12, 31),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


class TestCostForecastServiceInit:
    def test_init_sets_db(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        svc = CostForecastService(db)
        assert svc.db is db


class TestLinearForecast:
    def test_project_not_found_returns_error(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.linear_forecast(project_id=999)
        assert "error" in result
        assert "项目不存在" in result["error"]

    def test_insufficient_data_returns_error(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        # Patch _get_monthly_costs to return empty list
        svc._get_monthly_costs = MagicMock(return_value=[])
        result = svc.linear_forecast(project_id=1)
        assert "error" in result

    def test_linear_forecast_with_enough_data(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 50000, "cumulative_cost": 50000},
            {"month": "2024-02", "monthly_cost": 60000, "cumulative_cost": 110000},
            {"month": "2024-03", "monthly_cost": 55000, "cumulative_cost": 165000},
        ]
        svc._get_monthly_costs = MagicMock(return_value=monthly_data)
        result = svc.linear_forecast(project_id=1)
        # Should return a result dict without "error"
        assert "error" not in result
        assert "forecasted_completion_cost" in result
        assert result["method"] == "LINEAR"


class TestGetCostTrend:
    def test_project_not_found(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.get_cost_trend(project_id=999)
        assert "error" in result

    def test_no_monthly_data_returns_empty_trend(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        svc._get_monthly_costs = MagicMock(return_value=[])
        result = svc.get_cost_trend(project_id=1)
        assert result["monthly_trend"] == []
        assert result["cumulative_trend"] == []
        assert result["summary"]["total_months"] == 0

    def test_with_monthly_data_returns_summary(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 50000, "cumulative_cost": 50000},
            {"month": "2024-02", "monthly_cost": 60000, "cumulative_cost": 110000},
        ]
        svc._get_monthly_costs = MagicMock(return_value=monthly_data)
        result = svc.get_cost_trend(project_id=1)
        assert len(result["monthly_trend"]) == 2
        assert result["summary"]["total_months"] == 2
        assert result["summary"]["total_cost"] == 110000.0


class TestCheckCostAlerts:
    def test_project_not_found_returns_empty_list(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = CostForecastService(db)
        result = svc.check_cost_alerts(project_id=999)
        assert result == []

    def test_no_alerts_for_healthy_project(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        project = _make_project(actual_cost=Decimal("100000"), budget_amount=Decimal("500000"))
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        svc._get_alert_rules = MagicMock(return_value={
            "overspend_threshold": 0.9,
            "progress_mismatch_threshold": 0.2,
            "trend_anomaly_threshold": 0.3,
        })
        svc._check_overspend_alert = MagicMock(return_value=None)
        svc._check_progress_mismatch_alert = MagicMock(return_value=None)
        svc._check_trend_anomaly_alert = MagicMock(return_value=None)
        result = svc.check_cost_alerts(project_id=1, auto_create=False)
        assert result == []

    def test_overspend_alert_triggered(self):
        from app.services.cost_forecast_service import CostForecastService
        db = _make_db()
        project = _make_project(actual_cost=Decimal("490000"), budget_amount=Decimal("500000"))
        db.query.return_value.filter.return_value.first.return_value = project
        svc = CostForecastService(db)
        svc._get_alert_rules = MagicMock(return_value={})
        alert = {"alert_type": "OVERSPEND", "message": "成本超支预警"}
        svc._check_overspend_alert = MagicMock(return_value=alert)
        svc._check_progress_mismatch_alert = MagicMock(return_value=None)
        svc._check_trend_anomaly_alert = MagicMock(return_value=None)
        result = svc.check_cost_alerts(project_id=1, auto_create=False)
        assert len(result) == 1
        assert result[0]["alert_type"] == "OVERSPEND"

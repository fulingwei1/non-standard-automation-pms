# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 成本预测服务"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.services.cost.cost_forecast_service import CostForecastService


class FakeQuery:
    def __init__(self, *, first_value=None, all_value=None):
        self.first_value = first_value
        self.all_value = all_value if all_value is not None else []

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.first_value

    def all(self):
        return self.all_value


class TestCostForecastServiceBusinessLogic:
    """成本预测服务业务逻辑测试"""

    def test_simple_linear_regression_empty_input(self):
        service = CostForecastService(Mock())

        result = service._simple_linear_regression([], [])

        assert result == {"slope": 0.0, "intercept": 0.0, "r_squared": 0.0}

    def test_simple_linear_regression_with_constant_x(self):
        service = CostForecastService(Mock())

        result = service._simple_linear_regression([1, 1, 1], [10, 20, 30])

        assert result["slope"] == 0.0
        assert result["intercept"] == pytest.approx(20.0)
        assert 0.0 <= result["r_squared"] <= 1.0

    def test_linear_forecast_returns_error_when_project_missing(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)
        service = CostForecastService(db)

        result = service.linear_forecast(999)

        assert result == {"error": "项目不存在"}

    def test_linear_forecast_returns_error_when_monthly_data_insufficient(self):
        project = SimpleNamespace(
            id=1,
            planned_start_date=None,
            planned_end_date=None,
            progress_pct=0,
            actual_cost=0,
            budget_amount=0,
        )
        db = Mock()
        db.query.return_value = FakeQuery(first_value=project)
        service = CostForecastService(db)
        service._get_monthly_costs = Mock(
            return_value=[{"month": "2026-01", "monthly_cost": 100.0, "cumulative_cost": 100.0}]
        )

        result = service.linear_forecast(1)

        assert result["error"] == "历史数据不足（至少需要2个月数据）"
        assert result["data_points"] == 1

    def test_linear_forecast_generates_forecast_without_sklearn(self):
        project = SimpleNamespace(
            id=1,
            planned_start_date=date(2026, 1, 1),
            planned_end_date=date(2026, 4, 1),
            progress_pct=50,
            actual_cost=250.0,
            budget_amount=350.0,
        )
        db = Mock()
        db.query.return_value = FakeQuery(first_value=project)
        service = CostForecastService(db)
        service._get_monthly_costs = Mock(
            return_value=[
                {"month": "2026-01", "monthly_cost": 100.0, "cumulative_cost": 100.0},
                {"month": "2026-02", "monthly_cost": 150.0, "cumulative_cost": 250.0},
            ]
        )

        result = service.linear_forecast(1)

        assert result["method"] == "LINEAR"
        assert result["data_points"] == 2
        assert result["forecasted_completion_cost"] > 0
        assert result["trend_data"]["slope"] == pytest.approx(150.0)
        assert result["trend_data"]["intercept"] == pytest.approx(-50.0)
        assert result["trend_data"]["r_squared"] == pytest.approx(1.0)
        assert any(item["type"] == "forecast" for item in result["monthly_forecast_data"])
        assert result["is_over_budget"] is True

    def test_exponential_forecast_returns_error_for_insufficient_data(self):
        project = SimpleNamespace(progress_pct=20, actual_cost=50, budget_amount=100)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=project)
        service = CostForecastService(db)
        service._get_monthly_costs = Mock(return_value=[{"month": "2026-01", "monthly_cost": 100, "cumulative_cost": 100}])

        result = service.exponential_forecast(1)

        assert result == {"error": "历史数据不足（至少需要2个月数据）"}

    def test_historical_average_forecast_builds_actual_and_forecast_rows(self):
        project = SimpleNamespace(progress_pct=50, actual_cost=250, budget_amount=300)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=project)
        service = CostForecastService(db)
        service._get_monthly_costs = Mock(
            return_value=[
                {"month": "2026-01", "monthly_cost": 100, "cumulative_cost": 100},
                {"month": "2026-02", "monthly_cost": 150, "cumulative_cost": 250},
            ]
        )

        result = service.historical_average_forecast(1)

        assert result["method"] == "HISTORICAL_AVERAGE"
        assert result["trend_data"]["avg_monthly_cost"] == pytest.approx(125.0)
        assert len(result["monthly_forecast_data"]) == 4
        assert result["monthly_forecast_data"][-1]["type"] == "forecast"
        assert result["is_over_budget"] is True

    def test_get_cost_trend_returns_empty_summary_when_no_monthly_costs(self):
        project = SimpleNamespace(project_name="测试项目")
        db = Mock()
        db.query.return_value = FakeQuery(first_value=project)
        service = CostForecastService(db)
        service._get_monthly_costs = Mock(return_value=[])

        result = service.get_cost_trend(1)

        assert result["project_name"] == "测试项目"
        assert result["monthly_trend"] == []
        assert result["summary"]["total_months"] == 0

    def test_get_burn_down_data_returns_budget_error_when_missing_budget(self):
        project = SimpleNamespace(project_name="测试项目", budget_amount=0)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=project)
        service = CostForecastService(db)

        result = service.get_burn_down_data(1)

        assert result == {"error": "项目预算未设置"}

    def test_check_cost_alerts_aggregates_and_creates_records(self):
        project = SimpleNamespace(id=1)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=project)
        service = CostForecastService(db)
        service._get_alert_rules = Mock(return_value={})
        service._check_overspend_alert = Mock(return_value={"alert_type": "OVERSPEND"})
        service._check_progress_mismatch_alert = Mock(return_value={"alert_type": "PROGRESS_MISMATCH"})
        service._check_trend_anomaly_alert = Mock(return_value={"alert_type": "TREND_ANOMALY"})
        service._create_alert_record = Mock()

        result = service.check_cost_alerts(1, auto_create=True)

        assert [item["alert_type"] for item in result] == [
            "OVERSPEND",
            "PROGRESS_MISMATCH",
            "TREND_ANOMALY",
        ]
        assert service._create_alert_record.call_count == 3

    def test_check_progress_mismatch_alert_returns_info_when_progress_ahead(self):
        service = CostForecastService(Mock())
        project = SimpleNamespace(budget_amount=100, progress_pct=80, actual_cost=40)

        alert = service._check_progress_mismatch_alert(
            project, {"PROGRESS_MISMATCH": {"deviation_threshold": 15}}
        )

        assert alert["alert_level"] == "INFO"
        assert alert["alert_type"] == "PROGRESS_MISMATCH"
        assert alert["alert_data"]["deviation"] == pytest.approx(-40.0)

    def test_check_trend_anomaly_alert_returns_warning(self):
        service = CostForecastService(Mock())
        service._get_monthly_costs = Mock(
            return_value=[
                {"month": "2026-01", "monthly_cost": 100},
                {"month": "2026-02", "monthly_cost": 150},
                {"month": "2026-03", "monthly_cost": 250},
            ]
        )

        alert = service._check_trend_anomaly_alert(
            1, SimpleNamespace(), {"TREND_ANOMALY": {"growth_rate_threshold": 0.3}}
        )

        assert alert["alert_type"] == "TREND_ANOMALY"
        assert alert["alert_level"] == "WARNING"
        assert alert["alert_data"]["recent_months"] == ["2026-01", "2026-02", "2026-03"]

    def test_save_forecast_raises_when_project_missing(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)
        service = CostForecastService(db)

        with pytest.raises(ValueError, match="项目不存在"):
            service.save_forecast(1, {"method": "LINEAR", "forecast_date": date.today()}, created_by=1)

    def test_save_forecast_calls_save_obj(self):
        project = SimpleNamespace(project_code="P001", project_name="测试项目")
        db = Mock()
        db.query.return_value = FakeQuery(first_value=project)
        service = CostForecastService(db)
        forecast_result = {
            "method": "LINEAR",
            "forecast_date": date(2026, 4, 12),
            "forecasted_completion_cost": 123.45,
            "current_progress_pct": 50,
            "current_actual_cost": 100,
            "current_budget": 120,
            "monthly_forecast_data": [{"month": "2026-04"}],
            "trend_data": {"slope": 10},
        }

        with patch("app.services.cost.cost_forecast_service.save_obj") as mock_save_obj:
            forecast = service.save_forecast(1, forecast_result, created_by=7)

        mock_save_obj.assert_called_once()
        assert forecast.project_id == 1
        assert forecast.project_code == "P001"
        assert forecast.created_by == 7

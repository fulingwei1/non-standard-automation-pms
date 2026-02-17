# -*- coding: utf-8 -*-
"""
CostForecastService 单元测试

覆盖：
- linear_forecast (线性回归预测)
- exponential_forecast (指数预测)
- historical_average_forecast (历史平均法)
- get_cost_trend (成本趋势)
- get_burn_down_data (燃尽图)
- check_cost_alerts (预警检测)
- _check_overspend_alert
- _check_progress_mismatch_alert
- _check_trend_anomaly_alert
- save_forecast
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.cost_forecast_service import CostForecastService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return CostForecastService(db)


def _make_project(
    id=1,
    project_name="测试项目",
    project_code="P001",
    budget_amount=100000,
    actual_cost=50000,
    progress_pct=50,
    planned_start_date=None,
    planned_end_date=None,
):
    p = MagicMock()
    p.id = id
    p.project_name = project_name
    p.project_code = project_code
    p.budget_amount = Decimal(str(budget_amount))
    p.actual_cost = Decimal(str(actual_cost))
    p.progress_pct = Decimal(str(progress_pct))
    p.planned_start_date = planned_start_date
    p.planned_end_date = planned_end_date
    return p


# ---------------------------------------------------------------------------
# Tests: linear_forecast
# ---------------------------------------------------------------------------

class TestLinearForecast:
    def test_project_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.linear_forecast(project_id=99)
        assert "error" in result
        assert "项目不存在" in result["error"]

    def test_insufficient_data(self, service, db):
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        # _get_monthly_costs returns only 1 item → insufficient
        with patch.object(service, "_get_monthly_costs", return_value=[
            {"month": "2024-01", "monthly_cost": 1000, "cumulative_cost": 1000}
        ]):
            result = service.linear_forecast(project_id=1)
        assert "error" in result
        assert "历史数据不足" in result["error"]

    def _run_with_sklearn_mock(self, service, db, project, monthly_data, slope=10000.0):
        """Helper: run linear_forecast with properly mocked sklearn."""
        import sys
        mock_model = MagicMock()
        mock_model.coef_ = [slope]          # 1-D array-like
        mock_model.intercept_ = 0.0
        mock_model.score.return_value = 0.95
        mock_lr_class = MagicMock(return_value=mock_model)
        mock_lr_module = MagicMock()
        mock_lr_module.LinearRegression = mock_lr_class
        db.query.return_value.filter.return_value.first.return_value = project
        with patch.dict(sys.modules, {
            "sklearn": MagicMock(),
            "sklearn.linear_model": mock_lr_module,
        }):
            with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
                return service.linear_forecast(project_id=1)

    def test_linear_forecast_success(self, service, db):
        project = _make_project(budget_amount=100000, actual_cost=30000, progress_pct=30)
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 11000, "cumulative_cost": 21000},
            {"month": "2024-03", "monthly_cost": 9000,  "cumulative_cost": 30000},
        ]
        result = self._run_with_sklearn_mock(service, db, project, monthly_data)
        assert result["method"] == "LINEAR"
        assert "forecasted_completion_cost" in result
        assert "monthly_forecast_data" in result
        assert result["data_points"] == 3

    def test_is_over_budget_flag(self, service, db):
        """当预测完工成本 > 预算时 is_over_budget 为 True"""
        project = _make_project(budget_amount=10000, actual_cost=8000, progress_pct=50)
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 4000, "cumulative_cost": 4000},
            {"month": "2024-02", "monthly_cost": 4000, "cumulative_cost": 8000},
            {"month": "2024-03", "monthly_cost": 5000, "cumulative_cost": 13000},
        ]
        result = self._run_with_sklearn_mock(service, db, project, monthly_data, slope=5000.0)
        assert "is_over_budget" in result

    def test_forecast_with_planned_dates(self, service, db):
        """使用计划日期计算总月数"""
        from datetime import date as ddate
        project = _make_project(
            budget_amount=120000,
            actual_cost=40000,
            progress_pct=40,
            planned_start_date=ddate(2024, 1, 1),
            planned_end_date=ddate(2024, 12, 31),
        )
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 30000},
            {"month": "2024-04", "monthly_cost": 10000, "cumulative_cost": 40000},
        ]
        result = self._run_with_sklearn_mock(service, db, project, monthly_data, slope=10000.0)
        assert result["method"] == "LINEAR"
        assert result["current_budget"] == 120000.0


# ---------------------------------------------------------------------------
# Tests: exponential_forecast
# ---------------------------------------------------------------------------

class TestExponentialForecast:
    def test_project_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.exponential_forecast(project_id=99)
        assert "error" in result

    def test_insufficient_data(self, service, db):
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        with patch.object(service, "_get_monthly_costs", return_value=[
            {"month": "2024-01", "monthly_cost": 5000, "cumulative_cost": 5000}
        ]):
            result = service.exponential_forecast(project_id=1)
        assert "error" in result

    def test_exponential_forecast_success(self, service, db):
        project = _make_project(budget_amount=200000, actual_cost=40000, progress_pct=25)
        db.query.return_value.filter.return_value.first.return_value = project
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 12000, "cumulative_cost": 22000},
            {"month": "2024-03", "monthly_cost": 14400, "cumulative_cost": 36400},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.exponential_forecast(project_id=1)
        assert result["method"] == "EXPONENTIAL"
        assert "forecasted_completion_cost" in result
        assert result["data_points"] == 3

    def test_avg_growth_rate_positive(self, service, db):
        """累计成本增长 → avg_growth_rate > 0"""
        project = _make_project(budget_amount=100000, actual_cost=30000, progress_pct=30)
        db.query.return_value.filter.return_value.first.return_value = project
        # cumulative: 10000→20000→30000, growth rates = 1.0, 0.5, avg=0.75
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 30000},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.exponential_forecast(project_id=1)
        assert result["trend_data"]["avg_growth_rate"] > 0


# ---------------------------------------------------------------------------
# Tests: historical_average_forecast
# ---------------------------------------------------------------------------

class TestHistoricalAverageForecast:
    def test_project_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.historical_average_forecast(project_id=99)
        assert "error" in result

    def test_no_data(self, service, db):
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        with patch.object(service, "_get_monthly_costs", return_value=[]):
            result = service.historical_average_forecast(project_id=1)
        assert "error" in result

    def test_success_with_progress(self, service, db):
        project = _make_project(budget_amount=120000, actual_cost=60000, progress_pct=50)
        db.query.return_value.filter.return_value.first.return_value = project
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 30000},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.historical_average_forecast(project_id=1)
        assert result["method"] == "HISTORICAL_AVERAGE"
        assert result["trend_data"]["avg_monthly_cost"] == 10000.0

    def test_avg_monthly_cost_calculation(self, service, db):
        project = _make_project(budget_amount=100000, actual_cost=40000, progress_pct=40)
        db.query.return_value.filter.return_value.first.return_value = project
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 8000,  "cumulative_cost": 8000},
            {"month": "2024-02", "monthly_cost": 12000, "cumulative_cost": 20000},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.historical_average_forecast(project_id=1)
        # avg = (8000+12000)/2 = 10000
        assert result["trend_data"]["avg_monthly_cost"] == 10000.0

    def test_budget_variance_negative_when_under_budget(self, service, db):
        """预测完工成本 < 预算 → variance 为负"""
        project = _make_project(budget_amount=500000, actual_cost=10000, progress_pct=50)
        db.query.return_value.filter.return_value.first.return_value = project
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 5000, "cumulative_cost": 5000},
            {"month": "2024-02", "monthly_cost": 5000, "cumulative_cost": 10000},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.historical_average_forecast(project_id=1)
        assert result["is_over_budget"] is False
        assert result["budget_variance"] < 0


# ---------------------------------------------------------------------------
# Tests: get_cost_trend
# ---------------------------------------------------------------------------

class TestGetCostTrend:
    def test_project_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.get_cost_trend(project_id=99)
        assert "error" in result

    def test_empty_monthly_costs(self, service, db):
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        with patch.object(service, "_get_monthly_costs", return_value=[]):
            result = service.get_cost_trend(project_id=1)
        assert result["summary"]["total_months"] == 0

    def test_summary_statistics(self, service, db):
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 5000,  "cumulative_cost": 5000},
            {"month": "2024-02", "monthly_cost": 15000, "cumulative_cost": 20000},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.get_cost_trend(project_id=1)
        assert result["summary"]["total_months"] == 2
        assert result["summary"]["total_cost"] == 20000.0
        assert result["summary"]["avg_monthly_cost"] == 10000.0
        assert result["summary"]["min_monthly_cost"] == 5000.0
        assert result["summary"]["max_monthly_cost"] == 15000.0


# ---------------------------------------------------------------------------
# Tests: get_burn_down_data
# ---------------------------------------------------------------------------

class TestGetBurnDownData:
    def test_project_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.get_burn_down_data(project_id=99)
        assert "error" in result

    def test_no_budget(self, service, db):
        project = _make_project(budget_amount=0)
        db.query.return_value.filter.return_value.first.return_value = project
        with patch.object(service, "_get_monthly_costs", return_value=[]):
            result = service.get_burn_down_data(project_id=1)
        assert "error" in result

    def test_burn_down_basic(self, service, db):
        from datetime import date as ddate
        project = _make_project(
            budget_amount=120000,
            actual_cost=30000,
            progress_pct=25,
            planned_start_date=ddate(2024, 1, 1),
            planned_end_date=ddate(2024, 12, 31),
        )
        db.query.return_value.filter.return_value.first.return_value = project
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10000, "cumulative_cost": 20000},
            {"month": "2024-03", "monthly_cost": 10000, "cumulative_cost": 30000},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service.get_burn_down_data(project_id=1)
        assert result["budget"] == 120000.0
        assert result["current_spent"] == 30000.0
        assert "burn_down_data" in result


# ---------------------------------------------------------------------------
# Tests: _check_overspend_alert
# ---------------------------------------------------------------------------

class TestCheckOverspendAlert:
    def test_no_budget(self, service):
        project = _make_project(budget_amount=0)
        result = service._check_overspend_alert(project, {})
        assert result is None

    def test_below_threshold(self, service):
        project = _make_project(budget_amount=100000, actual_cost=70000)
        rules = {"OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}}
        result = service._check_overspend_alert(project, rules)
        assert result is None

    def test_warning_level(self, service):
        project = _make_project(budget_amount=100000, actual_cost=85000)
        rules = {"OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}}
        result = service._check_overspend_alert(project, rules)
        assert result is not None
        assert result["alert_level"] == "WARNING"
        assert result["alert_type"] == "OVERSPEND"

    def test_critical_level(self, service):
        project = _make_project(budget_amount=100000, actual_cost=110000)
        rules = {"OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100}}
        result = service._check_overspend_alert(project, rules)
        assert result is not None
        assert result["alert_level"] == "CRITICAL"

    def test_default_rules(self, service):
        """空规则时使用默认阈值"""
        project = _make_project(budget_amount=100000, actual_cost=95000)
        result = service._check_overspend_alert(project, {})
        assert result is not None
        assert result["alert_level"] == "WARNING"


# ---------------------------------------------------------------------------
# Tests: _check_progress_mismatch_alert
# ---------------------------------------------------------------------------

class TestCheckProgressMismatchAlert:
    def test_no_budget(self, service):
        project = _make_project(budget_amount=0)
        result = service._check_progress_mismatch_alert(project, {})
        assert result is None

    def test_within_threshold(self, service):
        # progress=50%, cost=55% → deviation=5% < 15%
        project = _make_project(budget_amount=100000, actual_cost=55000, progress_pct=50)
        rules = {"PROGRESS_MISMATCH": {"deviation_threshold": 15}}
        result = service._check_progress_mismatch_alert(project, rules)
        assert result is None

    def test_cost_ahead_of_progress(self, service):
        # cost=80%, progress=50% → deviation=30% > 15%
        project = _make_project(budget_amount=100000, actual_cost=80000, progress_pct=50)
        rules = {"PROGRESS_MISMATCH": {"deviation_threshold": 15}}
        result = service._check_progress_mismatch_alert(project, rules)
        assert result is not None
        assert result["alert_level"] == "WARNING"

    def test_progress_ahead_of_cost(self, service):
        # cost=20%, progress=60% → deviation=-40% → abs > 15%
        project = _make_project(budget_amount=100000, actual_cost=20000, progress_pct=60)
        rules = {"PROGRESS_MISMATCH": {"deviation_threshold": 15}}
        result = service._check_progress_mismatch_alert(project, rules)
        assert result is not None
        assert result["alert_level"] == "INFO"


# ---------------------------------------------------------------------------
# Tests: _check_trend_anomaly_alert
# ---------------------------------------------------------------------------

class TestCheckTrendAnomalyAlert:
    def test_insufficient_data(self, service, db):
        project = _make_project()
        with patch.object(service, "_get_monthly_costs", return_value=[
            {"month": "2024-01", "monthly_cost": 5000, "cumulative_cost": 5000},
            {"month": "2024-02", "monthly_cost": 5000, "cumulative_cost": 10000},
        ]):
            result = service._check_trend_anomaly_alert(1, project, {})
        assert result is None

    def test_normal_growth(self, service, db):
        project = _make_project()
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 10200, "cumulative_cost": 20200},
            {"month": "2024-03", "monthly_cost": 10400, "cumulative_cost": 30600},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service._check_trend_anomaly_alert(1, project, {})
        assert result is None  # 增长率约2%，低于30%阈值

    def test_anomalous_growth(self, service, db):
        project = _make_project()
        monthly_data = [
            {"month": "2024-01", "monthly_cost": 10000, "cumulative_cost": 10000},
            {"month": "2024-02", "monthly_cost": 15000, "cumulative_cost": 25000},
            {"month": "2024-03", "monthly_cost": 21000, "cumulative_cost": 46000},
        ]
        with patch.object(service, "_get_monthly_costs", return_value=monthly_data):
            result = service._check_trend_anomaly_alert(1, project, {})
        assert result is not None
        assert result["alert_type"] == "TREND_ANOMALY"


# ---------------------------------------------------------------------------
# Tests: check_cost_alerts (integration of sub-checks)
# ---------------------------------------------------------------------------

class TestCheckCostAlerts:
    def test_no_project(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.check_cost_alerts(project_id=99)
        assert result == []

    def test_alerts_returned(self, service, db):
        project = _make_project(budget_amount=100000, actual_cost=90000, progress_pct=50)
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        with patch.object(service, "_get_monthly_costs", return_value=[]):
            with patch.object(service, "_create_alert_record"):
                alerts = service.check_cost_alerts(project_id=1, auto_create=False)
        # 成本90%≥80%阈值 → 至少1个警告
        assert len(alerts) >= 1


# ---------------------------------------------------------------------------
# Tests: save_forecast
# ---------------------------------------------------------------------------

class TestSaveForecast:
    def test_project_not_found_raises(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            service.save_forecast(99, {"method": "LINEAR", "forecast_date": date.today()}, 1)

    def test_save_returns_forecast_object(self, service, db):
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project
        forecast_result = {
            "method": "LINEAR",
            "forecast_date": date.today(),
            "forecasted_completion_cost": 150000.0,
            "current_progress_pct": 50.0,
            "current_actual_cost": 60000.0,
            "current_budget": 120000.0,
            "monthly_forecast_data": [],
            "trend_data": {},
        }
        with patch("app.services.cost_forecast_service.save_obj"):
            result = service.save_forecast(1, forecast_result, created_by=1)
        assert result is not None

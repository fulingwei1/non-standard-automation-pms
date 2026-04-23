# -*- coding: utf-8 -*-
"""工时预测服务深度覆盖测试。"""

from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.timesheet import timesheet_forecast_service as svc_module
from app.services.timesheet.timesheet_forecast_service import TimesheetForecastService


def _chain_query(*, all_result=None, first_result=None):
    query = MagicMock()
    query.filter.return_value = query
    query.group_by.return_value = query
    query.having.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = all_result if all_result is not None else []
    query.first.return_value = first_result
    return query


def _patch_response_models(monkeypatch):
    factory = lambda **kwargs: SimpleNamespace(**kwargs)
    monkeypatch.setattr(svc_module, "ProjectForecastResponse", factory)
    monkeypatch.setattr(svc_module, "CompletionForecastResponse", factory)
    monkeypatch.setattr(svc_module, "GapAnalysisResponse", factory)
    monkeypatch.setattr(svc_module, "WorkloadAlertResponse", factory)


def test_forecast_project_hours_dispatches_and_rejects_unknown_method(monkeypatch):
    db = MagicMock()
    service = TimesheetForecastService(db)

    monkeypatch.setattr(service, "_forecast_by_historical_average", MagicMock(return_value="hist"))
    monkeypatch.setattr(service, "_forecast_by_linear_regression", MagicMock(return_value="linear"))
    monkeypatch.setattr(service, "_forecast_by_trend", MagicMock(return_value="trend"))

    assert service.forecast_project_hours(forecast_method="HISTORICAL_AVERAGE") == "hist"
    assert service.forecast_project_hours(forecast_method="LINEAR_REGRESSION") == "linear"
    assert service.forecast_project_hours(forecast_method="TREND_FORECAST") == "trend"

    with pytest.raises(ValueError, match="Unsupported forecast method"):
        service.forecast_project_hours(forecast_method="BOGUS")


def test_historical_average_uses_similar_projects_and_scaling():
    db = MagicMock()
    db.query.return_value = _chain_query(
        all_result=[
            SimpleNamespace(project_id=101, project_name="A", total_hours=100),
            SimpleNamespace(project_id=102, project_name="B", total_hours=200),
        ]
    )

    service = TimesheetForecastService(db)
    result = service._forecast_by_historical_average(
        project_id=9,
        project_name="新项目",
        project_type="ICT",
        complexity="HIGH",
        team_size=10,
        duration_days=60,
        similar_project_ids=[101, 102],
    )

    assert result.project_id == 9
    assert result.project_name == "新项目"
    assert float(result.predicted_hours) == pytest.approx(720.0)
    assert float(result.confidence_level) == 70.0


def test_linear_regression_fallback_without_sklearn(monkeypatch):
    db = MagicMock()
    db.query.return_value = _chain_query(
        all_result=[
            SimpleNamespace(total_hours=50, team_size=5, duration=10),
            SimpleNamespace(total_hours=20, team_size=2, duration=10),
            SimpleNamespace(total_hours=20, team_size=4, duration=5),
        ]
    )
    monkeypatch.setattr(svc_module, "SKLEARN_AVAILABLE", False)

    service = TimesheetForecastService(db)
    result = service._forecast_by_linear_regression(
        project_id=3,
        project_name="线回归项目",
        project_type="ICT",
        complexity="HIGH",
        team_size=3,
        duration_days=10,
    )

    assert result.project_id == 3
    assert result.project_name == "线回归项目"
    assert float(result.predicted_hours) == pytest.approx(45.0)
    assert float(result.confidence_level) == 65.0


def test_trend_forecast_uses_recent_trend_factor():
    db = MagicMock()
    db.query.return_value = _chain_query(
        all_result=[SimpleNamespace(daily_hours=hours) for hours in range(10, 20)]
    )

    service = TimesheetForecastService(db)
    result = service._forecast_by_trend(
        project_id=7,
        project_name="趋势项目",
        project_type="FCT",
        complexity="HIGH",
        team_size=5,
        duration_days=10,
    )

    assert result.project_id == 7
    assert result.project_name == "趋势项目"
    assert float(result.predicted_hours) == pytest.approx(256.77, abs=0.02)
    assert float(result.confidence_level) > 50


def test_forecast_completion_uses_default_branch_when_no_consumed_hours():
    db = MagicMock()
    project_query = _chain_query(first_result=SimpleNamespace(name="项目A"))
    consumed_query = _chain_query(first_result=SimpleNamespace(consumed_hours=0))
    db.query.side_effect = [project_query, consumed_query]

    service = TimesheetForecastService(db)
    result = service.forecast_completion(project_id=1)

    assert result.project_id == 1
    assert result.project_name == "项目A"
    assert result.predicted_days_remaining == 30
    assert result.predicted_completion_date == date.today() + timedelta(days=30)


def test_forecast_workload_alert_filters_and_sorts_levels():
    db = MagicMock()
    db.query.return_value = _chain_query(
        all_result=[
            SimpleNamespace(user_id=2, user_name="张三", department_name="测试部", total_hours=220, overtime_hours=60),
            SimpleNamespace(user_id=1, user_name="李四", department_name="研发部", total_hours=80, overtime_hours=10),
        ]
    )

    service = TimesheetForecastService(db)
    alerts = service.forecast_workload_alert(alert_level="CRITICAL", forecast_days=20)

    assert len(alerts) == 1
    assert alerts[0].user_id == 2
    assert alerts[0].alert_level == "CRITICAL"
    assert float(alerts[0].workload_saturation) > 120


def test_analyze_gap_respects_filters_and_returns_gap_rate():
    db = MagicMock()
    db.query.return_value = _chain_query(first_result=SimpleNamespace(total_hours=600))

    service = TimesheetForecastService(db)
    result = service.analyze_gap(
        period_type="MONTHLY",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 30),
        department_ids=[1],
        project_ids=[11, 12],
    )

    assert result.period_type == "MONTHLY"
    assert float(result.required_hours) == 600.0
    assert float(result.available_hours) > 0
    assert float(result.gap_rate) < 0


def test_historical_average_empty_history_adds_high_load_recommendations(monkeypatch):
    _patch_response_models(monkeypatch)
    db = MagicMock()
    db.query.return_value = _chain_query(all_result=[])

    service = TimesheetForecastService(db)
    result = service._forecast_by_historical_average(
        project_id=10,
        project_name="超大项目",
        project_type="ICT",
        complexity="HIGH",
        team_size=12,
        duration_days=20,
        similar_project_ids=None,
    )

    assert float(result.confidence_level) == 50.0
    assert "项目工时较大，建议分阶段实施" in result.recommendations
    assert "团队规模较大，注意协调沟通成本" in result.recommendations
    assert "高复杂度项目，建议预留缓冲时间" in result.recommendations



def test_historical_average_nan_hours_becomes_zero(monkeypatch):
    _patch_response_models(monkeypatch)
    db = MagicMock()
    db.query.return_value = _chain_query(
        all_result=[SimpleNamespace(project_id=1, project_name="A", total_hours=float("nan"))]
    )

    service = TimesheetForecastService(db)
    result = service._forecast_by_historical_average(
        project_id=11,
        project_name="NaN项目",
        project_type="ICT",
        complexity="MEDIUM",
        team_size=5,
        duration_days=30,
        similar_project_ids=[1],
    )

    assert float(result.predicted_hours) == 0.0


def test_linear_regression_sklearn_branch_and_high_hours_recommendation(monkeypatch):
    _patch_response_models(monkeypatch)
    db = MagicMock()
    db.query.return_value = _chain_query(
        all_result=[
            SimpleNamespace(total_hours=300, team_size=3, duration=10),
            SimpleNamespace(total_hours=500, team_size=5, duration=10),
            SimpleNamespace(total_hours=800, team_size=8, duration=10),
        ]
    )

    class FakeModel:
        coef_ = [2.0, 3.0, 4.0]
        intercept_ = 5.0

        def fit(self, x, y):
            self.fit_called = True

        def predict(self, data):
            rows = getattr(data, "shape", [len(data)])[0]
            if rows == 1:
                return [900.0]
            return [300.0, 500.0, 800.0]

    monkeypatch.setattr(svc_module, "SKLEARN_AVAILABLE", True)
    monkeypatch.setattr(svc_module, "LinearRegression", FakeModel, raising=False)
    monkeypatch.setattr(svc_module, "r2_score", lambda y_true, y_pred: 0.91, raising=False)

    service = TimesheetForecastService(db)
    result = service._forecast_by_linear_regression(
        project_id=8,
        project_name="大工时项目",
        project_type="ICT",
        complexity="HIGH",
        team_size=9,
        duration_days=30,
    )

    assert float(result.predicted_hours) == 900.0
    assert result.algorithm_params["feature_importance"]["team_size_coef"] == 2.0
    assert "预测工时较高，建议评估资源可用性" in result.recommendations



def test_linear_regression_with_too_few_samples_falls_back(monkeypatch):
    db = MagicMock()
    db.query.return_value = _chain_query(
        all_result=[
            SimpleNamespace(total_hours=100, team_size=2, duration=10),
            SimpleNamespace(total_hours=200, team_size=3, duration=12),
        ]
    )

    service = TimesheetForecastService(db)
    service._forecast_by_historical_average = MagicMock(return_value="fallback")

    assert service._forecast_by_linear_regression(1, "X", "ICT", "LOW", 3, 10) == "fallback"


def test_trend_forecast_fallback_and_downward_recommendation(monkeypatch):
    _patch_response_models(monkeypatch)
    db = MagicMock()
    service = TimesheetForecastService(db)
    service._forecast_by_historical_average = MagicMock(return_value="fallback")

    db.query.return_value = _chain_query(all_result=[SimpleNamespace(daily_hours=10)] * 5)
    assert service._forecast_by_trend(1, "A", "ICT", "LOW", 3, 10) == "fallback"

    db.query.return_value = _chain_query(
        all_result=[SimpleNamespace(daily_hours=x) for x in [20, 20, 20, 20, 20, 20, 20, 8, 8, 8, 8, 8, 8, 8]]
    )
    result = service._forecast_by_trend(2, "B", "ICT", "LOW", 3, 10)
    assert "工时呈下降趋势，效率有所提升" in result.recommendations


def test_forecast_completion_project_missing_and_zero_velocity_branch(monkeypatch):
    _patch_response_models(monkeypatch)
    db = MagicMock()
    missing_project_query = _chain_query(first_result=None)
    db.query.return_value = missing_project_query
    service = TimesheetForecastService(db)

    with pytest.raises(ValueError):
        service.forecast_completion(project_id=404)

    project_query = _chain_query(first_result=SimpleNamespace(name="项目B"))
    consumed_query = _chain_query(first_result=SimpleNamespace(consumed_hours=200))
    recent_query = _chain_query(first_result=SimpleNamespace(recent_hours=0, work_days=5))
    db.query.side_effect = [project_query, consumed_query, recent_query]

    result = service.forecast_completion(project_id=2)
    assert result.predicted_days_remaining == 30
    assert float(result.confidence_level) == 40.0
    assert "数据不足，预测置信度较低" in result.risk_factors



def test_forecast_completion_positive_velocity_branch(monkeypatch):
    _patch_response_models(monkeypatch)
    db = MagicMock()
    project_query = _chain_query(first_result=SimpleNamespace(name="项目C"))
    consumed_query = _chain_query(first_result=SimpleNamespace(consumed_hours=120))
    recent_query = _chain_query(first_result=SimpleNamespace(recent_hours=60, work_days=6))
    db.query.side_effect = [project_query, consumed_query, recent_query]

    service = TimesheetForecastService(db)
    result = service.forecast_completion(project_id=3)

    assert result.predicted_days_remaining == 12
    assert result.predicted_completion_date == date.today() + timedelta(days=12)
    assert float(result.confidence_level) == 65.0


def test_forecast_workload_alert_covers_filters_multiple_levels_and_low_recommendation(monkeypatch):
    _patch_response_models(monkeypatch)
    db = MagicMock()
    query = _chain_query(
        all_result=[
            SimpleNamespace(user_id=1, user_name="A", department_name="研发", total_hours=115, overtime_hours=10),
            SimpleNamespace(user_id=2, user_name="B", department_name="测试", total_hours=98, overtime_hours=10),
            SimpleNamespace(user_id=3, user_name="C", department_name="运维", total_hours=50, overtime_hours=0),
            SimpleNamespace(user_id=4, user_name="D", department_name="交付", total_hours=80, overtime_hours=0),
        ]
    )
    db.query.return_value = query

    service = TimesheetForecastService(db)
    alerts = service.forecast_workload_alert(user_ids=[1, 2, 3, 4], department_ids=[1], forecast_days=20)

    levels = {alert.user_id: alert.alert_level for alert in alerts}
    assert levels[1] == "HIGH"
    assert levels[2] == "MEDIUM"
    assert levels[3] == "LOW"
    assert 4 not in levels
    low_alert = next(alert for alert in alerts if alert.user_id == 3)
    assert "工时利用率较低，可分配更多任务" in low_alert.recommendations

    only_high = service.forecast_workload_alert(alert_level="HIGH", forecast_days=20)
    assert len(only_high) == 1
    assert only_high[0].user_id == 1


def test_analyze_gap_positive_gap_adds_recommendations(monkeypatch):
    _patch_response_models(monkeypatch)
    db = MagicMock()
    db.query.return_value = _chain_query(first_result=SimpleNamespace(total_hours=6000))

    service = TimesheetForecastService(db)
    result = service.analyze_gap(
        period_type="MONTHLY",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 10),
        project_ids=[1, 2, 3],
    )

    assert float(result.gap_hours) > 0
    assert any("建议增加人力或延长周期" in item for item in result.recommendations)
    assert "优先级排序，聚焦核心任务" in result.recommendations
    assert "缺口较大，考虑外部资源协助" in result.recommendations

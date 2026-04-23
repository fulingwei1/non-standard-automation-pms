# -*- coding: utf-8 -*-
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import app.services.timesheet.timesheet_forecast_service as svc_mod
from app.services.timesheet.timesheet_forecast_service import TimesheetForecastService


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


class TestTimesheetForecastServiceDeep2:
    def test_historical_average_fallback_builds_recommendations(self):
        db = MagicMock()
        service = TimesheetForecastService(db)

        query = MagicMock()
        query.filter.return_value.group_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value = query

        result = service._forecast_by_historical_average(
            project_id=None,
            project_name="新项目",
            project_type="ICT",
            complexity="HIGH",
            team_size=12,
            duration_days=20,
            similar_project_ids=None,
        )

        assert float(result.predicted_hours) == 2496.0
        assert float(result.confidence_level) == 50.0
        assert result.project_name == "新项目"

    def test_historical_average_with_similar_projects_scales_and_collects_examples(self):
        db = MagicMock()
        service = TimesheetForecastService(db)
        rows = [
            _ns(project_id=1, project_name="A", total_hours=100),
            _ns(project_id=2, project_name="B", total_hours=200),
        ]

        query = MagicMock()
        query.filter.return_value.group_by.return_value.all.return_value = rows
        db.query.return_value = query

        result = service._forecast_by_historical_average(
            project_id=9,
            project_name="目标项目",
            project_type="ICT",
            complexity="HIGH",
            team_size=10,
            duration_days=60,
            similar_project_ids=[1, 2],
        )

        assert float(result.predicted_hours) == 720.0
        assert float(result.confidence_level) == 70.0
        assert result.project_id == 9
        assert result.project_name == "目标项目"

    def test_linear_regression_falls_back_when_samples_insufficient(self):
        db = MagicMock()
        service = TimesheetForecastService(db)
        query = MagicMock()
        query.filter.return_value.group_by.return_value.having.return_value.all.return_value = [
            _ns(project_id=1),
            _ns(project_id=2),
        ]
        db.query.return_value = query
        service._forecast_by_historical_average = MagicMock(return_value="fallback")

        result = service._forecast_by_linear_regression(1, "P1", "ICT", "MEDIUM", 5, 30)

        assert result == "fallback"
        service._forecast_by_historical_average.assert_called_once_with(1, "P1", "ICT", "MEDIUM", 5, 30, None)

    def test_linear_regression_covers_sklearn_and_fallback_paths(self):
        historical_rows = [
            _ns(project_id=1, project_name="A", total_hours=300, team_size=3, duration=10),
            _ns(project_id=2, project_name="B", total_hours=400, team_size=4, duration=10),
            _ns(project_id=3, project_name="C", total_hours=500, team_size=5, duration=10),
        ]

        db1 = MagicMock()
        service1 = TimesheetForecastService(db1)
        query1 = MagicMock()
        query1.filter.return_value.group_by.return_value.having.return_value.all.return_value = historical_rows
        db1.query.return_value = query1
        fake_model = MagicMock()
        fake_model.coef_ = [10, 20, 30]
        fake_model.intercept_ = 40
        fake_model.predict.side_effect = [np.array([900.0]), np.array([300.0, 400.0, 500.0])]

        with patch.object(svc_mod, "SKLEARN_AVAILABLE", True), patch.object(svc_mod, "LinearRegression", return_value=fake_model, create=True), patch.object(svc_mod, "r2_score", return_value=0.83, create=True):
            result1 = service1._forecast_by_linear_regression(1, "P1", "ICT", "HIGH", 8, 20)

        assert float(result1.predicted_hours) == 900.0
        assert float(result1.confidence_level) == 83.0
        assert result1.project_name == "P1"

        db2 = MagicMock()
        service2 = TimesheetForecastService(db2)
        query2 = MagicMock()
        query2.filter.return_value.group_by.return_value.having.return_value.all.return_value = historical_rows
        db2.query.return_value = query2

        with patch.object(svc_mod, "SKLEARN_AVAILABLE", False):
            result2 = service2._forecast_by_linear_regression(2, "P2", "ICT", "LOW", 9, 20)

        assert float(result2.predicted_hours) == 900.0
        assert float(result2.confidence_level) == 65.0
        assert result2.project_name == "P2"

    def test_trend_forecast_fallback_and_rising_trend(self):
        db1 = MagicMock()
        service1 = TimesheetForecastService(db1)
        query1 = MagicMock()
        query1.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [_ns(daily_hours=10)] * 5
        db1.query.return_value = query1
        service1._forecast_by_historical_average = MagicMock(return_value="fallback")
        assert service1._forecast_by_trend(1, "P1", "ICT", "MEDIUM", 5, 30) == "fallback"

        db2 = MagicMock()
        service2 = TimesheetForecastService(db2)
        trend_rows = [_ns(daily_hours=10) for _ in range(7)] + [_ns(daily_hours=20) for _ in range(7)]
        query2 = MagicMock()
        query2.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = trend_rows
        db2.query.return_value = query2

        result = service2._forecast_by_trend(2, "P2", "ICT", "HIGH", 5, 30)

        assert float(result.predicted_hours) == 1125.0
        assert float(result.confidence_level) == 83.33
        assert result.project_name == "P2"

    def test_forecast_completion_handles_missing_project_and_low_velocity_risk(self):
        db1 = MagicMock()
        service1 = TimesheetForecastService(db1)
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = None
        db1.query.return_value = project_query

        with pytest.raises(ValueError, match="Project 404 not found"):
            service1.forecast_completion(404)

        db2 = MagicMock()
        service2 = TimesheetForecastService(db2)
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = _ns(name="项目A")
        consumed_query = MagicMock()
        consumed_query.filter.return_value.first.return_value = _ns(consumed_hours=100)
        recent_query = MagicMock()
        recent_query.filter.return_value.first.return_value = _ns(recent_hours=1, work_days=1)
        db2.query.side_effect = [project_query, consumed_query, recent_query]

        result = service2.forecast_completion(1)

        assert result.project_name == "项目A"
        assert result.predicted_days_remaining == 100
        assert result.predicted_completion_date == date.today() + timedelta(days=100)

    def test_trend_forecast_covers_declining_trend_message_branch(self):
        db = MagicMock()
        service = TimesheetForecastService(db)
        trend_rows = [_ns(daily_hours=20) for _ in range(7)] + [_ns(daily_hours=10) for _ in range(7)]
        query = MagicMock()
        query.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = trend_rows
        db.query.return_value = query

        result = service._forecast_by_trend(3, "P3", "ICT", "LOW", 5, 30)

        assert float(result.predicted_hours) == 168.75
        assert result.project_name == "P3"

    def test_forecast_completion_covers_zero_consumed_and_zero_velocity_paths(self):
        db1 = MagicMock()
        service1 = TimesheetForecastService(db1)
        project_query1 = MagicMock()
        project_query1.filter.return_value.first.return_value = _ns(name="项目B")
        consumed_query1 = MagicMock()
        consumed_query1.filter.return_value.first.return_value = _ns(consumed_hours=0)
        db1.query.side_effect = [project_query1, consumed_query1]

        result1 = service1.forecast_completion(2)
        assert result1.predicted_days_remaining == 30
        assert result1.predicted_completion_date == date.today() + timedelta(days=30)

        db2 = MagicMock()
        service2 = TimesheetForecastService(db2)
        project_query2 = MagicMock()
        project_query2.filter.return_value.first.return_value = _ns(name="项目C")
        consumed_query2 = MagicMock()
        consumed_query2.filter.return_value.first.return_value = _ns(consumed_hours=100)
        recent_query2 = MagicMock()
        recent_query2.filter.return_value.first.return_value = _ns(recent_hours=0, work_days=1)
        db2.query.side_effect = [project_query2, consumed_query2, recent_query2]

        result2 = service2.forecast_completion(3)
        assert result2.predicted_days_remaining == 30
        assert result2.predicted_completion_date == date.today() + timedelta(days=30)

    def test_generate_forecast_curve_and_workload_alerts_cover_levels_and_filters(self):
        service = TimesheetForecastService(MagicMock())
        curve = service._generate_forecast_curve(120, 0, 50, 0)
        assert len(curve.labels) == 30
        assert curve.datasets[1]["data"][-1] is None

        db = MagicMock()
        service = TimesheetForecastService(db)
        rows = [
            _ns(user_id=1, user_name="A", department_name="研发", total_hours=60, overtime_hours=20),
            _ns(user_id=2, user_name="B", department_name="测试", total_hours=40, overtime_hours=10),
            _ns(user_id=3, user_name="C", department_name="研发", total_hours=36, overtime_hours=0),
            _ns(user_id=4, user_name="D", department_name=None, total_hours=20, overtime_hours=0),
            _ns(user_id=5, user_name="E", department_name="研发", total_hours=28, overtime_hours=0),
        ]
        query = MagicMock()
        query.filter.return_value = query
        query.group_by.return_value.all.return_value = rows
        db.query.return_value = query

        alerts = service.forecast_workload_alert(user_ids=[1, 2], department_ids=[10], forecast_days=7)

        assert [a.alert_level for a in alerts] == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert [a.user_id for a in alerts] == [1, 2, 3, 4]

        query2 = MagicMock()
        query2.filter.return_value = query2
        query2.group_by.return_value.all.return_value = rows
        db.query.return_value = query2
        high_only = service.forecast_workload_alert(alert_level="HIGH", forecast_days=7)
        assert [a.user_id for a in high_only] == [2]

    def test_analyze_gap_covers_shortage_and_surplus_paths(self):
        start = date(2026, 4, 1)
        end = date(2026, 4, 7)

        db1 = MagicMock()
        service1 = TimesheetForecastService(db1)
        query1 = MagicMock()
        query1.filter.return_value = query1
        query1.first.return_value = _ns(total_hours=1500)
        db1.query.return_value = query1

        result1 = service1.analyze_gap(
            period_type="week",
            start_date=start,
            end_date=end,
            department_ids=[1],
            project_ids=[11, 22],
        )

        assert float(result1.available_hours) == 800.0
        assert float(result1.required_hours) == 1500.0
        assert float(result1.gap_hours) == 700.0
        assert float(result1.gap_rate) == 46.67

        db2 = MagicMock()
        service2 = TimesheetForecastService(db2)
        query2 = MagicMock()
        query2.filter.return_value = query2
        query2.first.return_value = _ns(total_hours=600)
        db2.query.return_value = query2

        result2 = service2.analyze_gap(period_type="week", start_date=start, end_date=end)

        assert float(result2.gap_hours) == -200.0
        assert float(result2.gap_rate) == -33.33

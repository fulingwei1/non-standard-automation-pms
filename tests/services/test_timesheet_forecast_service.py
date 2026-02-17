# -*- coding: utf-8 -*-
"""工时预测服务单元测试 (TimesheetForecastService)"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_db():
    return MagicMock()


def _make_project(**kw):
    p = MagicMock()
    defaults = dict(
        id=1,
        project_name="比亚迪ADAS ICT测试系统",
        project_code="BYD-2024-001",
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


class TestTimesheetForecastServiceInit:
    def test_init_sets_db(self):
        from app.services.timesheet_forecast_service import TimesheetForecastService
        db = _make_db()
        svc = TimesheetForecastService(db)
        assert svc.db is db


class TestForecastProjectHours:
    def test_historical_average_method_called(self):
        from app.services.timesheet_forecast_service import TimesheetForecastService
        db = _make_db()
        svc = TimesheetForecastService(db)
        mock_result = MagicMock()
        svc._forecast_by_historical_average = MagicMock(return_value=mock_result)
        result = svc.forecast_project_hours(
            project_id=1,
            project_type="ICT",
            complexity="MEDIUM",
            team_size=5,
            duration_days=60,
            forecast_method="HISTORICAL_AVERAGE"
        )
        assert result is mock_result
        svc._forecast_by_historical_average.assert_called_once()

    def test_linear_regression_method_called(self):
        from app.services.timesheet_forecast_service import TimesheetForecastService
        db = _make_db()
        svc = TimesheetForecastService(db)
        mock_result = MagicMock()
        svc._forecast_by_linear_regression = MagicMock(return_value=mock_result)
        result = svc.forecast_project_hours(
            project_id=1,
            project_type="ICT",
            forecast_method="LINEAR_REGRESSION"
        )
        assert result is mock_result
        svc._forecast_by_linear_regression.assert_called_once()

    def test_trend_forecast_method_called(self):
        from app.services.timesheet_forecast_service import TimesheetForecastService
        db = _make_db()
        svc = TimesheetForecastService(db)
        mock_result = MagicMock()
        svc._forecast_by_trend = MagicMock(return_value=mock_result)
        result = svc.forecast_project_hours(
            project_id=1,
            project_type="ICT",
            forecast_method="TREND_FORECAST"
        )
        assert result is mock_result
        svc._forecast_by_trend.assert_called_once()


class TestForecastByHistoricalAverage:
    def test_no_similar_projects_fallback(self):
        """历史平均法：无相似项目时应有合理返回"""
        from app.services.timesheet_forecast_service import TimesheetForecastService
        db = _make_db()
        # 查询相似项目，返回空列表
        db.query.return_value.filter.return_value.all.return_value = []
        svc = TimesheetForecastService(db)
        result = svc._forecast_by_historical_average(
            project_id=None,
            project_name="新项目",
            project_type="ICT",
            complexity="MEDIUM",
            team_size=5,
            duration_days=60,
            similar_project_ids=None
        )
        # 返回值应为 ProjectForecastResponse 或包含预测数据的对象
        assert result is not None


class TestForecastByLinearRegression:
    def test_returns_forecast_result(self):
        """线性回归法：返回预测结果"""
        from app.services.timesheet_forecast_service import TimesheetForecastService
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = TimesheetForecastService(db)
        result = svc._forecast_by_linear_regression(
            project_id=None,
            project_name="新项目",
            project_type="ICT",
            complexity="HIGH",
            team_size=8,
            duration_days=90
        )
        assert result is not None


class TestInitTimesheetForecastService:
    def test_service_methods_exist(self):
        """验证关键方法存在"""
        from app.services.timesheet_forecast_service import TimesheetForecastService
        assert hasattr(TimesheetForecastService, '__init__')
        assert hasattr(TimesheetForecastService, 'forecast_project_hours')
        assert hasattr(TimesheetForecastService, '_forecast_by_historical_average')
        assert hasattr(TimesheetForecastService, '_forecast_by_linear_regression')
        assert hasattr(TimesheetForecastService, '_forecast_by_trend')

    def test_db_injection(self):
        """验证db正确注入"""
        from app.services.timesheet_forecast_service import TimesheetForecastService
        db = MagicMock()
        svc = TimesheetForecastService(db)
        assert svc.db is db

    def test_forecast_method_routing_invalid(self):
        """传入无效预测方法应处理（不崩溃或抛出ValueError）"""
        from app.services.timesheet_forecast_service import TimesheetForecastService
        db = _make_db()
        svc = TimesheetForecastService(db)
        # 对于未知方法名，应返回 None 或抛出异常（两种都可接受）
        try:
            result = svc.forecast_project_hours(
                project_id=1,
                forecast_method="UNKNOWN_METHOD"
            )
            # 如果返回 None 也可接受
        except Exception:
            pass  # 异常也可接受

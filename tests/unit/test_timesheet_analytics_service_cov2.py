# -*- coding: utf-8 -*-
"""
timesheet_analytics_service.py 单元测试（第二批）
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_svc(mock_db=None):
    from app.services.timesheet_analytics_service import TimesheetAnalyticsService
    if mock_db is None:
        mock_db = MagicMock()
    return TimesheetAnalyticsService(mock_db)


# ─── 1. _calculate_trend ─────────────────────────────────────────────────────
def test_calculate_trend_stable():
    svc = _make_svc()
    r1 = MagicMock()
    r1.total_hours = 8.0
    r2 = MagicMock()
    r2.total_hours = 8.0

    trend, rate = svc._calculate_trend([r1, r2])
    assert trend == "STABLE"
    assert rate == 0.0


def test_calculate_trend_increasing():
    svc = _make_svc()
    r1 = MagicMock()
    r1.total_hours = 5.0
    r2 = MagicMock()
    r2.total_hours = 10.0

    trend, rate = svc._calculate_trend([r1, r2])
    assert trend == "INCREASING"
    assert rate > 5


def test_calculate_trend_decreasing():
    svc = _make_svc()
    r1 = MagicMock()
    r1.total_hours = 10.0
    r2 = MagicMock()
    r2.total_hours = 5.0

    trend, rate = svc._calculate_trend([r1, r2])
    assert trend == "DECREASING"
    assert rate < -5


def test_calculate_trend_single_point():
    svc = _make_svc()
    r = MagicMock()
    r.total_hours = 8.0
    trend, rate = svc._calculate_trend([r])
    assert trend == "STABLE"
    assert rate == 0.0


def test_calculate_trend_empty():
    svc = _make_svc()
    trend, rate = svc._calculate_trend([])
    assert trend == "STABLE"
    assert rate == 0.0


# ─── 2. _generate_trend_chart ────────────────────────────────────────────────
def test_generate_trend_chart_daily():
    from app.schemas.timesheet_analytics import TrendChartData
    svc = _make_svc()

    r = MagicMock()
    r.work_date = date(2024, 1, 15)
    r.total_hours = 8.0
    r.normal_hours = 8.0
    r.overtime_hours = 0.0

    chart = svc._generate_trend_chart([r], "DAILY")
    assert isinstance(chart, TrendChartData)
    assert "2024-01-15" in chart.labels
    assert len(chart.datasets) == 3


def test_generate_trend_chart_monthly():
    from app.schemas.timesheet_analytics import TrendChartData
    svc = _make_svc()

    r = MagicMock()
    r.work_date = date(2024, 3, 1)
    r.total_hours = 160.0
    r.normal_hours = 160.0
    r.overtime_hours = 0.0

    chart = svc._generate_trend_chart([r], "MONTHLY")
    assert "2024-03" in chart.labels


def test_generate_trend_chart_empty():
    from app.schemas.timesheet_analytics import TrendChartData
    svc = _make_svc()
    chart = svc._generate_trend_chart([], "DAILY")
    assert chart.labels == []
    assert len(chart.datasets) == 3


# ─── 3. analyze_trend - DB mock 全链路 ──────────────────────────────────────
def test_analyze_trend_no_results():
    svc = _make_svc()

    # 模拟查询结果为空
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.group_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []

    svc.db.query.return_value = mock_query

    result = svc.analyze_trend(
        period_type="DAILY",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )

    assert result.total_hours == Decimal("0")
    assert result.trend == "STABLE"


# ─── 4. analyze_workload - 基本调用 ─────────────────────────────────────────
def test_analyze_workload_no_results():
    from app.schemas.timesheet_analytics import WorkloadHeatmapResponse
    svc = _make_svc()

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.group_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []

    svc.db.query.return_value = mock_query

    result = svc.analyze_workload(
        period_type="DAILY",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )
    # 应返回 WorkloadHeatmapResponse 实例
    assert isinstance(result, WorkloadHeatmapResponse)
    assert result.period_type == "DAILY"

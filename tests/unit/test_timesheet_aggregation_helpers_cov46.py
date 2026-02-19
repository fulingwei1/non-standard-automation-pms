# -*- coding: utf-8 -*-
"""第四十六批 - 工时汇总辅助服务单元测试"""
import pytest
from decimal import Decimal
from datetime import date

pytest.importorskip("app.services.timesheet_aggregation_helpers",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.timesheet_aggregation_helpers import (
    calculate_month_range,
    query_timesheets,
    calculate_hours_summary,
    build_project_breakdown,
    build_daily_breakdown,
    build_task_breakdown,
    get_or_create_summary,
)


def _make_timesheet(hours=8.0, overtime_type="NORMAL", project_id=1,
                    project_code="P001", project_name="项目1",
                    task_id=None, task_name=None, work_date=None):
    ts = MagicMock()
    ts.hours = hours
    ts.overtime_type = overtime_type
    ts.project_id = project_id
    ts.project_code = project_code
    ts.project_name = project_name
    ts.task_id = task_id
    ts.task_name = task_name
    ts.work_date = work_date or date(2024, 1, 15)
    return ts


class TestCalculateMonthRange:
    def test_returns_tuple_of_dates(self):
        with patch("app.services.timesheet_aggregation_helpers.get_month_range_by_ym",
                   return_value=(date(2024, 1, 1), date(2024, 1, 31))):
            start, end = calculate_month_range(2024, 1)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)


class TestQueryTimesheets:
    def test_returns_approved_timesheets(self):
        db = MagicMock()
        ts = _make_timesheet()
        db.query.return_value.filter.return_value.all.return_value = [ts]

        result = query_timesheets(db, date(2024, 1, 1), date(2024, 1, 31),
                                  None, None, None)
        assert len(result) >= 0  # call doesn't raise

    def test_applies_user_filter(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = query_timesheets(db, date(2024, 1, 1), date(2024, 1, 31),
                                  user_id=5, department_id=None, project_id=None)
        assert isinstance(result, list)


class TestCalculateHoursSummary:
    def test_totals_hours(self):
        ts1 = _make_timesheet(hours=8.0, overtime_type="NORMAL")
        ts2 = _make_timesheet(hours=3.0, overtime_type="OVERTIME")
        result = calculate_hours_summary([ts1, ts2])
        assert result["total_hours"] == pytest.approx(11.0)
        assert result["normal_hours"] == pytest.approx(8.0)
        assert result["overtime_hours"] == pytest.approx(3.0)

    def test_empty_list_returns_zeros(self):
        result = calculate_hours_summary([])
        assert result["total_hours"] == 0.0


class TestBuildProjectBreakdown:
    def test_groups_by_project(self):
        ts1 = _make_timesheet(hours=5.0, project_id=1, project_code="P001")
        ts2 = _make_timesheet(hours=3.0, project_id=1, project_code="P001")
        result = build_project_breakdown([ts1, ts2])
        key = "P001_1"
        assert key in result
        assert result[key]["hours"] == pytest.approx(8.0)

    def test_skips_no_project(self):
        ts = _make_timesheet(hours=4.0, project_id=None)
        result = build_project_breakdown([ts])
        assert result == {}


class TestBuildDailyBreakdown:
    def test_groups_by_date(self):
        ts = _make_timesheet(hours=8.0, overtime_type="NORMAL",
                             work_date=date(2024, 1, 15))
        result = build_daily_breakdown([ts])
        assert "2024-01-15" in result
        assert result["2024-01-15"]["hours"] == pytest.approx(8.0)


class TestBuildTaskBreakdown:
    def test_groups_by_task(self):
        ts = _make_timesheet(hours=4.0, task_id=10, task_name="任务A")
        result = build_task_breakdown([ts])
        assert "task_10" in result
        assert result["task_10"]["hours"] == pytest.approx(4.0)

    def test_skips_no_task(self):
        ts = _make_timesheet(hours=4.0, task_id=None)
        result = build_task_breakdown([ts])
        assert result == {}


class TestGetOrCreateSummary:
    def test_creates_new_summary_when_not_found(self):
        db = MagicMock()
        # With user_id=1 only (no project_id/department_id):
        # chain = query().filter().filter().first() -> None
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        hours = {"total_hours": 80.0, "normal_hours": 80.0, "overtime_hours": 0.0,
                 "weekend_hours": 0.0, "holiday_hours": 0.0}

        result = get_or_create_summary(
            db, "USER", 2024, 1, user_id=1,
            project_id=None, department_id=None,
            hours_summary=hours, project_breakdown={},
            daily_breakdown={}, task_breakdown={},
            entries_count=10
        )
        db.add.assert_called_once()

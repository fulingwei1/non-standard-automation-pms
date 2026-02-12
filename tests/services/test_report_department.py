# -*- coding: utf-8 -*-
"""Tests for app.services.report_framework.generators.department"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.report_framework.generators.department import DeptReportGenerator


def _mock_dept(id=1, dept_name="技术部", dept_code="TECH"):
    d = MagicMock()
    d.id = id
    d.dept_name = dept_name
    d.dept_code = dept_code
    d.name = dept_name
    return d


def _mock_user(id=1, real_name="张三", username="zhangsan", department_id=1, position="工程师"):
    u = MagicMock()
    u.id = id
    u.real_name = real_name
    u.username = username
    u.department_id = department_id
    u.position = position
    u.is_active = True
    return u


def _mock_timesheet(user_id=1, project_id=1, hours=8.0, work_date=date(2025, 1, 6)):
    t = MagicMock()
    t.user_id = user_id
    t.project_id = project_id
    t.hours = hours
    t.work_date = work_date
    return t


class TestGenerateWeekly:
    def test_dept_not_found(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = DeptReportGenerator.generate_weekly(db, 999, date(2025, 1, 6), date(2025, 1, 10))
        assert "error" in result

    @patch.object(DeptReportGenerator, "_get_member_workload", return_value=[])
    @patch.object(DeptReportGenerator, "_get_project_breakdown", return_value=[])
    @patch.object(DeptReportGenerator, "_get_timesheet_summary", return_value={"total_hours": 40})
    @patch.object(DeptReportGenerator, "_get_department_members")
    def test_success(self, mock_members, mock_ts, mock_pb, mock_wl):
        db = MagicMock()
        dept = _mock_dept()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = dept
        db.query.return_value = q

        users = [_mock_user()]
        mock_members.return_value = users

        result = DeptReportGenerator.generate_weekly(db, 1, date(2025, 1, 6), date(2025, 1, 10))
        assert result["summary"]["department_id"] == 1
        assert result["timesheet"]["total_hours"] == 40
        assert result["members"]["total_count"] == 1


class TestGenerateMonthly:
    def test_dept_not_found(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = DeptReportGenerator.generate_monthly(db, 999, date(2025, 1, 1), date(2025, 1, 31))
        assert "error" in result

    @patch.object(DeptReportGenerator, "_get_member_workload_detailed", return_value=[
        {"utilization_rate": 80.0}
    ])
    @patch.object(DeptReportGenerator, "_get_project_breakdown", return_value=[])
    @patch.object(DeptReportGenerator, "_get_timesheet_summary", return_value={"total_hours": 160})
    @patch.object(DeptReportGenerator, "_get_project_stats", return_value={
        "total": 3, "by_health": {"H3": 1}, "by_stage": {}, "completed_this_month": 0, "started_this_month": 0
    })
    @patch.object(DeptReportGenerator, "_get_department_members")
    def test_success(self, mock_members, mock_ps, mock_ts, mock_pb, mock_wl):
        db = MagicMock()
        dept = _mock_dept()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = dept
        db.query.return_value = q

        mock_members.return_value = [_mock_user()]

        result = DeptReportGenerator.generate_monthly(db, 1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["key_metrics"]["total_members"] == 1
        assert result["key_metrics"]["high_risk_projects"] == 1


class TestGetDepartmentMembers:
    def test_by_department_id(self):
        from app.models.user import User
        db = MagicMock()
        dept = _mock_dept()
        users = [_mock_user()]

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = users
        db.query.return_value = q

        with patch.object(User, "department_id", create=True):
            result = DeptReportGenerator._get_department_members(db, dept)
            assert len(result) == 1

    def test_fallback_by_name(self):
        from app.models.user import User
        db = MagicMock()
        dept = _mock_dept()

        q = MagicMock()
        q.filter.return_value = q
        q.all.side_effect = [[], [_mock_user()]]  # first empty, then by name
        db.query.return_value = q

        with patch.object(User, "department_id", create=True):
            result = DeptReportGenerator._get_department_members(db, dept)
            assert len(result) == 1


class TestGetTimesheetSummary:
    def test_empty_users(self):
        db = MagicMock()
        result = DeptReportGenerator._get_timesheet_summary(db, [], date(2025, 1, 1), date(2025, 1, 31))
        assert result["total_hours"] == 0

    def test_with_data(self):
        db = MagicMock()
        ts = [_mock_timesheet(hours=8), _mock_timesheet(hours=6)]
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = ts
        db.query.return_value = q

        result = DeptReportGenerator._get_timesheet_summary(db, [1], date(2025, 1, 1), date(2025, 1, 31))
        assert result["total_hours"] == 14


class TestGetProjectBreakdown:
    def test_empty_users(self):
        db = MagicMock()
        result = DeptReportGenerator._get_project_breakdown(db, [], date(2025, 1, 1), date(2025, 1, 31))
        assert result == []

    def test_with_data(self):
        db = MagicMock()
        ts1 = _mock_timesheet(project_id=1, hours=8)
        ts2 = _mock_timesheet(project_id=1, hours=4)
        ts3 = _mock_timesheet(project_id=2, hours=6)

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [ts1, ts2, ts3]
        proj = MagicMock(project_name="项目A")
        q.first.return_value = proj
        db.query.return_value = q

        result = DeptReportGenerator._get_project_breakdown(db, [1], date(2025, 1, 1), date(2025, 1, 31))
        assert len(result) >= 1


class TestGetMemberWorkload:
    def test_empty(self):
        db = MagicMock()
        result = DeptReportGenerator._get_member_workload(db, [], date(2025, 1, 6), date(2025, 1, 10))
        assert result == []

    def test_with_data(self):
        db = MagicMock()
        user = _mock_user()
        ts = [_mock_timesheet(user_id=1, hours=8)]

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = ts
        db.query.return_value = q

        result = DeptReportGenerator._get_member_workload(db, [user], date(2025, 1, 6), date(2025, 1, 10))
        assert len(result) == 1
        assert result[0]["total_hours"] == 8


class TestGetProjectStats:
    def test_empty_users(self):
        db = MagicMock()
        result = DeptReportGenerator._get_project_stats(db, [], date(2025, 1, 1), date(2025, 1, 31))
        assert result["total"] == 0

    def test_with_data(self):
        db = MagicMock()
        pm = MagicMock(project_id=1, user_id=1)
        project = MagicMock(
            id=1, is_active=True, stage="S1", health="H1",
            created_at=MagicMock(), updated_at=MagicMock()
        )
        project.created_at.date.return_value = date(2025, 1, 15)
        project.updated_at.date.return_value = date(2025, 1, 20)

        q = MagicMock()
        q.filter.return_value = q
        q.all.side_effect = [[pm], [project]]
        db.query.return_value = q

        result = DeptReportGenerator._get_project_stats(db, [1], date(2025, 1, 1), date(2025, 1, 31))
        assert result["total"] == 1

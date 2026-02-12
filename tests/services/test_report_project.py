# -*- coding: utf-8 -*-
"""Tests for app.services.report_framework.generators.project"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from unittest.mock import PropertyMock
from app.services.report_framework.generators.project import ProjectReportGenerator
from app.models.project.financial import ProjectMilestone


def _mock_project(**kw):
    p = MagicMock()
    defaults = dict(
        id=1, project_code="P-001", project_name="测试项目",
        customer_name="客户A", current_stage="S3", health_status="H1",
        progress=50.0, budget_amount=100000,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


def _mock_milestone(id=1, status="COMPLETED", milestone_name="M1",
                     milestone_date=date(2025, 1, 15), actual_date=date(2025, 1, 14)):
    m = MagicMock()
    m.id = id
    m.status = status
    m.milestone_name = milestone_name
    m.milestone_date = milestone_date
    m.actual_date = actual_date
    return m


def _mock_timesheet(user_id=1, hours=8.0, work_date=date(2025, 1, 6), project_id=1):
    t = MagicMock()
    t.user_id = user_id
    t.hours = hours
    t.work_date = work_date
    t.project_id = project_id
    return t


class TestGenerateWeekly:
    def test_project_not_found(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = ProjectReportGenerator.generate_weekly(db, 999, date(2025, 1, 6), date(2025, 1, 10))
        assert "error" in result

    def test_success(self):
        db = MagicMock()
        project = _mock_project()
        milestone = _mock_milestone()
        ts = _mock_timesheet()
        machine = MagicMock(id=1, machine_code="M-1", machine_name="机台1", status="PENDING", progress=0)

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = project
        q.all.side_effect = [[milestone], [ts], [machine]]
        db.query.return_value = q

        with patch.object(ProjectMilestone, "milestone_date", create=True):
            result = ProjectReportGenerator.generate_weekly(db, 1, date(2025, 1, 6), date(2025, 1, 10))
        assert result["summary"]["project_id"] == 1
        assert "milestones" in result
        assert "timesheet" in result
        assert "machines" in result
        assert "risks" in result


class TestGenerateMonthly:
    def test_project_not_found(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = ProjectReportGenerator.generate_monthly(db, 999, date(2025, 1, 1), date(2025, 1, 31))
        assert "error" in result

    def test_success(self):
        db = MagicMock()
        project = _mock_project()
        milestone = _mock_milestone()
        ts = _mock_timesheet()

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = project
        q.all.side_effect = [[milestone], [ts], [ts], [ts], [ts], [ts]]  # milestones + weekly queries
        db.query.return_value = q

        with patch.object(ProjectMilestone, "milestone_date", create=True):
            result = ProjectReportGenerator.generate_monthly(db, 1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["summary"]["report_type"] == "月报"
        assert "cost" in result


class TestBuildProjectSummary:
    def test_summary(self):
        project = _mock_project()
        result = ProjectReportGenerator._build_project_summary(
            project, date(2025, 1, 6), date(2025, 1, 10)
        )
        assert result["project_id"] == 1
        assert result["project_name"] == "测试项目"
        assert result["progress"] == 50.0


class TestGetMilestoneData:
    def test_empty(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        with patch.object(ProjectMilestone, "milestone_date", create=True):
            result = ProjectReportGenerator._get_milestone_data(db, 1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["summary"]["total"] == 0

    def test_with_milestones(self):
        db = MagicMock()
        m1 = _mock_milestone(id=1, status="COMPLETED")
        m2 = _mock_milestone(id=2, status="DELAYED")
        m3 = _mock_milestone(id=3, status="IN_PROGRESS")

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [m1, m2, m3]
        db.query.return_value = q

        with patch.object(ProjectMilestone, "milestone_date", create=True):
            result = ProjectReportGenerator._get_milestone_data(db, 1, date(2025, 1, 1), date(2025, 1, 31))
        assert result["summary"]["completed"] == 1
        assert result["summary"]["delayed"] == 1
        assert result["summary"]["in_progress"] == 1


class TestGetTimesheetData:
    def test_empty(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = ProjectReportGenerator._get_timesheet_data(db, 1, date(2025, 1, 6), date(2025, 1, 10))
        assert result["total_hours"] == 0
        assert result["unique_workers"] == 0

    def test_with_data(self):
        db = MagicMock()
        ts1 = _mock_timesheet(user_id=1, hours=8)
        ts2 = _mock_timesheet(user_id=2, hours=6)

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [ts1, ts2]
        db.query.return_value = q

        result = ProjectReportGenerator._get_timesheet_data(db, 1, date(2025, 1, 6), date(2025, 1, 10))
        assert result["total_hours"] == 14
        assert result["unique_workers"] == 2


class TestGetMachineData:
    def test_empty(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = ProjectReportGenerator._get_machine_data(db, 1)
        assert result == []

    def test_with_machines(self):
        db = MagicMock()
        m = MagicMock(id=1, machine_code="M-1", machine_name="机台1", status="PENDING", progress=30.0)

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [m]
        db.query.return_value = q

        result = ProjectReportGenerator._get_machine_data(db, 1)
        assert len(result) == 1


class TestGetWeeklyTrend:
    def test_single_week(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [_mock_timesheet(hours=40)]
        db.query.return_value = q

        result = ProjectReportGenerator._get_weekly_trend(db, 1, date(2025, 1, 6), date(2025, 1, 10))
        assert len(result) >= 1
        assert result[0]["week"] == 1


class TestGetCostSummary:
    def test_with_budget(self):
        project = _mock_project(budget_amount=100000)
        result = ProjectReportGenerator._get_cost_summary(project)
        assert result["planned_cost"] == 100000

    def test_no_budget(self):
        project = _mock_project(budget_amount=None)
        result = ProjectReportGenerator._get_cost_summary(project)
        assert result["planned_cost"] == 0


class TestAssessRisks:
    def test_healthy(self):
        summary = {"health_status": "H1"}
        milestones = {"summary": {"delayed": 0}}
        result = ProjectReportGenerator._assess_risks(summary, milestones)
        assert result == []

    def test_unhealthy(self):
        summary = {"health_status": "H3"}
        milestones = {"summary": {"delayed": 2}}
        result = ProjectReportGenerator._assess_risks(summary, milestones)
        assert len(result) == 2

    def test_delayed_only(self):
        summary = {"health_status": "H1"}
        milestones = {"summary": {"delayed": 1}}
        result = ProjectReportGenerator._assess_risks(summary, milestones)
        assert len(result) == 1
        assert result[0]["type"] == "里程碑延期"

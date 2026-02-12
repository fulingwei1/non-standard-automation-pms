# -*- coding: utf-8 -*-
"""Tests for app.services.report_framework.generators.analysis"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.report_framework.generators.analysis import AnalysisReportGenerator


def _mock_user(id=1, real_name="张三", username="zhangsan", department="技术部"):
    u = MagicMock()
    u.id = id
    u.real_name = real_name
    u.username = username
    u.department = department
    u.is_active = True
    return u


def _mock_timesheet(user_id=1, project_id=1, hours=8.0, work_date=date(2025, 1, 6)):
    t = MagicMock()
    t.user_id = user_id
    t.project_id = project_id
    t.hours = hours
    t.work_date = work_date
    return t


class TestGenerateWorkloadAnalysis:
    @patch.object(AnalysisReportGenerator, "_calculate_workload")
    @patch.object(AnalysisReportGenerator, "_get_user_scope")
    def test_basic(self, mock_scope, mock_calc):
        db = MagicMock()
        users = [_mock_user()]
        mock_scope.return_value = (users, "技术部")
        mock_calc.return_value = (
            [{"user_id": 1, "working_days": 20}],
            {"OVERLOAD": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0}
        )

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = AnalysisReportGenerator.generate_workload_analysis(
            db, department_id=1, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        assert result["summary"]["scope"] == "技术部"
        assert result["summary"]["total_users"] == 1

    @patch.object(AnalysisReportGenerator, "_calculate_workload")
    @patch.object(AnalysisReportGenerator, "_get_user_scope")
    def test_default_dates(self, mock_scope, mock_calc):
        db = MagicMock()
        mock_scope.return_value = ([], "全公司")
        mock_calc.return_value = ([], {"OVERLOAD": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0})

        result = AnalysisReportGenerator.generate_workload_analysis(db)
        assert result["summary"]["total_users"] == 0


class TestGenerateCostAnalysis:
    @patch.object(AnalysisReportGenerator, "_calculate_project_costs")
    @patch.object(AnalysisReportGenerator, "_get_projects")
    def test_basic(self, mock_projects, mock_costs):
        db = MagicMock()
        project = MagicMock(id=1, project_name="P1")
        mock_projects.return_value = [project]
        mock_costs.return_value = (
            [{"project_id": 1, "budget": 100000, "actual_cost": 80000}],
            100000, 80000
        )

        result = AnalysisReportGenerator.generate_cost_analysis(
            db, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        assert result["summary"]["project_count"] == 1
        assert result["summary"]["total_variance"] == 20000

    @patch.object(AnalysisReportGenerator, "_calculate_project_costs")
    @patch.object(AnalysisReportGenerator, "_get_projects")
    def test_default_dates(self, mock_projects, mock_costs):
        db = MagicMock()
        mock_projects.return_value = []
        mock_costs.return_value = ([], 0, 0)

        result = AnalysisReportGenerator.generate_cost_analysis(db)
        assert result["summary"]["project_count"] == 0


class TestGetUserScope:
    def test_all_company(self):
        db = MagicMock()
        users = [_mock_user()]
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = users
        db.query.return_value = q

        result_users, scope = AnalysisReportGenerator._get_user_scope(db, None)
        assert scope == "全公司"
        assert len(result_users) == 1

    def test_department(self):
        from app.models.user import User
        db = MagicMock()
        dept = MagicMock(id=1, dept_name="技术部", name="技术部")
        users = [_mock_user()]

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = dept
        q.all.return_value = users
        db.query.return_value = q

        with patch.object(User, "department_id", create=True):
            result_users, scope = AnalysisReportGenerator._get_user_scope(db, 1)
            assert scope == "技术部"

    def test_department_not_found(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        q.all.return_value = []
        db.query.return_value = q

        result_users, scope = AnalysisReportGenerator._get_user_scope(db, 999)
        assert result_users == []


class TestCalculateWorkload:
    def test_empty(self):
        db = MagicMock()
        wl, summary = AnalysisReportGenerator._calculate_workload(db, [], [])
        assert wl == []
        assert summary == {"OVERLOAD": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    def test_load_levels(self):
        db = MagicMock()
        user_low = _mock_user(id=1, real_name="低")
        user_med = _mock_user(id=2, real_name="中")
        user_high = _mock_user(id=3, real_name="高")
        user_over = _mock_user(id=4, real_name="超")

        # LOW: <12 days = <96h, MED: 12-18 = 96-144h, HIGH: 18-22 = 144-176h, OVER: >22 = >176h
        timesheets = [
            _mock_timesheet(user_id=1, hours=40, project_id=1),   # 5 days -> LOW
            _mock_timesheet(user_id=2, hours=120, project_id=1),  # 15 days -> MEDIUM
            _mock_timesheet(user_id=3, hours=160, project_id=1),  # 20 days -> HIGH
            _mock_timesheet(user_id=4, hours=200, project_id=1),  # 25 days -> OVERLOAD
        ]

        wl, summary = AnalysisReportGenerator._calculate_workload(
            db, [user_low, user_med, user_high, user_over], timesheets
        )
        assert summary["LOW"] == 1
        assert summary["MEDIUM"] == 1
        assert summary["HIGH"] == 1
        assert summary["OVERLOAD"] == 1


class TestGetProjects:
    def test_specific_project(self):
        db = MagicMock()
        project = MagicMock(id=1)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [project]
        db.query.return_value = q

        result = AnalysisReportGenerator._get_projects(db, 1)
        assert len(result) == 1

    def test_all_active(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [MagicMock(), MagicMock()]
        db.query.return_value = q

        result = AnalysisReportGenerator._get_projects(db, None)
        assert len(result) == 2


class TestCalculateProjectCosts:
    def test_basic(self):
        db = MagicMock()
        project = MagicMock(id=1, project_name="P1", budget_amount=100000)

        ts = [_mock_timesheet(hours=80)]
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = ts
        db.query.return_value = q

        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            db, [project], date(2025, 1, 1), date(2025, 1, 31)
        )
        assert len(summaries) == 1
        assert total_budget == 100000
        assert total_actual == 80 * 100  # DEFAULT_HOURLY_RATE

    def test_no_budget(self):
        db = MagicMock()
        project = MagicMock(id=1, project_name="P1")
        project.budget_amount = None

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            db, [project], date(2025, 1, 1), date(2025, 1, 31)
        )
        assert total_budget == 0
        assert total_actual == 0

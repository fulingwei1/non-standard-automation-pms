# -*- coding: utf-8 -*-
"""
第四十五批覆盖：report_framework/generators/project.py
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

pytest.importorskip("app.services.report_framework.generators.project")

from unittest.mock import patch
from app.services.report_framework.generators.project import ProjectReportGenerator


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_project():
    p = MagicMock()
    p.id = 1
    p.project_name = "测试项目"
    p.project_code = "P-001"
    p.customer_name = "客户A"
    p.current_stage = "S3"
    p.health_status = "H1"
    p.progress = 50.0
    p.budget_amount = 100000
    return p


class TestProjectReportGeneratorWeekly:
    def test_generate_weekly_project_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = ProjectReportGenerator.generate_weekly(
            mock_db, 999, date(2024, 1, 1), date(2024, 1, 7)
        )
        assert "error" in result
        assert result["project_id"] == 999

    def test_generate_weekly_success(self, mock_db, mock_project):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(ProjectReportGenerator, "_get_milestone_data", return_value={"summary": {"total": 0, "completed": 0, "delayed": 0, "in_progress": 0}, "details": []}):
            result = ProjectReportGenerator.generate_weekly(
                mock_db, 1, date(2024, 1, 1), date(2024, 1, 7)
            )
        assert "summary" in result
        assert "milestones" in result
        assert "timesheet" in result
        assert result["summary"]["project_name"] == "测试项目"

    def test_generate_weekly_risks_for_h2(self, mock_db, mock_project):
        mock_project.health_status = "H2"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(ProjectReportGenerator, "_get_milestone_data", return_value={"summary": {"total": 0, "completed": 0, "delayed": 0, "in_progress": 0}, "details": []}):
            result = ProjectReportGenerator.generate_weekly(
                mock_db, 1, date(2024, 1, 1), date(2024, 1, 7)
            )
        assert len(result["risks"]) > 0
        assert any(r["type"] == "健康度" for r in result["risks"])


class TestProjectReportGeneratorMonthly:
    def test_generate_monthly_project_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = ProjectReportGenerator.generate_monthly(
            mock_db, 999, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert "error" in result

    def test_generate_monthly_success(self, mock_db, mock_project):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(ProjectReportGenerator, "_get_milestone_data", return_value={"summary": {"total": 0, "completed": 0, "delayed": 0, "in_progress": 0}, "details": []}):
            result = ProjectReportGenerator.generate_monthly(
                mock_db, 1, date(2024, 1, 1), date(2024, 1, 31)
            )
        assert "summary" in result
        assert result["summary"]["report_type"] == "月报"
        assert "cost" in result


class TestProjectReportGeneratorHelpers:
    def test_build_project_summary(self, mock_project):
        summary = ProjectReportGenerator._build_project_summary(
            mock_project, date(2024, 1, 1), date(2024, 1, 7)
        )
        assert summary["project_id"] == 1
        assert summary["project_name"] == "测试项目"
        assert summary["progress"] == 50.0

    def test_get_timesheet_data_empty(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        data = ProjectReportGenerator._get_timesheet_data(
            mock_db, 1, date(2024, 1, 1), date(2024, 1, 7)
        )
        assert data["total_hours"] == 0
        assert data["unique_workers"] == 0

    def test_get_cost_summary(self, mock_project):
        cost = ProjectReportGenerator._get_cost_summary(mock_project)
        assert cost["planned_cost"] == 100000.0

    def test_assess_risks_delayed_milestones(self, mock_project):
        summary = {"health_status": "H1"}
        milestones = {"summary": {"delayed": 2}}
        risks = ProjectReportGenerator._assess_risks(summary, milestones)
        assert any(r["type"] == "里程碑延期" for r in risks)
        assert risks[0]["level"] == "HIGH"

    def test_get_weekly_trend(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        trend = ProjectReportGenerator._get_weekly_trend(
            mock_db, 1, date(2024, 1, 1), date(2024, 1, 14)
        )
        assert len(trend) >= 2
        assert all("week" in t for t in trend)

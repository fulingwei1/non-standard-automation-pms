# -*- coding: utf-8 -*-
"""Tests for app.services.template_report.project_reports"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.template_report.project_reports import ProjectReportMixin


class TestGenerateProjectWeekly:
    @patch("app.services.template_report.project_reports.Machine")
    @patch("app.services.template_report.project_reports.Timesheet")
    @patch("app.services.template_report.project_reports.ProjectMilestone")
    @patch("app.services.template_report.project_reports.Project")
    def test_project_not_found(self, MockProj, *_):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = ProjectReportMixin._generate_project_weekly(
            db, 1, date(2025, 1, 1), date(2025, 1, 7), {}, {}
        )
        assert "error" in result

    @patch("app.services.template_report.project_reports.Machine")
    @patch("app.services.template_report.project_reports.Timesheet")
    @patch("app.services.template_report.project_reports.ProjectMilestone")
    @patch("app.services.template_report.project_reports.Project")
    def test_generates_report(self, MockProj, MockMilestone, MockTs, MockMachine):
        db = MagicMock()
        project = MagicMock()
        project.project_name = "测试项目"
        project.progress = 50
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = []

        result = ProjectReportMixin._generate_project_weekly(
            db, 1, date(2025, 1, 1), date(2025, 1, 7), {}, {}
        )
        assert "summary" in result
        assert "sections" in result
        assert "metrics" in result


class TestGenerateProjectMonthly:
    @patch("app.services.template_report.project_reports.Machine")
    @patch("app.services.template_report.project_reports.Timesheet")
    @patch("app.services.template_report.project_reports.ProjectMilestone")
    @patch("app.services.template_report.project_reports.Project")
    def test_includes_weekly_trend(self, MockProj, MockMilestone, MockTs, MockMachine):
        db = MagicMock()
        project = MagicMock()
        project.project_name = "测试项目"
        project.progress = 50
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = []

        result = ProjectReportMixin._generate_project_monthly(
            db, 1, date(2025, 1, 1), date(2025, 1, 31), {}, {}
        )
        assert "weekly_trend" in result["sections"]

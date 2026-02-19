# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/generators/project.py"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.generators.project import ProjectReportGenerator
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)

_GEN = "app.services.report_framework.generators.project.ProjectReportGenerator"


def _make_db(project=None):
    db = MagicMock()
    mock_q = MagicMock()
    db.query.return_value = mock_q
    mock_q.filter.return_value = mock_q
    mock_q.first.return_value = project
    mock_q.all.return_value = []
    return db


def test_generate_weekly_project_not_found():
    db = _make_db(project=None)
    result = ProjectReportGenerator.generate_weekly(db, 999, date(2025, 1, 1), date(2025, 1, 7))
    assert "error" in result
    assert result["project_id"] == 999


def test_generate_weekly_returns_keys():
    project = MagicMock()
    project.id = 1
    project.project_name = "测试项目"
    project.progress = 50
    db = _make_db(project=project)
    dummy_summary = {"project_id": 1, "health_status": "H1"}
    dummy_milestones = {"summary": {"delayed": 0}}
    with patch.object(ProjectReportGenerator, "_build_project_summary", return_value=dummy_summary), \
         patch.object(ProjectReportGenerator, "_get_milestone_data", return_value=dummy_milestones), \
         patch.object(ProjectReportGenerator, "_get_timesheet_data", return_value={"total_hours": 0}), \
         patch.object(ProjectReportGenerator, "_get_machine_data", return_value=[]):
        result = ProjectReportGenerator.generate_weekly(db, 1, date(2025, 1, 1), date(2025, 1, 7))
    assert "summary" in result
    assert "milestones" in result
    assert "timesheet" in result
    assert "machines" in result
    assert "risks" in result


def test_generate_monthly_project_not_found():
    db = _make_db(project=None)
    result = ProjectReportGenerator.generate_monthly(db, 99, date(2025, 1, 1), date(2025, 1, 31))
    assert "error" in result


def test_generate_monthly_returns_keys():
    project = MagicMock()
    project.id = 2
    project.project_name = "月报项目"
    project.progress = 30
    db = _make_db(project=project)
    dummy_summary = {"project_id": 2, "health_status": "H1"}
    dummy_milestones = {"summary": {"delayed": 0}}
    with patch.object(ProjectReportGenerator, "_build_project_summary", return_value=dummy_summary), \
         patch.object(ProjectReportGenerator, "_get_milestone_data", return_value=dummy_milestones), \
         patch.object(ProjectReportGenerator, "_get_weekly_trend", return_value=[]), \
         patch.object(ProjectReportGenerator, "_get_cost_summary", return_value={"planned_cost": 0}):
        result = ProjectReportGenerator.generate_monthly(db, 2, date(2025, 1, 1), date(2025, 1, 31))
    assert "summary" in result
    assert result["summary"]["report_type"] == "月报"
    assert "progress_trend" in result
    assert "cost" in result


def test_build_project_summary():
    project = MagicMock()
    project.id = 5
    project.project_name = "P5"
    project.progress = 75
    summary = ProjectReportGenerator._build_project_summary(project, date(2025, 2, 1), date(2025, 2, 7))
    assert summary["project_id"] == 5
    assert summary["project_name"] == "P5"
    assert summary["progress"] == 75.0
    assert summary["period_start"] == "2025-02-01"
    assert summary["period_end"] == "2025-02-07"


def test_assess_risks_h3_and_delayed():
    summary = {"health_status": "H3"}
    milestones = {"summary": {"delayed": 2}}
    risks = ProjectReportGenerator._assess_risks(summary, milestones)
    assert any(r["level"] == "HIGH" for r in risks)
    assert len(risks) == 2


def test_assess_risks_h1_no_delay():
    summary = {"health_status": "H1"}
    milestones = {"summary": {"delayed": 0}}
    risks = ProjectReportGenerator._assess_risks(summary, milestones)
    assert risks == []


def test_get_timesheet_data():
    db = MagicMock()
    ts1 = MagicMock()
    ts1.hours = 8
    ts1.user_id = 1
    ts2 = MagicMock()
    ts2.hours = 4
    ts2.user_id = 2
    db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
    result = ProjectReportGenerator._get_timesheet_data(db, 1, date(2025, 1, 1), date(2025, 1, 7))
    assert result["total_hours"] == 12.0
    assert result["unique_workers"] == 2

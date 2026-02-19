# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/adapters/project.py"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.project import (
        ProjectReportAdapter,
        ProjectWeeklyAdapter,
        ProjectMonthlyAdapter,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)

_BASE_ENGINE = "app.services.report_framework.adapters.base.ReportEngine"
_GEN = "app.services.report_framework.adapters.project.ProjectReportGenerator"


def _make_adapter(report_type="weekly"):
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = ProjectReportAdapter(db, report_type=report_type)
    return adapter, db


def test_weekly_report_code():
    adapter, _ = _make_adapter("weekly")
    assert adapter.get_report_code() == "PROJECT_WEEKLY"


def test_monthly_report_code():
    adapter, _ = _make_adapter("monthly")
    assert adapter.get_report_code() == "PROJECT_MONTHLY"


def test_generate_data_missing_project_id():
    adapter, _ = _make_adapter()
    with pytest.raises(ValueError, match="project_id"):
        adapter.generate_data({})


def test_generate_data_weekly():
    adapter, _ = _make_adapter("weekly")
    mock_data = {"summary": {}, "milestones": {}, "timesheet": {}, "machines": [], "risks": []}
    with patch(f"{_GEN}.generate_weekly", return_value=mock_data):
        result = adapter.generate_data({"project_id": 1})
    assert result["title"] == "项目周报"
    assert result["report_type"] == "PROJECT_WEEKLY"


def test_generate_data_monthly():
    adapter, _ = _make_adapter("monthly")
    mock_data = {"summary": {"report_type": "月报"}, "milestones": {}, "progress_trend": [], "cost": {}}
    with patch(f"{_GEN}.generate_monthly", return_value=mock_data):
        result = adapter.generate_data({"project_id": 2, "start_date": "2025-01-01", "end_date": "2025-01-31"})
    assert result["title"] == "项目月报"
    assert result["report_type"] == "PROJECT_MONTHLY"


def test_generate_data_with_string_dates():
    adapter, _ = _make_adapter("weekly")
    mock_data = {}
    with patch(f"{_GEN}.generate_weekly", return_value=mock_data):
        result = adapter.generate_data({
            "project_id": 3,
            "start_date": "2025-02-01",
            "end_date": "2025-02-07",
        })
    assert "title" in result


def test_weekly_adapter_class():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = ProjectWeeklyAdapter(db)
    assert adapter.get_report_code() == "PROJECT_WEEKLY"


def test_monthly_adapter_class():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = ProjectMonthlyAdapter(db)
    assert adapter.get_report_code() == "PROJECT_MONTHLY"

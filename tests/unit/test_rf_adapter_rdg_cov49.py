# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/adapters/report_data_generation.py"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.report_data_generation import (
        ReportDataGenerationAdapter
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)

_BASE_ENGINE = "app.services.report_framework.adapters.base.ReportEngine"


def _make_adapter(report_type="PROJECT_WEEKLY"):
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = ReportDataGenerationAdapter(db, report_type=report_type)
    return adapter, db


def test_get_report_code_known_type():
    adapter, _ = _make_adapter("PROJECT_WEEKLY")
    assert adapter.get_report_code() == "PROJECT_WEEKLY"


def test_get_report_code_unknown_type():
    adapter, _ = _make_adapter("CUSTOM_REPORT")
    assert adapter.get_report_code() == "CUSTOM_REPORT"


def test_get_report_title_project_weekly():
    adapter, _ = _make_adapter("PROJECT_WEEKLY")
    assert adapter._get_report_title() == "项目周报"


def test_get_report_title_dept_monthly():
    adapter, _ = _make_adapter("DEPT_MONTHLY")
    assert adapter._get_report_title() == "部门月报"


def test_get_report_title_unknown():
    adapter, _ = _make_adapter("UNKNOWN_TYPE")
    assert "UNKNOWN_TYPE" in adapter._get_report_title()


def test_generate_data_success():
    adapter, _ = _make_adapter("PROJECT_WEEKLY")
    mock_data = {"summary": {}, "milestones": {}}
    with patch("app.services.report_data_generation.router.ReportRouterMixin.generate_report_by_type",
               return_value=mock_data):
        result = adapter.generate_data({
            "project_id": 1,
            "start_date": "2025-01-01",
            "end_date": "2025-01-07",
        })
    assert result["report_type"] == "PROJECT_WEEKLY"
    assert result["title"] == "项目周报"


def test_generate_data_error_in_data():
    adapter, _ = _make_adapter("PROJECT_WEEKLY")
    with patch("app.services.report_data_generation.router.ReportRouterMixin.generate_report_by_type",
               return_value={"error": "项目不存在"}):
        with pytest.raises(ValueError, match="项目不存在"):
            adapter.generate_data({"project_id": 999})


def test_report_type_map_has_all_keys():
    adapter, _ = _make_adapter()
    for key in ["PROJECT_WEEKLY", "PROJECT_MONTHLY", "DEPT_WEEKLY", "DEPT_MONTHLY", "WORKLOAD_ANALYSIS", "COST_ANALYSIS"]:
        assert key in ReportDataGenerationAdapter.REPORT_TYPE_MAP

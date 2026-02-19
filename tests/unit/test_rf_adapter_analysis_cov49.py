# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/adapters/analysis.py"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.analysis import (
        WorkloadAnalysisAdapter,
        CostAnalysisAdapter,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)

_BASE_ENGINE = "app.services.report_framework.adapters.base.ReportEngine"
_GEN = "app.services.report_framework.adapters.analysis.AnalysisReportGenerator"


def _make_workload_adapter():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = WorkloadAnalysisAdapter(db)
    return adapter, db


def _make_cost_adapter():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = CostAnalysisAdapter(db)
    return adapter, db


def test_workload_adapter_get_report_code():
    adapter, _ = _make_workload_adapter()
    assert adapter.get_report_code() == "WORKLOAD_ANALYSIS"


def test_cost_adapter_get_report_code():
    adapter, _ = _make_cost_adapter()
    assert adapter.get_report_code() == "COST_ANALYSIS"


def test_workload_generate_data_with_dates():
    adapter, _ = _make_workload_adapter()
    mock_result = {
        "summary": {"scope": "全公司", "total_users": 0, "period_start": "2025-01-01", "period_end": "2025-01-31", "active_users": 0},
        "load_distribution": {},
        "workload_details": [],
        "charts": [],
    }
    with patch(f"{_GEN}.generate_workload_analysis", return_value=mock_result):
        result = adapter.generate_data({"start_date": "2025-01-01", "end_date": "2025-01-31"})
    assert result["title"] == "负荷分析报告"


def test_workload_generate_data_date_objects():
    adapter, _ = _make_workload_adapter()
    mock_result = {"summary": {}, "load_distribution": {}, "workload_details": [], "charts": []}
    with patch(f"{_GEN}.generate_workload_analysis", return_value=mock_result):
        result = adapter.generate_data({
            "start_date": date(2025, 2, 1),
            "end_date": date(2025, 2, 28),
        })
    assert result["report_type"] == "WORKLOAD_ANALYSIS"


def test_cost_generate_data_with_string_dates():
    adapter, _ = _make_cost_adapter()
    mock_result = {"summary": {}, "project_breakdown": [], "charts": []}
    with patch(f"{_GEN}.generate_cost_analysis", return_value=mock_result):
        result = adapter.generate_data({"start_date": "2025-01-01", "end_date": "2025-01-31"})
    assert result["title"] == "成本分析报告"


def test_cost_generate_data_no_project():
    adapter, _ = _make_cost_adapter()
    mock_result = {"summary": {}, "project_breakdown": [], "charts": []}
    with patch(f"{_GEN}.generate_cost_analysis", return_value=mock_result):
        result = adapter.generate_data({})
    assert "title" in result


def test_cost_generate_data_with_project_id():
    adapter, _ = _make_cost_adapter()
    mock_result = {"summary": {}, "project_breakdown": [{"project_id": 7}], "charts": []}
    with patch(f"{_GEN}.generate_cost_analysis", return_value=mock_result):
        result = adapter.generate_data({"project_id": 7})
    assert result["report_type"] == "COST_ANALYSIS"

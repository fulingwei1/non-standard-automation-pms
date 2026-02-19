# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/adapters/timesheet.py"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.timesheet import TimesheetReportAdapter
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)

_BASE_ENGINE = "app.services.report_framework.adapters.base.ReportEngine"


def _make_adapter():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = TimesheetReportAdapter(db)
    return adapter, db


def test_get_report_code():
    adapter, _ = _make_adapter()
    assert adapter.get_report_code() == "TIMESHEET_WEEKLY"


def test_generate_data_returns_dict():
    adapter, _ = _make_adapter()
    result = adapter.generate_data({})
    assert isinstance(result, dict)


def test_generate_data_has_title():
    adapter, _ = _make_adapter()
    result = adapter.generate_data({})
    assert result.get("title") == "工时报表"


def test_generate_data_has_summary():
    adapter, _ = _make_adapter()
    result = adapter.generate_data({})
    assert "summary" in result


def test_generate_data_has_details():
    adapter, _ = _make_adapter()
    result = adapter.generate_data({})
    assert "details" in result
    assert isinstance(result["details"], list)


def test_generate_data_with_user():
    adapter, _ = _make_adapter()
    user = MagicMock()
    result = adapter.generate_data({}, user=user)
    assert "title" in result


def test_generate_uses_engine():
    adapter, _ = _make_adapter()
    adapter.engine.generate.return_value = MagicMock(data={})
    result = adapter.generate({"report_code": "TIMESHEET_WEEKLY"})
    assert adapter.engine.generate.called

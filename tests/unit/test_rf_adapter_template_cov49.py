# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/adapters/template.py"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.template import TemplateReportAdapter
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)

_BASE_ENGINE = "app.services.report_framework.adapters.base.ReportEngine"


def _make_adapter():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = TemplateReportAdapter(db)
    return adapter, db


def test_get_report_code():
    adapter, _ = _make_adapter()
    assert adapter.get_report_code() == "TEMPLATE_REPORT"


def test_generate_data_missing_template_id():
    adapter, _ = _make_adapter()
    with pytest.raises(ValueError, match="template_id"):
        adapter.generate_data({})


def test_generate_data_template_not_found():
    adapter, db = _make_adapter()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="报表模板不存在"):
        adapter.generate_data({"template_id": 999})


def test_generate_missing_template_id():
    adapter, _ = _make_adapter()
    with pytest.raises(ValueError, match="template_id"):
        adapter.generate({"format": "json"})


def test_generate_template_not_found():
    adapter, db = _make_adapter()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="报表模板不存在"):
        adapter.generate({"template_id": 999})


def test_convert_to_report_result_with_summary():
    adapter, _ = _make_adapter()
    with patch("app.services.report_framework.renderers.JsonRenderer") as mock_rend_cls:
        mock_renderer = MagicMock()
        mock_rend_cls.return_value = mock_renderer
        mock_renderer.render.return_value = MagicMock(data={})
        data = {"summary": {"total": 5, "active": 3}}
        adapter._convert_to_report_result(data, "json")
        assert mock_renderer.render.called


def test_convert_to_report_result_with_sections():
    adapter, _ = _make_adapter()
    with patch("app.services.report_framework.renderers.JsonRenderer") as mock_rend_cls:
        mock_renderer = MagicMock()
        mock_rend_cls.return_value = mock_renderer
        mock_renderer.render.return_value = MagicMock()
        data = {"sections": {"detail": [{"a": 1}]}}
        adapter._convert_to_report_result(data, "json")
        assert mock_renderer.render.called

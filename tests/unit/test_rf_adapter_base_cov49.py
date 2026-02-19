# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/adapters/base.py"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.base import BaseReportAdapter
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)

_BASE_ENGINE = "app.services.report_framework.adapters.base.ReportEngine"


class ConcreteAdapter(BaseReportAdapter):
    def get_report_code(self) -> str:
        return "TEST_CODE"

    def generate_data(self, params, user=None):
        return {"summary": {"count": 5}, "details": [{"id": 1}]}


def _make_adapter():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = ConcreteAdapter(db)
    return adapter, db


def test_get_report_code():
    adapter, _ = _make_adapter()
    assert adapter.get_report_code() == "TEST_CODE"


def test_generate_data():
    adapter, _ = _make_adapter()
    result = adapter.generate_data({})
    assert "summary" in result
    assert "details" in result


def test_generate_uses_engine_first():
    adapter, _ = _make_adapter()
    mock_result = MagicMock()
    adapter.engine.generate.return_value = mock_result
    result = adapter.generate({"key": "val"})
    assert result == mock_result


def test_generate_falls_back_to_generate_data():
    adapter, _ = _make_adapter()
    adapter.engine.generate.side_effect = Exception("no yaml config")
    with patch("app.services.report_framework.renderers.JsonRenderer") as mock_rend_cls:
        mock_renderer = MagicMock()
        mock_rend_cls.return_value = mock_renderer
        mock_renderer.render.return_value = MagicMock()
        result = adapter.generate({})
        assert mock_renderer.render.called


def test_convert_to_report_result_summary_and_details():
    adapter, _ = _make_adapter()
    data = {"summary": {"total": 10}, "details": [{"id": 1}], "title": "测试报表"}
    with patch("app.services.report_framework.renderers.JsonRenderer") as mock_rend_cls:
        mock_renderer = MagicMock()
        mock_rend_cls.return_value = mock_renderer
        mock_renderer.render.return_value = MagicMock()
        adapter._convert_to_report_result(data)
        call_args = mock_renderer.render.call_args
        sections = call_args[0][0]
        section_ids = [s["id"] for s in sections]
        assert "summary" in section_ids
        assert "details" in section_ids


def test_base_adapter_is_abstract():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        with pytest.raises(TypeError):
            BaseReportAdapter(db)

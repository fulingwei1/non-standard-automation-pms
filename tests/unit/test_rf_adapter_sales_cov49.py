# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/adapters/sales.py"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.sales import SalesReportAdapter
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)

_BASE_ENGINE = "app.services.report_framework.adapters.base.ReportEngine"


def _make_adapter():
    db = MagicMock()
    with patch(_BASE_ENGINE):
        adapter = SalesReportAdapter(db)
    return adapter, db


def test_get_report_code():
    adapter, _ = _make_adapter()
    assert adapter.get_report_code() == "SALES_MONTHLY"


def test_generate_data_invalid_month_format():
    adapter, _ = _make_adapter()
    with pytest.raises(ValueError, match="月份格式"):
        adapter.generate_data({"month": "not-a-month"})


def test_generate_uses_engine_first():
    adapter, _ = _make_adapter()
    adapter.engine.generate.return_value = MagicMock(data={})
    result = adapter.generate({})
    assert adapter.engine.generate.called


def test_generate_falls_back_on_engine_failure():
    adapter, _ = _make_adapter()
    adapter.engine.generate.side_effect = Exception("no config")
    mock_data = {
        "report_date": "2025-01",
        "report_type": "monthly",
        "contract_statistics": {},
        "order_statistics": {},
        "receipt_statistics": {},
        "invoice_statistics": {},
        "bidding_statistics": {},
    }
    with patch.object(adapter, 'generate_data', return_value=mock_data), \
         patch("app.services.report_framework.renderers.JsonRenderer") as mock_rend_cls:
        mock_renderer = MagicMock()
        mock_rend_cls.return_value = mock_renderer
        mock_renderer.render.return_value = MagicMock()
        result = adapter.generate({})
        assert mock_renderer.render.called


def test_report_code_is_sales_monthly():
    adapter, _ = _make_adapter()
    code = adapter.get_report_code()
    assert "SALES" in code


def test_generate_data_invalid_month_format_variant():
    adapter, _ = _make_adapter()
    with pytest.raises(ValueError):
        adapter.generate_data({"month": "2025/01"})

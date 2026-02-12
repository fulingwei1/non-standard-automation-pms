# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/renderers/excel_renderer.py"""
from unittest.mock import MagicMock

from app.services.report_framework.renderers.excel_renderer import ExcelRenderer


class TestExcelRenderer:
    def test_format_name(self):
        renderer = ExcelRenderer.__new__(ExcelRenderer)
        assert renderer.format_name == "excel"

    def test_content_type(self):
        renderer = ExcelRenderer.__new__(ExcelRenderer)
        assert "spreadsheet" in renderer.content_type or "excel" in renderer.content_type.lower()

# -*- coding: utf-8 -*-
"""第十八批 - Excel导出服务单元测试"""
import io
import sys
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.services.excel_export_service import ExcelExportService, create_excel_response
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture
def service():
    with patch.dict("sys.modules", {
        "openpyxl": MagicMock(),
        "pandas": MagicMock(),
    }):
        with patch("app.services.excel_export_service.EXCEL_AVAILABLE", True):
            svc = ExcelExportService.__new__(ExcelExportService)
            return svc


class TestExcelExportService:
    def test_format_currency_normal(self, service):
        result = service.format_currency(1234567.89)
        assert "1,234,567.89" in result

    def test_format_currency_none(self, service):
        assert service.format_currency(None) == "0.00"

    def test_format_currency_empty_string(self, service):
        assert service.format_currency("") == "0.00"

    def test_format_currency_string_value(self, service):
        result = service.format_currency("9999.5")
        assert "9,999.50" in result

    def test_format_percentage_normal(self, service):
        result = service.format_percentage(85.5)
        assert "85.50%" in result

    def test_format_percentage_none(self, service):
        assert service.format_percentage(None) == "0.00%"

    def test_format_date_datetime(self, service):
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = service.format_date(dt)
        assert "2024-01-15" in result

    def test_format_date_date(self, service):
        d = date(2024, 3, 20)
        result = service.format_date(d)
        assert result == "2024-03-20"

    def test_format_date_none(self, service):
        assert service.format_date(None) == ""

    def test_import_error_raises(self):
        with patch("app.services.excel_export_service.EXCEL_AVAILABLE", False):
            with pytest.raises(ImportError):
                ExcelExportService()

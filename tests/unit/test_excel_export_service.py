# -*- coding: utf-8 -*-
"""Excel导出服务测试"""
import io
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.excel_export_service import ExcelExportService, create_excel_response


@pytest.fixture
def service():
    return ExcelExportService()


class TestExportToExcel:
    def test_empty_data(self, service):
        result = service.export_to_excel([])
        assert isinstance(result, io.BytesIO)

    def test_with_data(self, service):
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = service.export_to_excel(data)
        assert isinstance(result, io.BytesIO)
        assert result.tell() == 0

    def test_with_columns(self, service):
        data = [{"name": "Alice", "score": 95.5}]
        columns = [
            {"key": "name", "label": "姓名", "width": 20},
            {"key": "score", "label": "分数", "width": 15}
        ]
        result = service.export_to_excel(data, columns=columns, title="Test")
        assert isinstance(result, io.BytesIO)

    def test_with_special_types(self, service):
        data = [{
            "date_val": date(2026, 1, 1),
            "dt_val": datetime(2026, 1, 1, 12, 0),
            "dec_val": Decimal("100.50"),
            "none_val": None
        }]
        result = service.export_to_excel(data)
        assert isinstance(result, io.BytesIO)

    def test_with_format_function(self, service):
        data = [{"amount": 1000}]
        columns = [{"key": "amount", "label": "金额", "format": lambda x: f"¥{x}"}]
        result = service.export_to_excel(data, columns=columns)
        assert isinstance(result, io.BytesIO)


class TestExportMultisheet:
    def test_empty_sheets(self, service):
        result = service.export_multisheet([{"name": "Sheet1", "data": []}])
        assert isinstance(result, io.BytesIO)

    def test_with_data(self, service):
        sheets = [
            {
                "name": "Sheet1",
                "data": [{"a": 1, "b": 2}],
                "title": "Test Sheet"
            },
            {
                "name": "Sheet2",
                "data": [{"c": 3}],
                "columns": [{"key": "c", "label": "Col C", "width": 10}]
            }
        ]
        result = service.export_multisheet(sheets)
        assert isinstance(result, io.BytesIO)


class TestFormatters:
    def test_format_currency(self, service):
        assert service.format_currency(1000) == "1,000.00"
        assert service.format_currency(None) == "0.00"
        assert service.format_currency("abc") == "abc"

    def test_format_percentage(self, service):
        assert service.format_percentage(85.5) == "85.50%"
        assert service.format_percentage(None) == "0.00%"

    def test_format_date(self, service):
        assert service.format_date(date(2026, 1, 1)) == "2026-01-01"
        assert service.format_date(datetime(2026, 1, 1, 12, 0)) == "2026-01-01 12:00:00"
        assert service.format_date(None) == ""
        assert service.format_date("2026-01-01") == "2026-01-01"


class TestCreateExcelResponse:
    def test_response(self):
        data = io.BytesIO(b"test")
        response = create_excel_response(data, "test.xlsx")
        assert response is not None

# -*- coding: utf-8 -*-
"""
Tests for excel_export_service service
Covers: app/services/excel_export_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 160 lines
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from app.services.excel_export_service import ExcelExportService, create_excel_response


class TestExcelExportService:
    """Test suite for ExcelExportService."""

    def test_init_with_libraries(self):
        """测试初始化 - 有Excel库"""
        try:
            service = ExcelExportService()
            assert service is not None
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_to_excel_empty_data(self):
        """测试导出Excel - 空数据"""
        try:
            service = ExcelExportService()
            result = service.export_to_excel([], sheet_name="Empty")

            assert isinstance(result, BytesIO)
            assert len(result.getvalue()) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_to_excel_basic(self):
        """测试导出Excel - 基本功能"""
        try:
            service = ExcelExportService()
            data = [
                {"id": 1, "name": "测试1", "value": 100},
                {"id": 2, "name": "测试2", "value": 200},
            ]

            result = service.export_to_excel(data)

            assert isinstance(result, BytesIO)
            content = result.getvalue()
            assert len(content) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_to_excel_with_columns(self):
        """测试导出Excel - 指定列"""
        try:
            service = ExcelExportService()
            data = [
                {"id": 1, "name": "测试1", "value": 100},
            ]
            columns = [
                {"key": "id", "label": "ID", "width": 10},
                {"key": "name", "label": "名称", "width": 20},
            ]

            result = service.export_to_excel(data, columns=columns)

            assert isinstance(result, BytesIO)
            content = result.getvalue()
            assert len(content) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_to_excel_with_title(self):
        """测试导出Excel - 带标题"""
        try:
            service = ExcelExportService()
            data = [{"id": 1, "name": "测试"}]

            result = service.export_to_excel(data, title="测试报表")

            assert isinstance(result, BytesIO)
            assert len(result.getvalue()) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_to_excel_with_date(self):
        """测试导出Excel - 日期类型"""
        try:
            service = ExcelExportService()
            data = [
                {"id": 1, "date": date.today()},
                {"id": 2, "date": datetime.now()},
            ]

            result = service.export_to_excel(data)

            assert isinstance(result, BytesIO)
            assert len(result.getvalue()) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_to_excel_with_decimal(self):
        """测试导出Excel - Decimal类型"""
        try:
            service = ExcelExportService()
            data = [
                {"id": 1, "amount": Decimal("100.50")},
            ]

            result = service.export_to_excel(data)

            assert isinstance(result, BytesIO)
            assert len(result.getvalue()) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_to_excel_with_format(self):
        """测试导出Excel - 格式化函数"""
        try:
            service = ExcelExportService()
            data = [{"id": 1, "value": 100}]
            columns = [
                {
                    "key": "value",
                    "label": "值",
                    "format": lambda x: f"¥{x}" if x else ""
                }
            ]

            result = service.export_to_excel(data, columns=columns)

            assert isinstance(result, BytesIO)
            assert len(result.getvalue()) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_multisheet(self):
        """测试导出多Sheet Excel"""
        try:
            service = ExcelExportService()
            sheets = [
                {
                    "name": "Sheet1",
                    "data": [{"id": 1, "name": "测试1"}],
                },
                {
                    "name": "Sheet2",
                    "data": [{"id": 2, "name": "测试2"}],
                },
            ]

            result = service.export_multisheet(sheets)

            assert isinstance(result, BytesIO)
            content = result.getvalue()
            assert len(content) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_multisheet_with_title(self):
        """测试导出多Sheet Excel - 带标题"""
        try:
            service = ExcelExportService()
            sheets = [
                {
                    "name": "Sheet1",
                    "data": [{"id": 1}],
                    "title": "报表1",
                },
            ]

            result = service.export_multisheet(sheets)

            assert isinstance(result, BytesIO)
            assert len(result.getvalue()) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_format_currency(self):
        """测试格式化货币"""
        try:
            service = ExcelExportService()

            assert service.format_currency(100.50) == "100.50"
            assert service.format_currency(1000) == "1,000.00"
            assert service.format_currency(None) == "0.00"
            assert service.format_currency("") == "0.00"
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_format_percentage(self):
        """测试格式化百分比"""
        try:
            service = ExcelExportService()

            assert service.format_percentage(50) == "50.00%"
            assert service.format_percentage(0.5) == "0.50%"
            assert service.format_percentage(None) == "0.00%"
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_format_date(self):
        """测试格式化日期"""
        try:
            service = ExcelExportService()

            assert service.format_date(date.today()) == date.today().strftime('%Y-%m-%d')
            test_datetime = datetime.now()
            assert service.format_date(test_datetime) == test_datetime.strftime('%Y-%m-%d %H:%M:%S')
            assert service.format_date(None) == ""
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_create_excel_response(self):
        """测试创建Excel响应"""
        try:
            service = ExcelExportService()
            data = [{"id": 1, "name": "测试"}]
            excel_data = service.export_to_excel(data)

            response = create_excel_response(excel_data, "test.xlsx")

            assert response is not None
            assert hasattr(response, 'headers')
            assert 'Content-Disposition' in response.headers
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_to_excel_no_styles(self):
        """测试导出Excel - 不应用样式"""
        try:
            service = ExcelExportService()
            data = [{"id": 1, "name": "测试"}]

            result = service.export_to_excel(data, apply_styles=False)

            assert isinstance(result, BytesIO)
            assert len(result.getvalue()) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

    def test_export_multisheet_empty_sheet(self):
        """测试导出多Sheet Excel - 空Sheet"""
        try:
            service = ExcelExportService()
            sheets = [
                {
                    "name": "EmptySheet",
                    "data": [],
                    "title": "空报表",
                },
            ]

            result = service.export_multisheet(sheets)

            assert isinstance(result, BytesIO)
            assert len(result.getvalue()) > 0
        except ImportError:
            pytest.skip("Excel libraries not available")

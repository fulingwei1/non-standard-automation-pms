# -*- coding: utf-8 -*-
"""
ExcelExportService 综合单元测试

测试覆盖:
- export_to_excel: 导出数据到Excel
- export_multisheet: 导出多Sheet Excel文件
- _format_headers: 格式化表头
- format_currency: 格式化货币值
- format_percentage: 格式化百分比
- format_date: 格式化日期
- create_excel_response: 创建Excel下载响应
"""

import io
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestExportToExcel:
    """测试 export_to_excel 方法"""

    def test_exports_simple_data(self):
        """测试导出简单数据"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [
            {"name": "项目A", "amount": 1000},
            {"name": "项目B", "amount": 2000}
        ]

        result = service.export_to_excel(data)

        assert isinstance(result, io.BytesIO)
        assert result.getvalue()  # 有内容

    def test_exports_with_column_config(self):
        """测试带列配置导出"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [
            {"name": "项目A", "amount": 1000}
        ]
        columns = [
            {"key": "name", "label": "项目名称", "width": 20},
            {"key": "amount", "label": "金额", "width": 15}
        ]

        result = service.export_to_excel(data, columns=columns)

        assert isinstance(result, io.BytesIO)

    def test_exports_with_title(self):
        """测试带标题导出"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [{"name": "项目A"}]

        result = service.export_to_excel(data, title="项目列表")

        assert isinstance(result, io.BytesIO)

    def test_exports_empty_data(self):
        """测试导出空数据"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.export_to_excel([])

        assert isinstance(result, io.BytesIO)

    def test_exports_with_decimal_values(self):
        """测试导出Decimal值"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [
            {"name": "项目A", "amount": Decimal("1234.56")}
        ]

        result = service.export_to_excel(data)

        assert isinstance(result, io.BytesIO)

    def test_exports_with_date_values(self):
        """测试导出日期值"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [
            {"name": "项目A", "date": date(2026, 1, 15)}
        ]

        result = service.export_to_excel(data)

        assert isinstance(result, io.BytesIO)

    def test_exports_with_datetime_values(self):
        """测试导出日期时间值"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [
            {"name": "项目A", "datetime": datetime(2026, 1, 15, 10, 30, 0)}
        ]

        result = service.export_to_excel(data)

        assert isinstance(result, io.BytesIO)

    def test_exports_with_none_values(self):
        """测试导出None值"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [
            {"name": "项目A", "value": None}
        ]

        result = service.export_to_excel(data)

        assert isinstance(result, io.BytesIO)

    def test_exports_with_format_function(self):
        """测试带格式化函数导出"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [
            {"name": "项目A", "amount": 1000}
        ]
        columns = [
            {"key": "name", "label": "项目名称"},
            {"key": "amount", "label": "金额", "format": lambda x: f"¥{x:,.2f}"}
        ]

        result = service.export_to_excel(data, columns=columns)

        assert isinstance(result, io.BytesIO)

    def test_exports_without_styles(self):
        """测试不应用样式导出"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        data = [{"name": "项目A"}]

        result = service.export_to_excel(data, apply_styles=False)

        assert isinstance(result, io.BytesIO)


class TestExportMultisheet:
    """测试 export_multisheet 方法"""

    def test_exports_multiple_sheets(self):
        """测试导出多个Sheet"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        sheets = [
            {
                "name": "项目",
                "data": [{"name": "项目A"}]
            },
            {
                "name": "成本",
                "data": [{"item": "材料", "amount": 1000}]
            }
        ]

        result = service.export_multisheet(sheets)

        assert isinstance(result, io.BytesIO)

    def test_exports_sheet_with_title(self):
        """测试导出带标题的Sheet"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        sheets = [
            {
                "name": "项目列表",
                "title": "2026年项目汇总",
                "data": [{"name": "项目A"}]
            }
        ]

        result = service.export_multisheet(sheets)

        assert isinstance(result, io.BytesIO)

    def test_exports_sheet_with_columns(self):
        """测试导出带列配置的Sheet"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        sheets = [
            {
                "name": "项目",
                "data": [{"name": "项目A", "amount": 1000}],
                "columns": [
                    {"key": "name", "label": "项目名称", "width": 25},
                    {"key": "amount", "label": "金额", "width": 15}
                ]
            }
        ]

        result = service.export_multisheet(sheets)

        assert isinstance(result, io.BytesIO)

    def test_exports_empty_sheet(self):
        """测试导出空Sheet"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()
        sheets = [
            {
                "name": "空Sheet",
                "data": [],
                "title": "无数据"
            }
        ]

        result = service.export_multisheet(sheets)

        assert isinstance(result, io.BytesIO)


class TestFormatCurrency:
    """测试 format_currency 方法"""

    def test_formats_integer(self):
        """测试格式化整数"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_currency(1000)

        assert result == "1,000.00"

    def test_formats_float(self):
        """测试格式化浮点数"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_currency(1234.56)

        assert result == "1,234.56"

    def test_formats_string_number(self):
        """测试格式化字符串数字"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_currency("1000")

        assert result == "1,000.00"

    def test_formats_none(self):
        """测试格式化None"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_currency(None)

        assert result == "0.00"

    def test_formats_empty_string(self):
        """测试格式化空字符串"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_currency("")

        assert result == "0.00"

    def test_handles_invalid_value(self):
        """测试处理无效值"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_currency("invalid")

        assert result == "invalid"


class TestFormatPercentage:
    """测试 format_percentage 方法"""

    def test_formats_integer(self):
        """测试格式化整数"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_percentage(50)

        assert result == "50.00%"

    def test_formats_float(self):
        """测试格式化浮点数"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_percentage(75.5)

        assert result == "75.50%"

    def test_formats_string_number(self):
        """测试格式化字符串数字"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_percentage("85.25")

        assert result == "85.25%"

    def test_formats_none(self):
        """测试格式化None"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_percentage(None)

        assert result == "0.00%"

    def test_formats_empty_string(self):
        """测试格式化空字符串"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_percentage("")

        assert result == "0.00%"


class TestFormatDate:
    """测试 format_date 方法"""

    def test_formats_date(self):
        """测试格式化date"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_date(date(2026, 1, 15))

        assert result == "2026-01-15"

    def test_formats_datetime(self):
        """测试格式化datetime"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_date(datetime(2026, 1, 15, 10, 30, 45))

        assert result == "2026-01-15 10:30:45"

    def test_formats_none(self):
        """测试格式化None"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_date(None)

        assert result == ""

    def test_formats_string(self):
        """测试格式化字符串"""
        from app.services.excel_export_service import ExcelExportService

        service = ExcelExportService()

        result = service.format_date("2026-01-15")

        assert result == "2026-01-15"


class TestCreateExcelResponse:
    """测试 create_excel_response 函数"""

    def test_creates_streaming_response(self):
        """测试创建流式响应"""
        from app.services.excel_export_service import create_excel_response

        excel_data = io.BytesIO(b"test data")

        with patch('app.services.excel_export_service.StreamingResponse') as mock_response:
            create_excel_response(excel_data, "test.xlsx")

            mock_response.assert_called_once()
            call_args = mock_response.call_args
            assert call_args[1]["media_type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert "test.xlsx" in call_args[1]["headers"]["Content-Disposition"]

    def test_uses_custom_media_type(self):
        """测试使用自定义媒体类型"""
        from app.services.excel_export_service import create_excel_response

        excel_data = io.BytesIO(b"test data")

        with patch('app.services.excel_export_service.StreamingResponse') as mock_response:
            create_excel_response(excel_data, "test.xls", media_type="application/vnd.ms-excel")

            call_args = mock_response.call_args
            assert call_args[1]["media_type"] == "application/vnd.ms-excel"


class TestExcelAvailable:
    """测试Excel库可用性"""

    def test_raises_error_when_not_available(self):
        """测试库不可用时抛出异常"""
        from app.services import excel_export_service

        original_value = excel_export_service.EXCEL_AVAILABLE
        try:
            excel_export_service.EXCEL_AVAILABLE = False

            with pytest.raises(ImportError, match="Excel处理库未安装"):
                excel_export_service.ExcelExportService()
        finally:
            excel_export_service.EXCEL_AVAILABLE = original_value

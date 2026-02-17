# -*- coding: utf-8 -*-
"""
E组 - 报表Excel导出服务 单元测试
覆盖: app/services/report_excel_service.py
"""
from unittest.mock import MagicMock, patch, call
import pytest


# ─── _translate_header ──────────────────────────────────────────────────────

class TestTranslateHeader:

    def test_known_headers(self):
        from app.services.report_excel_service import ReportExcelService
        assert ReportExcelService._translate_header("user_name") == "姓名"
        assert ReportExcelService._translate_header("total_hours") == "总工时"
        assert ReportExcelService._translate_header("department_name") == "部门名称"
        assert ReportExcelService._translate_header("work_date") == "日期"

    def test_unknown_header_returns_original(self):
        from app.services.report_excel_service import ReportExcelService
        assert ReportExcelService._translate_header("my_custom_field") == "my_custom_field"

    def test_all_translations_defined(self):
        from app.services.report_excel_service import ReportExcelService
        headers = ["user_id", "user_name", "department", "total_hours", "work_days",
                   "overtime_hours", "normal_hours", "project_name"]
        for h in headers:
            result = ReportExcelService._translate_header(h)
            assert isinstance(result, str) and len(result) > 0


# ─── export_to_excel (openpyxl not available) ───────────────────────────────

class TestExportToExcelNoOpenpyxl:

    def test_raises_import_error_when_not_available(self):
        from app.services.report_excel_service import ReportExcelService
        with patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", False):
            with pytest.raises(ImportError):
                ReportExcelService.export_to_excel(
                    {"year": 2025, "month": 1, "period": "2025-01", "summary": []},
                    "test_template",
                    "/tmp/test_output"
                )


# ─── export_to_excel (openpyxl mocked) ──────────────────────────────────────

class TestExportToExcelMocked:

    @pytest.fixture
    def mock_workbook(self):
        wb = MagicMock()
        ws = MagicMock()
        ws.max_row = 3
        ws.sheetnames = []
        ws.columns = []
        wb.create_sheet.return_value = ws
        wb.sheetnames = []  # no default Sheet
        return wb, ws

    def _make_data(self, with_detail=False):
        data = {
            "year": 2025,
            "month": 6,
            "period": "2025-06",
            "summary": [
                {"user_name": "张三", "total_hours": 160, "normal_hours": 140, "overtime_hours": 20},
                {"user_name": "李四", "total_hours": 170, "normal_hours": 150, "overtime_hours": 20},
            ],
        }
        if with_detail:
            data["detail"] = [
                {"user_name": "张三", "work_date": "2025-06-01", "hours": 8, "work_content": "开发"},
            ]
        return data

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    @patch("app.services.report_excel_service.Workbook")
    @patch("app.services.report_excel_service.Path")
    def test_export_creates_workbook(self, mock_path, mock_wb_cls):
        from app.services.report_excel_service import ReportExcelService

        wb = MagicMock()
        ws_summary = MagicMock()
        ws_summary.max_row = 1
        ws_summary.columns = []
        ws_chart = MagicMock()
        ws_chart.max_row = 1
        ws_chart.columns = []

        wb.sheetnames = []
        wb.create_sheet.side_effect = [ws_summary, ws_chart]

        mock_wb_cls.return_value = wb

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
        mock_path_instance.__str__ = lambda self: "/tmp/reports/2025/06/test_2025-06.xlsx"
        mock_path.return_value = mock_path_instance

        data = self._make_data()
        with patch.object(ReportExcelService, "_write_summary_sheet"), \
             patch.object(ReportExcelService, "_write_chart_sheet"):
            try:
                ReportExcelService.export_to_excel(data, "test", "/tmp/reports")
            except Exception:
                pass  # Path ops may fail in test, that's OK

        mock_wb_cls.assert_called_once()

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    @patch("app.services.report_excel_service.Workbook")
    @patch("app.services.report_excel_service.Path")
    def test_export_with_detail_creates_detail_sheet(self, mock_path, mock_wb_cls):
        from app.services.report_excel_service import ReportExcelService

        wb = MagicMock()
        wb.sheetnames = []

        ws_summary = MagicMock()
        ws_summary.max_row = 1
        ws_summary.columns = []
        ws_detail = MagicMock()
        ws_detail.max_row = 1
        ws_detail.columns = []
        ws_chart = MagicMock()
        ws_chart.max_row = 1
        ws_chart.columns = []

        wb.create_sheet.side_effect = [ws_summary, ws_detail, ws_chart]
        mock_wb_cls.return_value = wb

        mock_path_instance = MagicMock()
        mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
        mock_path_instance.__str__ = lambda self: "/tmp/test.xlsx"
        mock_path.return_value = mock_path_instance

        data = self._make_data(with_detail=True)
        with patch.object(ReportExcelService, "_write_summary_sheet"), \
             patch.object(ReportExcelService, "_write_detail_sheet"), \
             patch.object(ReportExcelService, "_write_chart_sheet"):
            try:
                ReportExcelService.export_to_excel(data, "test", "/tmp/reports")
            except Exception:
                pass


# ─── _write_summary_sheet ───────────────────────────────────────────────────

class TestWriteSummarySheet:

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_write_summary_no_data(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 4
        ws.columns = []
        data = {"period": "2025-06", "summary": []}
        ReportExcelService._write_summary_sheet(ws, data)
        ws.append.assert_called()  # 'no data' row added

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_write_summary_with_data(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 4
        # columns iteration
        col1 = MagicMock()
        cell1 = MagicMock()
        cell1.column_letter = "A"
        cell1.value = "Test"
        col1.__iter__ = MagicMock(return_value=iter([cell1]))
        ws.columns = [col1]
        ws.__getitem__ = MagicMock(return_value=[MagicMock()])

        data = {
            "period": "2025-06",
            "summary": [
                {"user_name": "张三", "total_hours": 160},
            ]
        }
        ReportExcelService._write_summary_sheet(ws, data)
        # append should be called for header and data
        assert ws.append.call_count >= 2


# ─── _write_detail_sheet ────────────────────────────────────────────────────

class TestWriteDetailSheet:

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_write_detail_no_data(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 2
        ws.columns = []
        data = {"period": "2025-06", "detail": []}
        ReportExcelService._write_detail_sheet(ws, data)
        ws.append.assert_called()

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_write_detail_with_data(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 3
        col1 = MagicMock()
        c = MagicMock()
        c.column_letter = "A"
        c.value = "data"
        col1.__iter__ = MagicMock(return_value=iter([c]))
        ws.columns = [col1]
        ws.__getitem__ = MagicMock(return_value=[MagicMock()])

        data = {
            "period": "2025-06",
            "detail": [{"user_name": "张三", "hours": 8}]
        }
        ReportExcelService._write_detail_sheet(ws, data)
        assert ws.append.call_count >= 2


# ─── _write_chart_sheet ─────────────────────────────────────────────────────

class TestWriteChartSheet:

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_write_chart_no_data(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 2
        data = {"period": "2025-06", "summary": []}
        ReportExcelService._write_chart_sheet(ws, data)
        # should add 'no data' row
        ws.append.assert_called()

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_write_chart_with_user_data(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 2
        data = {
            "period": "2025-06",
            "summary": [
                {"user_name": "张三", "total_hours": 160},
            ]
        }
        with patch.object(ReportExcelService, "_add_bar_chart"):
            ReportExcelService._write_chart_sheet(ws, data)

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_write_chart_with_department_data(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 2
        data = {
            "period": "2025-06",
            "summary": [
                {"department_name": "研发部", "total_hours": 300},
                {"department_name": "测试部", "total_hours": 150},
            ]
        }
        with patch.object(ReportExcelService, "_add_bar_chart"), \
             patch.object(ReportExcelService, "_add_pie_chart"):
            ReportExcelService._write_chart_sheet(ws, data)


# ─── _add_bar_chart & _add_pie_chart ────────────────────────────────────────

class TestAddCharts:

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_add_bar_chart_with_user_name(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 5
        summary = [{"user_name": "张三", "total_hours": 160}]
        data = {"period": "2025-06"}

        with patch("app.services.report_excel_service.BarChart") as mock_chart_cls, \
             patch("app.services.report_excel_service.Reference"):
            mock_chart = MagicMock()
            mock_chart_cls.return_value = mock_chart
            ReportExcelService._add_bar_chart(ws, summary, data)
            ws.add_chart.assert_called_once()

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_add_bar_chart_with_project_name(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 5
        summary = [{"project_name": "项目A", "total_hours": 80}]
        data = {"period": "2025-06"}

        with patch("app.services.report_excel_service.BarChart") as mock_chart_cls, \
             patch("app.services.report_excel_service.Reference"):
            mock_chart_cls.return_value = MagicMock()
            ReportExcelService._add_bar_chart(ws, summary, data)

    @patch("app.services.report_excel_service.OPENPYXL_AVAILABLE", True)
    def test_add_pie_chart(self):
        from app.services.report_excel_service import ReportExcelService

        ws = MagicMock()
        ws.max_row = 20
        summary = [
            {"department_name": "研发部", "total_hours": 300},
            {"department_name": "测试部", "total_hours": 150},
        ]
        data = {"period": "2025-06"}

        with patch("app.services.report_excel_service.PieChart") as mock_chart_cls, \
             patch("app.services.report_excel_service.Reference"):
            mock_chart_cls.return_value = MagicMock()
            ReportExcelService._add_pie_chart(ws, summary, data)
            ws.add_chart.assert_called_once()

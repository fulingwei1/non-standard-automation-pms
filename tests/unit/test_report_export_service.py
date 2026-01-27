# -*- coding: utf-8 -*-
"""
Tests for report_export_service
Covers: app/services/report_export_service.py
"""

import os
import tempfile


from app.services.report_export_service import ReportExportService


class TestReportExportService:
    """Test suite for ReportExportService."""

    def test_init_creates_export_dir(self):
        """服务初始化应创建导出目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_dir = os.path.join(tmpdir, "test_exports")
            service = ReportExportService(export_dir=export_dir)

            assert os.path.exists(export_dir)
            assert service.export_dir == export_dir

    def test_init_default_dir(self):
        """使用默认目录初始化。"""
        service = ReportExportService()
        assert service.export_dir == "exports"

    def test_export_to_excel_basic(self):
        """测试基本的 Excel 导出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            # 准备测试数据（符合实际API）
        data = {
        "details": [
        {"name": "项目A", "progress": 50, "status": "进行中"},
        {"name": "项目B", "progress": 100, "status": "已完成"},
        ]
        }

            # 调用导出方法
        result = service.export_to_excel(
        data=data,
        filename="test_report",
        title="项目报表"
        )

            # 验证文件生成
        assert result is not None
        assert os.path.exists(result)
        assert result.endswith(".xlsx")

    def test_export_to_csv_basic(self):
        """测试基本的 CSV 导出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            data = {
            "details": [
            {"name": "测试1", "value": 100},
            {"name": "测试2", "value": 200},
            ]
            }

            result = service.export_to_csv(
            data=data,
            filename="test_report"
            )

            assert result is not None
            assert os.path.exists(result)
            assert result.endswith(".csv")

    def test_export_empty_data(self):
        """空数据应能正常导出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            result = service.export_to_excel(
            data={},
            filename="empty_report",
            title="空报表"
            )

            assert result is not None
            assert os.path.exists(result)

    def test_export_to_excel_with_sheets(self):
        """测试多Sheet Excel导出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            sheets = [
            {
            "name": "Sheet1",
            "title": "报表1",
            "headers": ["列1", "列2"],
            "rows": [["值1", "值2"]]
            },
            {
            "name": "Sheet2",
            "title": "报表2",
            "headers": ["列A", "列B"],
            "rows": [["值A", "值B"]]
            }
            ]

            result = service.export_to_excel(
            data={},
            filename="multisheet_report",
            sheets=sheets
            )

            assert result is not None
            assert os.path.exists(result)

    def test_export_to_pdf_basic(self):
        """测试基本的PDF导出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            data = {
            "title": "测试报表",
            "summary": {"总计": 100},
            "details": [
            {"name": "项目A", "value": 50},
            {"name": "项目B", "value": 50}
            ]
            }

            result = service.export_to_pdf(
            data=data,
            filename="test_report"
            )

            assert result is not None
            assert os.path.exists(result)
            assert result.endswith(".pdf")

    def test_export_to_csv_with_special_chars(self):
        """测试CSV导出 - 特殊字符"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            data = {
            "details": [
            {"name": "测试,项目", "value": "100,000"},
            {"name": "测试\"项目", "value": 200}
            ]
            }

            result = service.export_to_csv(
            data=data,
            filename="special_chars_report"
            )

            assert result is not None
            assert os.path.exists(result)

    def test_export_to_pdf_landscape(self):
        """测试横向 PDF 导出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            data = {
            "details": [
            {"name": "项目A", "value": 50},
            ]
            }

            result = service.export_to_pdf(
            data=data,
            filename="landscape_report",
            title="横向报表",
            landscape_mode=True
            )

            assert result is not None
            assert os.path.exists(result)

    def test_export_to_csv_list_data(self):
        """测试列表格式数据的 CSV 导出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            data = [
            {"name": "测试1", "value": 100},
            {"name": "测试2", "value": 200},
            ]

            result = service.export_to_csv(
            data=data,
            filename="list_report"
            )

            assert result is not None
            assert os.path.exists(result)

    def test_format_value(self):
        """测试值格式化方法。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            # 测试各种类型的值
        from decimal import Decimal
        from datetime import date, datetime

        assert service._format_value(100) == 100
        assert service._format_value(100.5) == 100.5
        assert service._format_value("测试") == "测试"
        assert service._format_value(None) == ""
        assert service._format_value(Decimal("100.50")) == 100.50
        assert isinstance(service._format_value(date(2024, 1, 15)), str)
        assert isinstance(service._format_value(datetime(2024, 1, 15, 10, 30)), str)


class TestReportGenerator:
    """Test suite for ReportGenerator static methods."""

    def test_generate_project_report(self):
        """测试生成项目报表数据。"""
        from app.services.report_export_service import ReportGenerator

        projects = [
        {
        "project_code": "PJ001",
        "project_name": "项目A",
        "status": "EXECUTING",
        "progress": 50
        },
        {
        "project_code": "PJ002",
        "project_name": "项目B",
        "status": "COMPLETED",
        "progress": 100
        }
        ]

        result = ReportGenerator.generate_project_report(projects)

        assert isinstance(result, dict)
        assert "summary" in result
        assert "details" in result
        assert result["summary"]["总项目数"] == 2
        assert result["summary"]["进行中"] == 1
        assert result["summary"]["已完成"] == 1
        assert len(result["details"]) == 2

    def test_generate_financial_report(self):
        """测试生成财务报表数据。"""
        from app.services.report_export_service import ReportGenerator

        financial_data = [
        {
        "category": "收入",
        "revenue": 100000,
        "cost": 0,
        "date": "2024-01-15"
        },
        {
        "category": "支出",
        "revenue": 0,
        "cost": 50000,
        "date": "2024-01-20"
        }
        ]

        result = ReportGenerator.generate_financial_report(financial_data)

        assert isinstance(result, dict)
        assert "summary" in result
        assert "details" in result
        assert "总营收" in result["summary"]
        assert "总成本" in result["summary"]
        assert "总利润" in result["summary"]
        assert "利润率" in result["summary"]

    def test_generate_utilization_report(self):
        """测试生成利用率报表数据。"""
        from app.services.report_export_service import ReportGenerator

        utilization_data = [
        {
        "resource": "人员A",
        "rate": 80.5,
        "period": "2024-01"
        },
        {
        "resource": "人员B",
        "rate": 65.0,
        "period": "2024-01"
        },
        {
        "resource": "人员C",
        "rate": 90.0,
        "period": "2024-01"
        }
        ]

        result = ReportGenerator.generate_utilization_report(utilization_data)

        assert isinstance(result, dict)
        assert "summary" in result
        assert "details" in result
        assert result["summary"]["人员总数"] == 3
        assert "平均利用率" in result["summary"]
        assert result["summary"]["饱和人数(>=80%)"] == 2
        assert result["summary"]["空闲人数(<60%)"] == 0
        assert len(result["details"]) == 3

    def test_generate_utilization_report_empty(self):
        """测试空数据的利用率报表。"""
        from app.services.report_export_service import ReportGenerator

        result = ReportGenerator.generate_utilization_report([])

        assert isinstance(result, dict)
        assert result["summary"]["人员总数"] == 0
        assert result["summary"]["平均利用率"] == "0.0%"

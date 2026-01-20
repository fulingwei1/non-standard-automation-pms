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

            # 准备测试数据
            data = [
                {"name": "项目A", "progress": 50, "status": "进行中"},
                {"name": "项目B", "progress": 100, "status": "已完成"},
            ]
            columns = ["name", "progress", "status"]
            headers = ["项目名称", "进度", "状态"]

            # 调用导出方法
            result = service.export_to_excel(
                data=data,
                columns=columns,
                headers=headers,
                filename="test_report.xlsx",
                sheet_name="项目报表"
            )

            # 验证文件生成
            assert result is not None
            assert os.path.exists(result)
            assert result.endswith(".xlsx")

    def test_export_to_csv_basic(self):
        """测试基本的 CSV 导出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            data = [
                {"name": "测试1", "value": 100},
                {"name": "测试2", "value": 200},
            ]
            columns = ["name", "value"]
            headers = ["名称", "数值"]

            result = service.export_to_csv(
                data=data,
                columns=columns,
                headers=headers,
                filename="test_report.csv"
            )

            assert result is not None
            assert os.path.exists(result)
            assert result.endswith(".csv")

    def test_export_empty_data(self):
        """空数据应能正常导出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ReportExportService(export_dir=tmpdir)

            result = service.export_to_excel(
                data=[],
                columns=["name"],
                headers=["名称"],
                filename="empty_report.xlsx"
            )

            assert result is not None
            assert os.path.exists(result)

# -*- coding: utf-8 -*-
"""
G3组 - 工时报表服务单元测试
目标文件: app/services/report_service.py
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call

from app.services.report_service import ReportService
from app.models.report import ReportTypeEnum, GeneratedByEnum, ArchiveStatusEnum


class TestGetActiveMonthlyTemplates:
    """测试获取启用的月度报表模板"""

    def test_returns_enabled_monthly_templates(self):
        db = MagicMock()
        mock_templates = [MagicMock(), MagicMock()]
        (db.query.return_value
            .filter.return_value
            .filter.return_value
            .all.return_value) = mock_templates

        result = ReportService.get_active_monthly_templates(db)
        assert result == mock_templates

    def test_returns_empty_when_no_templates(self):
        db = MagicMock()
        (db.query.return_value
            .filter.return_value
            .filter.return_value
            .all.return_value) = []

        result = ReportService.get_active_monthly_templates(db)
        assert result == []


class TestGenerateReport:
    """测试生成报表数据"""

    def setup_method(self):
        self.db = MagicMock()

    def test_raises_when_template_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="报表模板不存在"):
            ReportService.generate_report(self.db, template_id=999, period="2026-01")

    def test_generates_user_monthly_report(self):
        template = MagicMock()
        template.id = 1
        template.report_type = ReportTypeEnum.USER_MONTHLY.value
        template.config = None
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch.object(ReportService, "_generate_user_monthly_report",
                          return_value={"summary": [], "detail": [],
                                        "year": 2026, "month": 1}) as mock_gen:
            result = ReportService.generate_report(self.db, template_id=1, period="2026-01")

        mock_gen.assert_called_once_with(self.db, template, 2026, 1)
        assert result["template"] is template
        assert result["period"] == "2026-01"

    def test_generates_dept_monthly_report(self):
        template = MagicMock()
        template.id = 2
        template.report_type = ReportTypeEnum.DEPT_MONTHLY.value
        template.config = None
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch.object(ReportService, "_generate_dept_monthly_report",
                          return_value={"summary": [], "detail": [],
                                        "year": 2026, "month": 2}) as mock_gen:
            result = ReportService.generate_report(self.db, template_id=2, period="2026-02")

        mock_gen.assert_called_once_with(self.db, template, 2026, 2)
        assert result["period"] == "2026-02"

    def test_generates_project_monthly_report(self):
        template = MagicMock()
        template.id = 3
        template.report_type = ReportTypeEnum.PROJECT_MONTHLY.value
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch.object(ReportService, "_generate_project_monthly_report",
                          return_value={"summary": [], "detail": [],
                                        "year": 2026, "month": 3}):
            result = ReportService.generate_report(self.db, template_id=3, period="2026-03")

        assert result["period"] == "2026-03"

    def test_generates_company_monthly_report(self):
        template = MagicMock()
        template.id = 4
        template.report_type = ReportTypeEnum.COMPANY_MONTHLY.value
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch.object(ReportService, "_generate_company_monthly_report",
                          return_value={"summary": [], "detail": [],
                                        "year": 2026, "month": 4}):
            result = ReportService.generate_report(self.db, template_id=4, period="2026-04")

        assert result["period"] == "2026-04"

    def test_generates_overtime_monthly_report(self):
        template = MagicMock()
        template.id = 5
        template.report_type = ReportTypeEnum.OVERTIME_MONTHLY.value
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch.object(ReportService, "_generate_overtime_monthly_report",
                          return_value={"summary": [], "detail": [],
                                        "year": 2026, "month": 5}):
            result = ReportService.generate_report(self.db, template_id=5, period="2026-05")

        assert result["period"] == "2026-05"

    def test_unsupported_report_type_raises(self):
        template = MagicMock()
        template.id = 99
        template.report_type = "UNSUPPORTED_TYPE"
        self.db.query.return_value.filter.return_value.first.return_value = template

        with pytest.raises(ValueError, match="不支持的报表类型"):
            ReportService.generate_report(self.db, template_id=99, period="2026-01")

    def test_generated_by_defaults_to_system(self):
        template = MagicMock()
        template.id = 1
        template.report_type = ReportTypeEnum.USER_MONTHLY.value
        template.config = None
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch.object(ReportService, "_generate_user_monthly_report",
                          return_value={"summary": [], "detail": [], "year": 2026, "month": 1}):
            result = ReportService.generate_report(self.db, template_id=1, period="2026-01")

        assert result["generated_by"] == GeneratedByEnum.SYSTEM.value


class TestGetLastMonthPeriod:
    """测试获取上月周期字符串"""

    def test_returns_string_format(self):
        result = ReportService.get_last_month_period()
        assert len(result) == 7  # "YYYY-MM"
        assert "-" in result

    def test_january_returns_december_of_previous_year(self):
        with patch("app.services.report_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15)
            result = ReportService.get_last_month_period()
        assert result == "2025-12"

    def test_july_returns_june(self):
        with patch("app.services.report_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 10)
            result = ReportService.get_last_month_period()
        assert result == "2026-06"


class TestArchiveReport:
    """测试归档报表"""

    def setup_method(self):
        self.db = MagicMock()

    def test_raises_when_template_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="报表模板不存在"):
            ReportService.archive_report(
                self.db,
                template_id=999,
                period="2026-01",
                file_path="/tmp/report.xlsx",
                file_size=1024,
                row_count=100,
            )

    def test_archive_creates_record(self):
        template = MagicMock()
        template.id = 1
        template.report_type = ReportTypeEnum.USER_MONTHLY.value
        template.name = "人员月报"
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch("app.services.report_service.save_obj") as mock_save:
            archive = ReportService.archive_report(
                self.db,
                template_id=1,
                period="2026-01",
                file_path="/reports/2026-01.xlsx",
                file_size=20480,
                row_count=50,
            )

        mock_save.assert_called_once()
        assert archive.template_id == 1
        assert archive.period == "2026-01"
        assert archive.file_path == "/reports/2026-01.xlsx"
        assert archive.file_size == 20480
        assert archive.row_count == 50
        assert archive.download_count == 0

    def test_archive_with_error_message(self):
        template = MagicMock()
        template.id = 1
        template.report_type = "USER_MONTHLY"
        template.name = "人员月报"
        self.db.query.return_value.filter.return_value.first.return_value = template

        with patch("app.services.report_service.save_obj"):
            archive = ReportService.archive_report(
                self.db,
                template_id=1,
                period="2026-01",
                file_path="",
                file_size=0,
                row_count=0,
                status=ArchiveStatusEnum.FAILED.value,
                error_message="生成失败",
            )

        assert archive.error_message == "生成失败"
        assert archive.status == ArchiveStatusEnum.FAILED.value


class TestIncrementDownloadCount:
    """测试增加下载次数"""

    def setup_method(self):
        self.db = MagicMock()

    def test_increments_existing_archive(self):
        archive = MagicMock()
        archive.download_count = 5
        self.db.query.return_value.filter.return_value.first.return_value = archive

        ReportService.increment_download_count(self.db, archive_id=1)

        assert archive.download_count == 6
        self.db.commit.assert_called_once()

    def test_no_op_when_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 不应抛出异常
        ReportService.increment_download_count(self.db, archive_id=999)
        self.db.commit.assert_not_called()

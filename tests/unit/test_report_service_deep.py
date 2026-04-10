# -*- coding: utf-8 -*-
"""对齐当前静态 API 的 report_service 深度测试"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.report import ArchiveStatusEnum, GeneratedByEnum, ReportTypeEnum
from app.services.report_service import ReportService


class TestReportServiceBusinessLogic:
    """报表服务业务逻辑测试"""

    @patch.object(ReportService, "_generate_user_monthly_report")
    def test_generate_report(self, mock_generate):
        """测试生成报表入口会分发到对应静态方法"""
        mock_db = MagicMock()
        mock_template = MagicMock()
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_generate.return_value = {
            "summary": [{"user_name": "张三", "total_hours": 160}],
            "detail": [],
            "year": 2026,
            "month": 1,
        }

        result = ReportService.generate_report(mock_db, template_id=1, period="2026-01")

        assert result["template"] is mock_template
        assert result["period"] == "2026-01"
        assert result["generated_by"] == GeneratedByEnum.SYSTEM.value
        mock_generate.assert_called_once_with(mock_db, mock_template, 2026, 1)

    @patch("app.services.report_service.save_obj")
    @patch("app.services.report_service.datetime")
    def test_archive_report(self, mock_datetime, mock_save_obj):
        """测试归档报表会保存归档对象"""
        mock_db = MagicMock()
        mock_datetime.utcnow.return_value = datetime(2026, 2, 1, 10, 0, 0)

        mock_template = MagicMock()
        mock_template.name = "人员月报"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template

        archive = ReportService.archive_report(
            db=mock_db,
            template_id=1,
            period="2026-01",
            file_path="/tmp/report.xlsx",
            file_size=1024,
            row_count=10,
            status=ArchiveStatusEnum.SUCCESS.value,
        )

        mock_save_obj.assert_called_once_with(mock_db, archive)
        assert archive.template_id == 1
        assert archive.report_type == ReportTypeEnum.USER_MONTHLY.value
        assert archive.download_count == 0

    def test_get_active_monthly_templates(self):
        """测试获取启用的月度模板"""
        mock_db = MagicMock()
        mock_templates = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_templates

        result = ReportService.get_active_monthly_templates(mock_db)

        assert result == mock_templates

    def test_increment_download_count(self):
        """测试增加下载次数"""
        mock_db = MagicMock()
        mock_archive = MagicMock()
        mock_archive.download_count = 2
        mock_db.query.return_value.filter.return_value.first.return_value = mock_archive

        ReportService.increment_download_count(mock_db, archive_id=9)

        assert mock_archive.download_count == 3
        mock_db.commit.assert_called_once()

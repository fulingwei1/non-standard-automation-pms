# -*- coding: utf-8 -*-
"""Tests for meeting_report_docx_service"""
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest


class TestMeetingReportDocxService:

    @patch("app.services.meeting_report_docx_service.DOCX_AVAILABLE", True)
    def test_init_success(self):
        from app.services.meeting_report_docx_service import MeetingReportDocxService
        service = MeetingReportDocxService()
        assert service is not None

    @patch("app.services.meeting_report_docx_service.DOCX_AVAILABLE", False)
    def test_init_no_docx(self):
        from app.services.meeting_report_docx_service import MeetingReportDocxService
        with pytest.raises(ImportError):
            MeetingReportDocxService()

    def test_format_rhythm_level(self):
        from app.services.meeting_report_docx_service import MeetingReportDocxService
        with patch("app.services.meeting_report_docx_service.DOCX_AVAILABLE", True):
            svc = MeetingReportDocxService()
            assert svc._format_rhythm_level("STRATEGIC") == "战略层"
            assert svc._format_rhythm_level("UNKNOWN") == "UNKNOWN"

    def test_format_cycle_type(self):
        from app.services.meeting_report_docx_service import MeetingReportDocxService
        with patch("app.services.meeting_report_docx_service.DOCX_AVAILABLE", True):
            svc = MeetingReportDocxService()
            assert svc._format_cycle_type("MONTHLY") == "月度"
            assert svc._format_cycle_type("X") == "X"

    def test_format_status(self):
        from app.services.meeting_report_docx_service import MeetingReportDocxService
        with patch("app.services.meeting_report_docx_service.DOCX_AVAILABLE", True):
            svc = MeetingReportDocxService()
            assert svc._format_status("COMPLETED") == "已完成"
            assert svc._format_status("CANCELLED") == "已取消"

    @patch("app.services.meeting_report_docx_service.DOCX_AVAILABLE", True)
    @patch("app.services.meeting_report_docx_service.Document")
    def test_generate_annual_report_docx(self, mock_doc_cls):
        from app.services.meeting_report_docx_service import MeetingReportDocxService
        mock_doc = MagicMock()
        mock_doc_cls.return_value = mock_doc
        mock_doc.styles = {"Normal": MagicMock(), **{f"Heading {i}": MagicMock() for i in range(1, 10)}}

        with patch("app.services.meeting_report_docx_service.qn", return_value="w:eastAsia"):
            svc = MeetingReportDocxService()
            with patch("app.services.docx_content_builders.setup_document_formatting"), \
                 patch("app.services.docx_content_builders.add_document_header"), \
                 patch("app.services.docx_content_builders.add_summary_section"), \
                 patch("app.services.docx_content_builders.add_level_statistics_section"), \
                 patch("app.services.docx_content_builders.add_action_items_section"), \
                 patch("app.services.docx_content_builders.add_key_decisions_section"), \
                 patch("app.services.docx_content_builders.add_strategic_structures_section"), \
                 patch("app.services.docx_content_builders.add_meetings_list_section"), \
                 patch("app.services.docx_content_builders.add_document_footer"):
                result = svc.generate_annual_report_docx(
                    report_data={"summary": {}, "by_level": {}, "action_items_summary": {},
                                 "key_decisions": [], "strategic_structures": [], "meetings": []},
                    report_title="测试报告",
                    period_year=2024
                )
                assert isinstance(result, BytesIO)

    @patch("app.services.meeting_report_docx_service.DOCX_AVAILABLE", True)
    @patch("app.services.meeting_report_docx_service.Document")
    def test_generate_monthly_report_docx(self, mock_doc_cls):
        from app.services.meeting_report_docx_service import MeetingReportDocxService
        mock_doc = MagicMock()
        mock_doc_cls.return_value = mock_doc
        mock_doc.styles = {"Normal": MagicMock(), **{f"Heading {i}": MagicMock() for i in range(1, 10)}}

        with patch("app.services.meeting_report_docx_service.qn", return_value="w:eastAsia"):
            svc = MeetingReportDocxService()
            with patch("app.services.docx_content_builders.setup_document_formatting"), \
                 patch("app.services.docx_content_builders.add_document_header"), \
                 patch("app.services.docx_content_builders.add_summary_section"), \
                 patch("app.services.docx_content_builders.add_comparison_section"), \
                 patch("app.services.docx_content_builders.add_level_statistics_section"), \
                 patch("app.services.docx_content_builders.add_action_items_section"), \
                 patch("app.services.docx_content_builders.add_key_decisions_section"), \
                 patch("app.services.docx_content_builders.add_meetings_list_section"), \
                 patch("app.services.docx_content_builders.add_document_footer"):
                result = svc.generate_monthly_report_docx(
                    report_data={"summary": {}, "by_level": {}, "action_items_summary": {},
                                 "key_decisions": [], "meetings": []},
                    comparison_data={},
                    report_title="月度报告",
                    period_year=2024,
                    period_month=6
                )
                assert isinstance(result, BytesIO)

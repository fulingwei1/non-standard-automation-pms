# -*- coding: utf-8 -*-
"""meeting_report_docx_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.meeting_report_docx_service import MeetingReportDocxService

class TestMeetingReportDocxServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = MeetingReportDocxService(mock_db)
        assert hasattr(service, 'db')

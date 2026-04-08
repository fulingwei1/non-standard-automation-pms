# -*- coding: utf-8 -*-
"""report_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report.report_service import ReportService

class TestReportServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ReportService(mock_db)
        assert hasattr(service, 'db')

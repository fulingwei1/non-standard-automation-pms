# -*- coding: utf-8 -*-
"""weekly_report_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_report_auto.weekly_report_service import WeeklyReportService

class TestWeeklyReportServiceInit:
    def test_init(self):
        service = WeeklyReportService(Mock())
        assert service is not None

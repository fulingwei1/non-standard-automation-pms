# -*- coding: utf-8 -*-
"""monthly_report_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_report_auto.monthly_report_service import MonthlyReportService

class TestMonthlyReportServiceInit:
    def test_init(self):
        service = MonthlyReportService(Mock())
        assert service is not None

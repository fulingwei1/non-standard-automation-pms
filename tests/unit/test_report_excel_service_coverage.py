# -*- coding: utf-8 -*-
"""report_excel_service单元测试"""
import pytest
from app.services.report_excel_service import ReportExcelService

class TestReportExcelServiceInit:
    def test_init_without_db(self):
        """测试无参数初始化"""
        service = ReportExcelService()
        assert service is not None
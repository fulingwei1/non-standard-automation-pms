# -*- coding: utf-8 -*-
"""template_report_data_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.template_report_data_service import TemplateReportDataService

class TestTemplateReportDataServiceInit:
    def test_init(self):
        service = TemplateReportDataService(Mock())
        assert service is not None

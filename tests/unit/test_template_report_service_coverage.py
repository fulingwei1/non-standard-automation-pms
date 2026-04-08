# -*- coding: utf-8 -*-
"""template_report_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.template_report_service import TemplateReportService

class TestTemplateReportServiceInit:
    def test_init(self):
        service = TemplateReportService(Mock())
        assert service is not None

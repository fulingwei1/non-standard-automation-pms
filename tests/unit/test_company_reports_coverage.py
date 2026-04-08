# -*- coding: utf-8 -*-
"""company_reports单元测试"""
import pytest
from unittest.mock import Mock
from services/template_report/company_reports import CompanyReportMixin

class TestCompanyReportMixinInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = CompanyReportMixin(mock_db)
        assert hasattr(service, 'db')

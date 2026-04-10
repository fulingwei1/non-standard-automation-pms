# -*- coding: utf-8 -*-
"""business_support_reports_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.business_support_reports.business_support_reports_service import BusinessSupportReportsService

class TestBusinessSupportReportsServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = BusinessSupportReportsService(mock_db)
        assert hasattr(service, 'db')

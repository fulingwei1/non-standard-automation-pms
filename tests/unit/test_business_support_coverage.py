# -*- coding: utf-8 -*-
"""business_support单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.adapters.business_support import BusinessSupportReportAdapter

class TestBusinessSupportReportAdapterInit:
    def test_init(self):
        service = BusinessSupportReportAdapter(Mock())
        assert service is not None

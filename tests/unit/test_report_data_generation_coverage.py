# -*- coding: utf-8 -*-
"""report_data_generation单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.adapters.report_data_generation import ReportDataGenerationAdapter

class TestReportDataGenerationAdapterInit:
    def test_init(self):
        service = ReportDataGenerationAdapter(Mock())
        assert service is not None

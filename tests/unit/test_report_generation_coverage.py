# -*- coding: utf-8 -*-
"""report_generation单元测试"""
import pytest
from unittest.mock import Mock
from app.services.resource_waste_analysis.report_generation import ReportGenerationMixin

class TestReportGenerationMixinInit:
    def test_init(self):
        service = ReportGenerationMixin(Mock())
        assert service is not None

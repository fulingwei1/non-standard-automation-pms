# -*- coding: utf-8 -*-
"""analysis_reports单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_data_generation.analysis_reports import AnalysisReportMixin

class TestAnalysisReportMixinInit:
    def test_init(self):
        service = AnalysisReportMixin(Mock())
        assert service is not None

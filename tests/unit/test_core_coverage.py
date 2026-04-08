# -*- coding: utf-8 -*-
"""core单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_data_generation.core import ReportDataGenerationCore

class TestReportDataGenerationCoreInit:
    def test_init(self):
        service = ReportDataGenerationCore(Mock())
        assert service is not None

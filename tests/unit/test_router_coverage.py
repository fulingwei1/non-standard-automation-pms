# -*- coding: utf-8 -*-
"""router单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_data_generation.router import ReportRouterMixin

class TestReportRouterMixinInit:
    def test_init(self):
        service = ReportRouterMixin(Mock())
        assert service is not None

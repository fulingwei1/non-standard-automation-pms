# -*- coding: utf-8 -*-
"""dept_reports单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_data_generation.dept_reports import DeptReportMixin

class TestDeptReportMixinInit:
    def test_init(self):
        service = DeptReportMixin(Mock())
        assert service is not None

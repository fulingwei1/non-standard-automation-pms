# -*- coding: utf-8 -*-
"""department单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.adapters.department import DeptReportAdapter

class TestDeptReportAdapterInit:
    def test_init(self):
        service = DeptReportAdapter(Mock())
        assert service is not None

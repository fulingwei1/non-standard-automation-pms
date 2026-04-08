# -*- coding: utf-8 -*-
"""rd_expense单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter

class TestRdExpenseReportAdapterInit:
    def test_init(self):
        service = RdExpenseReportAdapter(Mock())
        assert service is not None

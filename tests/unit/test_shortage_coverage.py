# -*- coding: utf-8 -*-
"""shortage单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.adapters.shortage import ShortageReportAdapter

class TestShortageReportAdapterInit:
    def test_init(self):
        service = ShortageReportAdapter(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""report单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_integrity.report import DataReportMixin

class TestDataReportMixinInit:
    def test_init(self):
        service = DataReportMixin(Mock())
        assert service is not None

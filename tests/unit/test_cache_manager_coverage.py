# -*- coding: utf-8 -*-
"""cache_manager单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.cache_manager import ReportCacheManager

class TestReportCacheManagerInit:
    def test_init(self):
        service = ReportCacheManager(Mock())
        assert service is not None

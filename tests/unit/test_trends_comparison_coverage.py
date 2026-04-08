# -*- coding: utf-8 -*-
"""trends_comparison单元测试"""
import pytest
from unittest.mock import Mock
from app.services.resource_waste_analysis.trends_comparison import TrendsComparisonMixin

class TestTrendsComparisonMixinInit:
    def test_init(self):
        service = TrendsComparisonMixin(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""aggregator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_collector.aggregator import PerformanceDataAggregator

class TestPerformanceDataAggregatorInit:
    def test_init(self):
        service = PerformanceDataAggregator(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""cost_benchmark_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project.cost_benchmark_service import CostBenchmarkService

class TestCostBenchmarkServiceInit:
    def test_init(self):
        service = CostBenchmarkService(Mock())
        assert service is not None

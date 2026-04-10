# -*- coding: utf-8 -*-
"""optimization_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.cost.optimization_engine import OptimizationEngine

class TestOptimizationEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = OptimizationEngine(mock_db)
        assert hasattr(service, 'db')

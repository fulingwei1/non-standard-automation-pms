# -*- coding: utf-8 -*-
"""supplier_performance_evaluator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator

class TestSupplierPerformanceEvaluatorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SupplierPerformanceEvaluator(mock_db)
        assert hasattr(service, 'db')

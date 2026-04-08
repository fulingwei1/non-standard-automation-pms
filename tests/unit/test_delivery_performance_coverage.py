# -*- coding: utf-8 -*-
"""delivery_performance单元测试"""
import pytest
from unittest.mock import Mock
from services/procurement_analysis/delivery_performance import DeliveryPerformanceAnalyzer

class TestDeliveryPerformanceAnalyzerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = DeliveryPerformanceAnalyzer(mock_db)
        assert hasattr(service, 'db')

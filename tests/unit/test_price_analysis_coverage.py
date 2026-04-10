# -*- coding: utf-8 -*-
"""price_analysis单元测试"""
import pytest
from unittest.mock import Mock
from app.services.procurement_analysis.price_analysis import PriceAnalyzer

class TestPriceAnalyzerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PriceAnalyzer(mock_db)
        assert hasattr(service, 'db')

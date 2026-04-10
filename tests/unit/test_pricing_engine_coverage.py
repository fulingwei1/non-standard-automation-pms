# -*- coding: utf-8 -*-
"""pricing_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.cost.pricing_engine import PricingEngine

class TestPricingEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PricingEngine(mock_db)
        assert hasattr(service, 'db')

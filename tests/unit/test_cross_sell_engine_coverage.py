# -*- coding: utf-8 -*-
"""cross_sell_engine单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/engines/cross_sell_engine import CrossSellEngine

class TestCrossSellEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = CrossSellEngine(mock_db)
        assert hasattr(service, 'db')

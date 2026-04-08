# -*- coding: utf-8 -*-
"""stock_count_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stock_count_service import StockCountService

class TestStockCountServiceInit:
    def test_init(self):
        service = StockCountService(Mock())
        assert service is not None

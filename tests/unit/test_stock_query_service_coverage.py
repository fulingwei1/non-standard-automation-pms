# -*- coding: utf-8 -*-
"""stock_query_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.stock_query_service import StockQueryService

class TestStockQueryServiceInit:
    def test_init(self):
        service = StockQueryService(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""stock_count_service单元测试"""
from unittest.mock import Mock
from app.services.stock_count_service import StockCountService


class TestStockCountServiceInit:
    def test_init(self):
        service = StockCountService(Mock(), tenant_id=1)
        assert service.db is not None

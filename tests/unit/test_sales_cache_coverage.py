# -*- coding: utf-8 -*-
"""sales_cache单元测试"""
import pytest
from unittest.mock import Mock
from services/cache/sales_cache import SalesCacheService

class TestSalesCacheServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SalesCacheService(mock_db)
        assert hasattr(service, 'db')

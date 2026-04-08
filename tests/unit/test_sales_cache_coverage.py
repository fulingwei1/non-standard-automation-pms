# -*- coding: utf-8 -*-
"""sales_cache单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cache.sales_cache import SalesCacheService

class TestSalesCacheServiceInit:
    def test_init(self):
        service = SalesCacheService(Mock())
        assert service is not None

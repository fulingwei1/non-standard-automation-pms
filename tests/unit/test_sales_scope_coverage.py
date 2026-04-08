# -*- coding: utf-8 -*-
"""sales_scope单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/sales_scope import SalesScopeContext

class TestSalesScopeContextInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SalesScopeContext(mock_db)
        assert hasattr(service, 'db')

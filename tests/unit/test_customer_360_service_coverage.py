# -*- coding: utf-8 -*-
"""customer_360_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.customer_360_service import Customer360Service

class TestCustomer360ServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = Customer360Service(mock_db)
        assert hasattr(service, 'db')

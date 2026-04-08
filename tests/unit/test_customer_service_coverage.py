# -*- coding: utf-8 -*-
"""customer_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.customer_service import CustomerService

class TestCustomerServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = CustomerService(mock_db)
        assert hasattr(service, 'db')

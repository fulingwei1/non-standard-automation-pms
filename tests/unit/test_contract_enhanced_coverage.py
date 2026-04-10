# -*- coding: utf-8 -*-
"""contract_enhanced单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.contract_enhanced import ContractEnhancedService

class TestContractEnhancedServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ContractEnhancedService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""contract_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.contract_service import ContractService

class TestContractServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ContractService(mock_db)
        assert hasattr(service, 'db')

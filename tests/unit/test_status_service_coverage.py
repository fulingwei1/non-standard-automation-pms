# -*- coding: utf-8 -*-
"""status_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/contract/status_service import ContractStatusService

class TestContractStatusServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ContractStatusService(mock_db)
        assert hasattr(service, 'db')

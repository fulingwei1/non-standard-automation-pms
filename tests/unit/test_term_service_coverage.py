# -*- coding: utf-8 -*-
"""term_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/contract/term_service import ContractTermService

class TestContractTermServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ContractTermService(mock_db)
        assert hasattr(service, 'db')

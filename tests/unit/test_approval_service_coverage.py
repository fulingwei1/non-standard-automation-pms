# -*- coding: utf-8 -*-
"""approval_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.contract.approval_service import ContractApprovalService

class TestContractApprovalServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ContractApprovalService(mock_db)
        assert hasattr(service, 'db')

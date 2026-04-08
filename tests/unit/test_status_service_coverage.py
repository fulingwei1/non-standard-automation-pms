# -*- coding: utf-8 -*-
"""status_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.contract.status_service import ContractStatusService

class TestContractStatusServiceInit:
    def test_init(self):
        service = ContractStatusService(Mock())
        assert service is not None

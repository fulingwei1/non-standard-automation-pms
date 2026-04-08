# -*- coding: utf-8 -*-
"""term_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.contract.term_service import ContractTermService

class TestContractTermServiceInit:
    def test_init(self):
        service = ContractTermService(Mock())
        assert service is not None

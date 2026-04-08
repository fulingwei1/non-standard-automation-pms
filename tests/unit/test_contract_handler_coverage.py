# -*- coding: utf-8 -*-
"""contract_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.status_handlers.contract_handler import ContractStatusHandler

class TestContractStatusHandlerInit:
    def test_init(self):
        service = ContractStatusHandler(Mock())
        assert service is not None

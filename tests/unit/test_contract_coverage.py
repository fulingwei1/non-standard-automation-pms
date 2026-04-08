# -*- coding: utf-8 -*-
"""contract单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

class TestContractApprovalAdapterInit:
    def test_init(self):
        service = ContractApprovalAdapter(Mock())
        assert service is not None

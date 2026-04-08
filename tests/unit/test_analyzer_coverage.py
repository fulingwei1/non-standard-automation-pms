# -*- coding: utf-8 -*-
"""analyzer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.contract.analyzer import ContractAnalyzer

class TestContractAnalyzerInit:
    def test_init(self):
        service = ContractAnalyzer(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""evm_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.evm_service import EVMCalculator

class TestEVMCalculatorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = EVMCalculator(mock_db)
        assert hasattr(service, 'db')

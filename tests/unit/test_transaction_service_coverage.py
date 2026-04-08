# -*- coding: utf-8 -*-
"""transaction_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.transaction_service import TransactionService

class TestTransactionServiceInit:
    def test_init(self):
        service = TransactionService(Mock())
        assert service is not None

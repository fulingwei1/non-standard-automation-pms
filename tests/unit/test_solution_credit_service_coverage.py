# -*- coding: utf-8 -*-
"""solution_credit_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.solution_credit_service import CreditTransactionType

class TestCreditTransactionTypeInit:
    def test_init(self):
        service = CreditTransactionType(Mock())
        assert service is not None

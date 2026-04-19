# -*- coding: utf-8 -*-
"""transaction_service单元测试"""
from unittest.mock import Mock

from app.services.inventory.transaction_service import TransactionService


class TestTransactionServiceInit:
    def test_init(self):
        service = TransactionService(Mock(), tenant_id=1)
        assert service.db is not None
        assert service.tenant_id == 1

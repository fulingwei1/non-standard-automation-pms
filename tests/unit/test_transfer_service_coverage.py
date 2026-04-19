# -*- coding: utf-8 -*-
"""transfer_service单元测试"""
from unittest.mock import Mock

from app.services.inventory.transfer_service import TransferService


class TestTransferServiceInit:
    def test_init(self):
        service = TransferService(Mock(), tenant_id=1)
        assert service.db is not None
        assert service.tenant_id == 1

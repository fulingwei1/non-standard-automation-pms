# -*- coding: utf-8 -*-
"""transfer_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.transfer_service import TransferService

class TestTransferServiceInit:
    def test_init(self):
        service = TransferService(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""purchase_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.purchase.purchase_service import PurchaseService

class TestPurchaseServiceInit:
    def test_init(self):
        service = PurchaseService(Mock())
        assert service is not None

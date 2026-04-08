# -*- coding: utf-8 -*-
"""purchase单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.adapters.purchase import PurchaseOrderApprovalAdapter

class TestPurchaseOrderApprovalAdapterInit:
    def test_init(self):
        service = PurchaseOrderApprovalAdapter(Mock())
        assert service is not None

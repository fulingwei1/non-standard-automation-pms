# -*- coding: utf-8 -*-
"""invoice单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter

class TestInvoiceApprovalAdapterInit:
    def test_init(self):
        service = InvoiceApprovalAdapter(Mock())
        assert service is not None

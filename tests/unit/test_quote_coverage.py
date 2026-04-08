# -*- coding: utf-8 -*-
"""quote单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter

class TestQuoteApprovalAdapterInit:
    def test_init(self):
        service = QuoteApprovalAdapter(Mock())
        assert service is not None

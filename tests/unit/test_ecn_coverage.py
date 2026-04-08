# -*- coding: utf-8 -*-
"""ecn单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter

class TestEcnApprovalAdapterInit:
    def test_init(self):
        service = EcnApprovalAdapter(Mock())
        assert service is not None

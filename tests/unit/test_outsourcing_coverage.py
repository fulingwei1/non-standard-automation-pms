# -*- coding: utf-8 -*-
"""outsourcing单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.adapters.outsourcing import OutsourcingOrderApprovalAdapter

class TestOutsourcingOrderApprovalAdapterInit:
    def test_init(self):
        service = OutsourcingOrderApprovalAdapter(Mock())
        assert service is not None

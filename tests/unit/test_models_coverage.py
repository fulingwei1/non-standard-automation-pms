# -*- coding: utf-8 -*-
"""models单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.models import ApprovalFlowType

class TestApprovalFlowTypeInit:
    def test_init(self):
        service = ApprovalFlowType(Mock())
        assert service is not None

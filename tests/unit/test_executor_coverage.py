# -*- coding: utf-8 -*-
"""executor单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.executor import ApprovalNodeExecutor

class TestApprovalNodeExecutorInit:
    def test_init(self):
        service = ApprovalNodeExecutor(Mock())
        assert service is not None

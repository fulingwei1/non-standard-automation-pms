# -*- coding: utf-8 -*-
"""execution_logger单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.execution_logger import ApprovalExecutionLogger

class TestApprovalExecutionLoggerInit:
    def test_init(self):
        service = ApprovalExecutionLogger(Mock())
        assert service is not None

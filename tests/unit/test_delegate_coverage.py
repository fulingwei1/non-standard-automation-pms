# -*- coding: utf-8 -*-
"""delegate单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.delegate import ApprovalDelegateService

class TestApprovalDelegateServiceInit:
    def test_init(self):
        service = ApprovalDelegateService(Mock())
        assert service is not None

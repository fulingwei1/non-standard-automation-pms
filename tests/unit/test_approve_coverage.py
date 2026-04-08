# -*- coding: utf-8 -*-
"""approve单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.engine.approve import ApprovalProcessMixin

class TestApprovalProcessMixinInit:
    def test_init(self):
        service = ApprovalProcessMixin(Mock())
        assert service is not None

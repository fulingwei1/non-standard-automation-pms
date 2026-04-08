# -*- coding: utf-8 -*-
"""submit单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.engine.submit import ApprovalSubmitMixin

class TestApprovalSubmitMixinInit:
    def test_init(self):
        service = ApprovalSubmitMixin(Mock())
        assert service is not None

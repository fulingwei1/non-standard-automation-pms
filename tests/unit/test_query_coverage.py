# -*- coding: utf-8 -*-
"""query单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.engine.query import ApprovalQueryMixin

class TestApprovalQueryMixinInit:
    def test_init(self):
        service = ApprovalQueryMixin(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""actions单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.engine.actions import ApprovalActionsMixin

class TestApprovalActionsMixinInit:
    def test_init(self):
        service = ApprovalActionsMixin(Mock())
        assert service is not None

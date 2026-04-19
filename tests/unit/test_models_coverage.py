# -*- coding: utf-8 -*-
"""models单元测试"""
from app.services.approval_engine.models import ApprovalFlowType


class TestApprovalFlowTypeInit:
    def test_init(self):
        assert ApprovalFlowType.SINGLE_LEVEL.value == "SINGLE_LEVEL"

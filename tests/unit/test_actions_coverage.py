# -*- coding: utf-8 -*-
"""actions单元测试"""

from app.services.approval_engine.engine.actions import ApprovalActionsMixin


class TestApprovalActionsMixinInit:
    def test_methods_available(self):
        assert ApprovalActionsMixin is not None
        assert hasattr(ApprovalActionsMixin, "add_cc")
        assert hasattr(ApprovalActionsMixin, "withdraw")

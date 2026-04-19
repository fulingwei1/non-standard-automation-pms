# -*- coding: utf-8 -*-
"""approve单元测试"""

import pytest
from app.services.approval_engine.engine.approve import ApprovalProcessMixin


class TestApprovalProcessMixinInit:
    def test_init(self):
        service = ApprovalProcessMixin()
        assert service is not None

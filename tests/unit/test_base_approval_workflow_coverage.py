# -*- coding: utf-8 -*-
"""base_approval_workflow单元测试"""
import pytest
from app.services.base_approval_workflow import BaseApprovalWorkflowService


class TestBaseApprovalWorkflowServiceInit:
    def test_init_with_db(self):
        assert BaseApprovalWorkflowService is not None
        assert hasattr(BaseApprovalWorkflowService, 'submit_orders_for_approval')
        assert hasattr(BaseApprovalWorkflowService, 'get_pending_tasks')

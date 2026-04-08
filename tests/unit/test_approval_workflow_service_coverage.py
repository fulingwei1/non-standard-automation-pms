# -*- coding: utf-8 -*-
"""approval_workflow_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_workflow_service import ApprovalWorkflowService

class TestApprovalWorkflowServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ApprovalWorkflowService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""base_approval_workflow单元测试"""
import pytest
from unittest.mock import Mock
from app.services.base_approval_workflow import BaseApprovalWorkflowService

class TestBaseApprovalWorkflowServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = BaseApprovalWorkflowService(mock_db)
        assert hasattr(service, 'db')

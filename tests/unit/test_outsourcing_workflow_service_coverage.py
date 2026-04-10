# -*- coding: utf-8 -*-
"""outsourcing_workflow_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.outsourcing_workflow.outsourcing_workflow_service import OutsourcingWorkflowService

class TestOutsourcingWorkflowServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = OutsourcingWorkflowService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""project_data_flow_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_data_flow_service import ProjectDataFlowService

class TestProjectDataFlowServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectDataFlowService(mock_db)
        assert hasattr(service, 'db')

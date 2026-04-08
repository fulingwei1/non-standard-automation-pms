# -*- coding: utf-8 -*-
"""node_task_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.node_task_service import NodeTaskService

class TestNodeTaskServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = NodeTaskService(mock_db)
        assert hasattr(service, 'db')

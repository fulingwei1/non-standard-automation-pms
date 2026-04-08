# -*- coding: utf-8 -*-
"""project_relation_service单元测试"""
import pytest
from unittest.mock import Mock
from services/project_relation_service import ProjectRelationService

class TestProjectRelationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectRelationService(mock_db)
        assert hasattr(service, 'db')

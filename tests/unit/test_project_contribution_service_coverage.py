# -*- coding: utf-8 -*-
"""project_contribution_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_contribution_service import ProjectContributionService

class TestProjectContributionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectContributionService(mock_db)
        assert hasattr(service, 'db')

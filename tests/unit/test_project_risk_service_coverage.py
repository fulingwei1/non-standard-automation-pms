# -*- coding: utf-8 -*-
"""project_risk_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_risk.project_risk_service import ProjectRiskService

class TestProjectRiskServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectRiskService(mock_db)
        assert hasattr(service, 'db')

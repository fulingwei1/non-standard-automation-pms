# -*- coding: utf-8 -*-
"""project_bonus_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bonus.project_bonus_service import ProjectBonusService

class TestProjectBonusServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectBonusService(mock_db)
        assert hasattr(service, 'db')

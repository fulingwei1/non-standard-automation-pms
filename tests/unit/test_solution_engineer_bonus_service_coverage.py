# -*- coding: utf-8 -*-
"""solution_engineer_bonus_service单元测试"""
import pytest
from unittest.mock import Mock
from services/bonus/solution_engineer_bonus_service import SolutionEngineerBonusService

class TestSolutionEngineerBonusServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SolutionEngineerBonusService(mock_db)
        assert hasattr(service, 'db')

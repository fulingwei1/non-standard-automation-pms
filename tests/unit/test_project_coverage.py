# -*- coding: utf-8 -*-
"""project单元测试"""
import pytest
from unittest.mock import Mock
from services/bonus/project import ProjectBonusCalculator

class TestProjectBonusCalculatorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectBonusCalculator(mock_db)
        assert hasattr(service, 'db')

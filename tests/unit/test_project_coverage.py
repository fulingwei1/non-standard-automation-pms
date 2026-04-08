# -*- coding: utf-8 -*-
"""project单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bonus.project import ProjectBonusCalculator

class TestProjectBonusCalculatorInit:
    def test_init(self):
        service = ProjectBonusCalculator(Mock())
        assert service is not None

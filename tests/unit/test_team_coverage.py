# -*- coding: utf-8 -*-
"""team单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bonus.team import TeamBonusCalculator

class TestTeamBonusCalculatorInit:
    def test_init(self):
        service = TeamBonusCalculator(Mock())
        assert service is not None

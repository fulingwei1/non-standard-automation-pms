# -*- coding: utf-8 -*-
"""score_calculators单元测试"""
import pytest
from unittest.mock import Mock
from app.services.staff_matching.score_calculators import SkillScoreCalculator

class TestSkillScoreCalculatorInit:
    def test_init(self):
        service = SkillScoreCalculator(Mock())
        assert service is not None

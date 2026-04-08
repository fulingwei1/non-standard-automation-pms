# -*- coding: utf-8 -*-
"""performance单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bonus.performance import PerformanceBonusCalculator

class TestPerformanceBonusCalculatorInit:
    def test_init(self):
        service = PerformanceBonusCalculator(Mock())
        assert service is not None

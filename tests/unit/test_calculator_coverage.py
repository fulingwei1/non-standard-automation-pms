# -*- coding: utf-8 -*-
"""calculator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bonus.calculator import BonusCalculator

class TestBonusCalculatorInit:
    def test_init(self):
        service = BonusCalculator(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""presale单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bonus.presale import PresaleBonusCalculator

class TestPresaleBonusCalculatorInit:
    def test_init(self):
        service = PresaleBonusCalculator(Mock())
        assert service is not None

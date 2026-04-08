# -*- coding: utf-8 -*-
"""sales单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bonus.sales import SalesBonusCalculator

class TestSalesBonusCalculatorInit:
    def test_init(self):
        service = SalesBonusCalculator(Mock())
        assert service is not None

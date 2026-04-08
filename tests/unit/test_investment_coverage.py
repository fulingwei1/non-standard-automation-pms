# -*- coding: utf-8 -*-
"""investment单元测试"""
import pytest
from unittest.mock import Mock
from app.services.resource_waste_analysis.investment import InvestmentAnalysisMixin

class TestInvestmentAnalysisMixinInit:
    def test_init(self):
        service = InvestmentAnalysisMixin(Mock())
        assert service is not None

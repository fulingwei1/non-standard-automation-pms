# -*- coding: utf-8 -*-
"""salesperson_analysis单元测试"""
import pytest
from unittest.mock import Mock
from app.services.resource_waste_analysis.salesperson_analysis import SalespersonAnalysisMixin

class TestSalespersonAnalysisMixinInit:
    def test_init(self):
        service = SalespersonAnalysisMixin(Mock())
        assert service is not None

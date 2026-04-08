# -*- coding: utf-8 -*-
"""waste_calculation单元测试"""
import pytest
from unittest.mock import Mock
from app.services.resource_waste_analysis.waste_calculation import WasteCalculationMixin

class TestWasteCalculationMixinInit:
    def test_init(self):
        service = WasteCalculationMixin(Mock())
        assert service is not None

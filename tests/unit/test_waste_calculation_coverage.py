# -*- coding: utf-8 -*-
"""waste_calculation单元测试"""
from app.services.resource_waste_analysis.waste_calculation import WasteCalculationMixin


class TestWasteCalculationMixinInit:
    def test_init(self):
        assert hasattr(WasteCalculationMixin, "calculate_waste_by_period")

# -*- coding: utf-8 -*-
"""labor_cost_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.labor_cost_service import LaborCostService

class TestLaborCostServiceInit:
    def test_init(self):
        service = LaborCostService(Mock())
        assert service is not None

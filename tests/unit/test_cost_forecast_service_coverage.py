# -*- coding: utf-8 -*-
"""cost_forecast_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.cost_forecast_service import CostForecastService

class TestCostForecastServiceInit:
    def test_init(self):
        service = CostForecastService(Mock())
        assert service is not None

# -*- coding: utf-8 -*-
"""demand_forecast_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.shortage.demand_forecast_engine import DemandForecastEngine

class TestDemandForecastEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = DemandForecastEngine(mock_db)
        assert hasattr(service, 'db')

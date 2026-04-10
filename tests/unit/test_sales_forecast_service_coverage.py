# -*- coding: utf-8 -*-
"""sales_forecast_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales_forecast_service import SalesForecastService

class TestSalesForecastServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SalesForecastService(mock_db)
        assert hasattr(service, 'db')

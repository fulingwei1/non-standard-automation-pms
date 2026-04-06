# -*- coding: utf-8 -*-
"""
销售预测服务测试（最小版）
"""

import pytest
from unittest.mock import MagicMock


class TestSalesForecastService:
    """销售预测服务测试"""

    def test_service_creation(self):
        """测试服务创建"""
        from app.services.sales_forecast_service import SalesForecastService
        
        mock_db = MagicMock()
        service = SalesForecastService(mock_db)
        
        assert service is not None
        assert service.db == mock_db
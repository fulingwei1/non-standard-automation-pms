# -*- coding: utf-8 -*-
"""sales_prediction_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales_prediction_service import SalesPredictionService

class TestSalesPredictionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SalesPredictionService(mock_db)
        assert hasattr(service, 'db')

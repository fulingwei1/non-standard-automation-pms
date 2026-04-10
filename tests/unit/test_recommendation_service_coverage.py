# -*- coding: utf-8 -*-
"""recommendation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.recommendation_service import SalesRecommendationService

class TestSalesRecommendationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SalesRecommendationService(mock_db)
        assert hasattr(service, 'db')

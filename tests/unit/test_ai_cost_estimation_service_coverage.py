# -*- coding: utf-8 -*-
"""ai_cost_estimation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.ai_cost_estimation_service import AICostEstimationService

class TestAICostEstimationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AICostEstimationService(mock_db)
        assert hasattr(service, 'db')

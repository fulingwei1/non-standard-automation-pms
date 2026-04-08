# -*- coding: utf-8 -*-
"""health_trend_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.health_trend_service import HealthTrendService

class TestHealthTrendServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = HealthTrendService(mock_db)
        assert hasattr(service, 'db')

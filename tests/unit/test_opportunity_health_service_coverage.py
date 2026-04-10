# -*- coding: utf-8 -*-
"""opportunity_health_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.opportunity_health_service import HealthLevel

class TestHealthLevelInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = HealthLevel(mock_db)
        assert hasattr(service, 'db')

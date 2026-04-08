# -*- coding: utf-8 -*-
"""performance_trend_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_trend_service import PerformanceTrendService

class TestPerformanceTrendServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PerformanceTrendService(mock_db)
        assert hasattr(service, 'db')

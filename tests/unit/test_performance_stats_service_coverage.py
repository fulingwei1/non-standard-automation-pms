# -*- coding: utf-8 -*-
"""performance_stats_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_stats_service import PerformanceStatsService

class TestPerformanceStatsServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PerformanceStatsService(mock_db)
        assert hasattr(service, 'db')

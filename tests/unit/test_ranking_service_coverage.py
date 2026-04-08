# -*- coding: utf-8 -*-
"""ranking_service单元测试"""
import pytest
from unittest.mock import Mock
from services/engineer_performance/ranking_service import RankingService

class TestRankingServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = RankingService(mock_db)
        assert hasattr(service, 'db')

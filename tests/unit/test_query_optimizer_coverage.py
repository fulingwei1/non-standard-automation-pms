# -*- coding: utf-8 -*-
"""query_optimizer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.database.query_optimizer import QueryOptimizer

class TestQueryOptimizerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = QueryOptimizer(mock_db)
        assert hasattr(service, 'db')

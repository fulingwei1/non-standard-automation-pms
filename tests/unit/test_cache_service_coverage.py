# -*- coding: utf-8 -*-
"""cache_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cache_service import CacheService

class TestCacheServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = CacheService(mock_db)
        assert hasattr(service, 'db')

# -*- coding: utf-8 -*-
"""redis_cache单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cache.redis_cache import CacheKeys

class TestCacheKeysInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = CacheKeys(mock_db)
        assert hasattr(service, 'db')

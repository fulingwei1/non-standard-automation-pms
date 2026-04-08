# -*- coding: utf-8 -*-
"""business_cache单元测试"""
import pytest
from unittest.mock import Mock
from services/cache/business_cache import BusinessCacheService

class TestBusinessCacheServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = BusinessCacheService(mock_db)
        assert hasattr(service, 'db')

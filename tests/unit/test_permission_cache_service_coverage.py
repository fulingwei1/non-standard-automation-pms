# -*- coding: utf-8 -*-
"""permission_cache_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.permission_management.permission_cache_service import PermissionCacheService

class TestPermissionCacheServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PermissionCacheService(mock_db)
        assert hasattr(service, 'db')

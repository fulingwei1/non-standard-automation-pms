# -*- coding: utf-8 -*-
"""Tests for app/services/cache/business_cache.py"""
from unittest.mock import MagicMock, patch


class TestBusinessCacheService:
    @patch("app.services.cache.business_cache.get_cache")
    def test_get_project_list_cache_miss(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        from app.services.cache.business_cache import BusinessCacheService
        service = BusinessCacheService()
        result = service.get_project_list(skip=0, limit=10)
        assert result is None

    @patch("app.services.cache.business_cache.get_cache")
    def test_get_project_list_cache_hit(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_cache.get.return_value = [{"id": 1}]
        mock_get_cache.return_value = mock_cache

        from app.services.cache.business_cache import BusinessCacheService
        service = BusinessCacheService()
        result = service.get_project_list(skip=0, limit=10)
        assert result == [{"id": 1}]

    @patch("app.services.cache.business_cache.get_cache")
    def test_set_project_list(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        from app.services.cache.business_cache import BusinessCacheService
        service = BusinessCacheService()
        service.set_project_list([MagicMock()], skip=0, limit=10)
        mock_cache.set.assert_called_once()

    @patch("app.services.cache.business_cache.get_cache")
    def test_get_project_dashboard(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_cache.get.return_value = {"stats": 42}
        mock_get_cache.return_value = mock_cache

        from app.services.cache.business_cache import BusinessCacheService
        service = BusinessCacheService()
        result = service.get_project_dashboard(1)
        assert result == {"stats": 42}

    @patch("app.services.cache.business_cache.get_cache")
    def test_get_user_permissions(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_cache.get.return_value = ["read", "write"]
        mock_get_cache.return_value = mock_cache

        from app.services.cache.business_cache import BusinessCacheService
        service = BusinessCacheService()
        result = service.get_user_permissions(1)
        assert result == ["read", "write"]

# -*- coding: utf-8 -*-
"""
Unit tests for PermissionCacheService (第三十批)
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.permission_cache_service import PermissionCacheService


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton instance before each test"""
    PermissionCacheService._instance = None
    yield
    PermissionCacheService._instance = None


@pytest.fixture
def service():
    with patch("app.services.permission_cache_service.CacheService") as MockCache:
        mock_cache = MagicMock()
        MockCache.return_value = mock_cache
        svc = PermissionCacheService()
        svc._cache = mock_cache
        return svc, mock_cache


# ---------------------------------------------------------------------------
# Singleton pattern
# ---------------------------------------------------------------------------

class TestSingleton:
    def test_same_instance_returned(self):
        with patch("app.services.permission_cache_service.CacheService"):
            svc1 = PermissionCacheService()
            svc2 = PermissionCacheService()
            assert svc1 is svc2


# ---------------------------------------------------------------------------
# _build_key
# ---------------------------------------------------------------------------

class TestBuildKey:
    def test_builds_key_with_tenant_id(self, service):
        svc, _ = service
        key = svc._build_key("perm:t{tenant_id}:user", tenant_id=1, resource_id=42)
        assert "t1" in key
        assert "42" in key

    def test_builds_key_with_none_tenant_id(self, service):
        svc, _ = service
        key = svc._build_key("perm:t{tenant_id}:user", tenant_id=None, resource_id=10)
        assert "system" in key
        assert "10" in key


# ---------------------------------------------------------------------------
# User permissions cache
# ---------------------------------------------------------------------------

class TestUserPermissionsCache:
    def test_get_user_permissions_returns_set_when_cached(self, service):
        svc, mock_cache = service
        mock_cache.get.return_value = ["perm:read", "perm:write"]

        result = svc.get_user_permissions(user_id=1, tenant_id=1)
        assert isinstance(result, set)
        assert "perm:read" in result

    def test_get_user_permissions_returns_none_when_not_cached(self, service):
        svc, mock_cache = service
        mock_cache.get.return_value = None

        result = svc.get_user_permissions(user_id=1)
        assert result is None

    def test_set_user_permissions_calls_cache_set(self, service):
        svc, mock_cache = service
        mock_cache.set.return_value = True

        result = svc.set_user_permissions(user_id=1, permissions={"perm:read"}, tenant_id=1)
        mock_cache.set.assert_called_once()
        assert result is True

    def test_invalidate_user_permissions_calls_cache_delete(self, service):
        svc, mock_cache = service
        mock_cache.delete.return_value = True

        result = svc.invalidate_user_permissions(user_id=1, tenant_id=1)
        mock_cache.delete.assert_called_once()
        assert result is True

    def test_invalidate_tenant_user_permissions(self, service):
        svc, mock_cache = service
        mock_cache.delete_pattern.return_value = 5

        result = svc.invalidate_tenant_user_permissions(tenant_id=2)
        mock_cache.delete_pattern.assert_called_once_with("perm:t2:user:*")
        assert result == 5

    def test_invalidate_all_user_permissions(self, service):
        svc, mock_cache = service
        mock_cache.delete_pattern.return_value = 20

        result = svc.invalidate_all_user_permissions()
        mock_cache.delete_pattern.assert_called_once_with("perm:t*:user:*")
        assert result == 20


# ---------------------------------------------------------------------------
# Role permissions cache
# ---------------------------------------------------------------------------

class TestRolePermissionsCache:
    def test_get_role_permissions_returns_cached_data(self, service):
        svc, mock_cache = service
        cached = {"permissions": ["admin:read"]}
        mock_cache.get.return_value = cached

        result = svc.get_role_permissions(role_id=10, tenant_id=1)
        assert result == cached

    def test_set_role_permissions_calls_cache_set(self, service):
        svc, mock_cache = service
        mock_cache.set.return_value = True

        data = {"permissions": ["admin:write"]}
        result = svc.set_role_permissions(role_id=10, data=data, tenant_id=1)
        mock_cache.set.assert_called_once()

    def test_invalidate_role_permissions(self, service):
        svc, mock_cache = service
        mock_cache.delete.return_value = True

        result = svc.invalidate_role_permissions(role_id=10, tenant_id=1)
        mock_cache.delete.assert_called_once()

    def test_invalidate_all_role_permissions(self, service):
        svc, mock_cache = service
        mock_cache.delete_pattern.return_value = 8

        result = svc.invalidate_all_role_permissions()
        mock_cache.delete_pattern.assert_called_once_with("perm:t*:role:*")


# ---------------------------------------------------------------------------
# User-role association cache
# ---------------------------------------------------------------------------

class TestUserRoleCache:
    def test_get_user_role_ids(self, service):
        svc, mock_cache = service
        mock_cache.get.return_value = [1, 2, 3]

        result = svc.get_user_role_ids(user_id=1, tenant_id=1)
        assert result == [1, 2, 3]

    def test_set_user_role_ids(self, service):
        svc, mock_cache = service
        mock_cache.set.return_value = True

        result = svc.set_user_role_ids(user_id=1, role_ids=[1, 2], tenant_id=1)
        mock_cache.set.assert_called_once()

    def test_get_role_user_ids(self, service):
        svc, mock_cache = service
        mock_cache.get.return_value = [10, 20]

        result = svc.get_role_user_ids(role_id=5, tenant_id=1)
        assert result == [10, 20]

    def test_set_role_user_ids(self, service):
        svc, mock_cache = service
        mock_cache.set.return_value = True

        result = svc.set_role_user_ids(role_id=5, user_ids=[10, 20], tenant_id=1)
        mock_cache.set.assert_called_once()


# ---------------------------------------------------------------------------
# invalidate_role_and_users
# ---------------------------------------------------------------------------

class TestInvalidateRoleAndUsers:
    def test_invalidates_role_and_specified_users(self, service):
        svc, mock_cache = service
        mock_cache.delete.return_value = True

        count = svc.invalidate_role_and_users(role_id=5, user_ids=[1, 2, 3], tenant_id=1)
        # Should call delete for role + each user + user_roles cache
        assert mock_cache.delete.call_count >= 1

    def test_invalidates_role_without_user_ids(self, service):
        svc, mock_cache = service
        mock_cache.delete.return_value = True

        count = svc.invalidate_role_and_users(role_id=5, tenant_id=1)
        assert mock_cache.delete.call_count >= 1

# -*- coding: utf-8 -*-
"""
app/services/permission_cache_service.py 覆盖率测试（当前 41%）
"""
import pytest
from unittest.mock import MagicMock, patch


class TestPermissionCacheService:
    """测试 PermissionCacheService"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """每个测试前重置单例"""
        from app.services.permission_cache_service import PermissionCacheService
        PermissionCacheService._instance = None
        yield
        PermissionCacheService._instance = None

    @pytest.fixture
    def mock_cache(self):
        with patch("app.services.permission_cache_service.CacheService") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def svc(self, mock_cache):
        from app.services.permission_cache_service import PermissionCacheService
        return PermissionCacheService()

    # ── 基础测试 ──────────────────────────────────

    def test_singleton(self, mock_cache):
        from app.services.permission_cache_service import PermissionCacheService
        s1 = PermissionCacheService()
        s2 = PermissionCacheService()
        assert s1 is s2

    def test_build_key_with_tenant(self, svc):
        from app.services.permission_cache_service import CACHE_PREFIX_USER_PERMISSIONS
        key = svc._build_key(CACHE_PREFIX_USER_PERMISSIONS, tenant_id=5, resource_id=42)
        assert "5" in key
        assert "42" in key

    def test_build_key_without_tenant(self, svc):
        from app.services.permission_cache_service import CACHE_PREFIX_USER_PERMISSIONS
        key = svc._build_key(CACHE_PREFIX_USER_PERMISSIONS, tenant_id=None, resource_id=1)
        assert "system" in key
        assert "1" in key

    # ── 用户权限缓存 ──────────────────────────────

    def test_get_user_permissions_miss(self, svc, mock_cache):
        mock_cache.get.return_value = None
        result = svc.get_user_permissions(tenant_id=1, user_id=10)
        assert result is None

    def test_get_user_permissions_hit(self, svc, mock_cache):
        mock_cache.get.return_value = {"view", "edit"}
        result = svc.get_user_permissions(tenant_id=1, user_id=10)
        assert result == {"view", "edit"}

    def test_set_user_permissions(self, svc, mock_cache):
        perms = {"view", "edit", "delete"}
        svc.set_user_permissions(tenant_id=1, user_id=10, permissions=perms)
        mock_cache.set.assert_called_once()

    def test_invalidate_user_permissions(self, svc, mock_cache):
        mock_cache.delete.return_value = True
        svc.invalidate_user_permissions(tenant_id=1, user_id=10)
        mock_cache.delete.assert_called_once()

    def test_invalidate_tenant_user_permissions(self, svc, mock_cache):
        mock_cache.delete_pattern.return_value = 5
        result = svc.invalidate_tenant_user_permissions(tenant_id=1)
        mock_cache.delete_pattern.assert_called()
        assert isinstance(result, int)

    def test_invalidate_all_user_permissions(self, svc, mock_cache):
        mock_cache.delete_pattern.return_value = 10
        result = svc.invalidate_all_user_permissions()
        assert isinstance(result, int)

    # ── 角色权限缓存 ──────────────────────────────

    def test_get_role_permissions_miss(self, svc, mock_cache):
        mock_cache.get.return_value = None
        result = svc.get_role_permissions(tenant_id=1, role_id=5)
        assert result is None

    def test_set_role_permissions(self, svc, mock_cache):
        svc.set_role_permissions(role_id=5, data={"permissions": ["read"]}, tenant_id=1)
        mock_cache.set.assert_called_once()

    def test_invalidate_role_permissions(self, svc, mock_cache):
        mock_cache.delete.return_value = True
        svc.invalidate_role_permissions(tenant_id=1, role_id=5)
        mock_cache.delete.assert_called_once()

    def test_invalidate_tenant_role_permissions(self, svc, mock_cache):
        mock_cache.delete_pattern.return_value = 3
        result = svc.invalidate_tenant_role_permissions(tenant_id=1)
        assert isinstance(result, int)

    def test_invalidate_all_role_permissions(self, svc, mock_cache):
        mock_cache.delete_pattern.return_value = 7
        result = svc.invalidate_all_role_permissions()
        assert isinstance(result, int)

    # ── 用户角色缓存 ──────────────────────────────

    def test_get_user_role_ids_miss(self, svc, mock_cache):
        mock_cache.get.return_value = None
        result = svc.get_user_role_ids(tenant_id=1, user_id=10)
        assert result is None

    def test_set_user_role_ids(self, svc, mock_cache):
        svc.set_user_role_ids(tenant_id=1, user_id=10, role_ids=[1, 2, 3])
        mock_cache.set.assert_called_once()

    def test_get_role_user_ids_miss(self, svc, mock_cache):
        mock_cache.get.return_value = None
        result = svc.get_role_user_ids(tenant_id=1, role_id=5)
        assert result is None

    def test_set_role_user_ids(self, svc, mock_cache):
        svc.set_role_user_ids(tenant_id=1, role_id=5, user_ids=[10, 20])
        mock_cache.set.assert_called_once()

    # ── 组合失效 ──────────────────────────────────

    def test_invalidate_role_and_users(self, svc, mock_cache):
        mock_cache.delete.return_value = True
        mock_cache.get.return_value = [10, 20]
        mock_cache.delete_pattern.return_value = 2
        result = svc.invalidate_role_and_users(tenant_id=1, role_id=5)
        assert isinstance(result, int)

    def test_invalidate_user_role_change(self, svc, mock_cache):
        mock_cache.delete.return_value = True
        mock_cache.delete_pattern.return_value = 1
        result = svc.invalidate_user_role_change(
            user_id=10,
            old_role_ids=[1, 2],
            new_role_ids=[3, 4],
            tenant_id=1
        )
        assert isinstance(result, int)

    def test_invalidate_tenant(self, svc, mock_cache):
        mock_cache.delete_pattern.return_value = 20
        result = svc.invalidate_tenant(tenant_id=1)
        assert isinstance(result, int)

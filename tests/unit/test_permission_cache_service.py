# -*- coding: utf-8 -*-
"""权限缓存服务测试。"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.permission_management import permission_cache_service as cache_module


@pytest.fixture(autouse=True)
def reset_singletons():
    cache_module.PermissionCacheService._instance = None
    cache_module._permission_cache_service = None
    yield
    cache_module.PermissionCacheService._instance = None
    cache_module._permission_cache_service = None


@pytest.fixture
def mock_cache():
    with patch.object(cache_module, "CacheService") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def svc(mock_cache):
    return cache_module.PermissionCacheService()


class TestPermissionCacheService:
    def test_singleton(self, mock_cache):
        service1 = cache_module.PermissionCacheService()
        service2 = cache_module.PermissionCacheService()

        assert service1 is service2

    def test_build_key_supports_tenant_and_system_scope(self, svc):
        assert svc._build_key(cache_module.CACHE_PREFIX_USER_PERMISSIONS, 5, 42) == "perm:t5:user:42"
        assert (
            svc._build_key(cache_module.CACHE_PREFIX_USER_PERMISSIONS, None, 7)
            == "perm:tsystem:user:7"
        )

    def test_user_permission_cache_round_trip(self, svc, mock_cache):
        mock_cache.get.return_value = ["view", "edit"]

        assert svc.get_user_permissions(10, tenant_id=1) == {"view", "edit"}
        svc.set_user_permissions(10, {"view"}, tenant_id=1)
        svc.invalidate_user_permissions(10, tenant_id=1)

        mock_cache.set.assert_called_once_with("perm:t1:user:10", ["view"], cache_module.PERMISSION_CACHE_TTL)
        mock_cache.delete.assert_called_once_with("perm:t1:user:10")

    def test_invalidate_all_user_permissions_uses_global_pattern(self, svc, mock_cache):
        mock_cache.delete_pattern.return_value = 6

        assert svc.invalidate_all_user_permissions() == 6
        mock_cache.delete_pattern.assert_called_once_with("perm:t*:user:*")

    def test_role_permission_cache_and_invalidation_patterns(self, svc, mock_cache):
        mock_cache.get.return_value = {"permissions": ["role:read"]}

        assert svc.get_role_permissions(5, tenant_id=2) == {"permissions": ["role:read"]}
        svc.set_role_permissions(5, {"permissions": ["role:write"]}, tenant_id=2)
        svc.invalidate_role_permissions(5, tenant_id=2)
        svc.invalidate_tenant_role_permissions(tenant_id=2)
        svc.invalidate_all_role_permissions()

        mock_cache.set.assert_called_once_with(
            "perm:t2:role:5", {"permissions": ["role:write"]}, cache_module.ROLE_CACHE_TTL
        )
        assert mock_cache.delete.call_args_list[0].args == ("perm:t2:role:5",)
        assert mock_cache.delete_pattern.call_args_list[0].args == ("perm:t2:role:*",)
        assert mock_cache.delete_pattern.call_args_list[1].args == ("perm:t*:role:*",)

    def test_role_and_user_link_caches(self, svc, mock_cache):
        mock_cache.get.side_effect = [[1, 2], [10, 20]]

        assert svc.get_user_role_ids(10, tenant_id=3) == [1, 2]
        svc.set_user_role_ids(10, [1, 2], tenant_id=3)
        assert svc.get_role_user_ids(8, tenant_id=3) == [10, 20]
        svc.set_role_user_ids(8, [10, 20], tenant_id=3)

        assert mock_cache.set.call_args_list[0].args == (
            "perm:t3:user_roles:10",
            [1, 2],
            cache_module.PERMISSION_CACHE_TTL,
        )
        assert mock_cache.set.call_args_list[1].args == (
            "perm:t3:role_users:8",
            [10, 20],
            cache_module.ROLE_CACHE_TTL,
        )

    def test_invalidate_role_and_users_loads_cached_users_when_not_provided(self, svc, mock_cache):
        mock_cache.get.return_value = [11, 12]

        count = svc.invalidate_role_and_users(9, tenant_id=4)

        assert count == 4
        delete_calls = [call.args[0] for call in mock_cache.delete.call_args_list]
        assert delete_calls == [
            "perm:t4:role:9",
            "perm:t4:user:11",
            "perm:t4:user:12",
            "perm:t4:role_users:9",
        ]

    def test_invalidate_user_role_change_clears_user_and_changed_role_links(self, svc, mock_cache):
        count = svc.invalidate_user_role_change(
            user_id=15,
            old_role_ids=[1, 2],
            new_role_ids=[2, 3],
            tenant_id=6,
        )

        assert count == 4
        deleted_keys = [call.args[0] for call in mock_cache.delete.call_args_list]
        assert deleted_keys == [
            "perm:t6:user:15",
            "perm:t6:user_roles:15",
            "perm:t6:role_users:1",
            "perm:t6:role_users:3",
        ]

    def test_invalidate_tenant_and_stats(self, svc, mock_cache):
        mock_cache.delete_pattern.return_value = 9
        mock_cache.get_stats.return_value = {"backend": "memory"}

        assert svc.invalidate_tenant(7) == 9
        assert svc.get_stats() == {
            "backend": "memory",
            "cache_type": "permission",
            "ttl_user": cache_module.PERMISSION_CACHE_TTL,
            "ttl_role": cache_module.ROLE_CACHE_TTL,
            "tenant_isolation": True,
        }

        mock_cache.delete_pattern.assert_called_once_with("perm:t7:*")

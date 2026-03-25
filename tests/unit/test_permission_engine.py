# -*- coding: utf-8 -*-
"""
Tests for the unified permission engine (app/core/permission_engine.py).

The engine consolidates DB+cache logic only. Privilege bypass (superuser,
system admin) stays at the caller level (auth.py / PermissionService).
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.permission_engine import (
    _load_permissions_from_db,
    check_all_permissions_for_user,
    check_any_permission_for_user,
    check_permission_for_user,
    load_permissions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id=1, is_superuser=False, tenant_id=100):
    user = MagicMock()
    user.id = user_id
    user.username = f"user_{user_id}"
    user.is_superuser = is_superuser
    user.is_tenant_admin = False
    user.tenant_id = tenant_id
    user.roles = []
    return user


# ---------------------------------------------------------------------------
# check_permission_for_user (pure data layer, no privilege bypass)
# ---------------------------------------------------------------------------

class TestCheckPermissionForUser:
    @patch("app.core.permission_engine.load_permissions")
    def test_has_permission(self, mock_load):
        mock_load.return_value = {"sales:read", "sales:create"}
        db = MagicMock()
        assert check_permission_for_user(1, "sales:read", db, tenant_id=42) is True
        mock_load.assert_called_with(1, db, 42)

    @patch("app.core.permission_engine.load_permissions")
    def test_lacks_permission(self, mock_load):
        mock_load.return_value = {"sales:read"}
        db = MagicMock()
        assert check_permission_for_user(1, "sales:delete", db) is False


class TestCheckAnyForUser:
    @patch("app.core.permission_engine.load_permissions")
    def test_has_one(self, mock_load):
        mock_load.return_value = {"a:1"}
        assert check_any_permission_for_user(1, ["a:1", "b:2"], MagicMock()) is True

    @patch("app.core.permission_engine.load_permissions")
    def test_has_none(self, mock_load):
        mock_load.return_value = {"c:3"}
        assert check_any_permission_for_user(1, ["a:1", "b:2"], MagicMock()) is False


class TestCheckAllForUser:
    @patch("app.core.permission_engine.load_permissions")
    def test_has_all(self, mock_load):
        mock_load.return_value = {"a:1", "b:2"}
        assert check_all_permissions_for_user(1, ["a:1", "b:2"], MagicMock()) is True

    @patch("app.core.permission_engine.load_permissions")
    def test_missing_one(self, mock_load):
        mock_load.return_value = {"a:1"}
        assert check_all_permissions_for_user(1, ["a:1", "b:2"], MagicMock()) is False


# ---------------------------------------------------------------------------
# load_permissions (cache integration)
# ---------------------------------------------------------------------------

class TestLoadPermissions:
    @patch("app.core.permission_engine._load_permissions_from_db")
    @patch("app.services.permission_cache_service.get_permission_cache_service")
    def test_cache_hit(self, mock_get_cache, mock_db_load):
        """When cache has data, DB should NOT be queried."""
        cache = MagicMock()
        cache.get_user_permissions.return_value = {"cached:perm"}
        mock_get_cache.return_value = cache

        result = load_permissions(1, MagicMock(), tenant_id=10)

        assert result == {"cached:perm"}
        mock_db_load.assert_not_called()

    @patch("app.core.permission_engine._load_permissions_from_db")
    @patch("app.services.permission_cache_service.get_permission_cache_service")
    def test_cache_miss_loads_from_db(self, mock_get_cache, mock_db_load):
        """When cache misses, DB is queried and result is cached."""
        cache = MagicMock()
        cache.get_user_permissions.return_value = None
        mock_get_cache.return_value = cache
        mock_db_load.return_value = {"db:perm1", "db:perm2"}
        db = MagicMock()

        result = load_permissions(1, db, tenant_id=10)

        assert result == {"db:perm1", "db:perm2"}
        mock_db_load.assert_called_once_with(1, db, 10)
        cache.set_user_permissions.assert_called_once_with(1, {"db:perm1", "db:perm2"}, 10)


# ---------------------------------------------------------------------------
# Integration: auth.py delegation
# ---------------------------------------------------------------------------

class TestAuthDelegation:
    """Verify that auth.py's check_permission delegates to the engine for data loading."""

    @patch("app.core.permission_engine.load_permissions")
    def test_auth_check_permission_uses_engine(self, mock_load):
        mock_load.return_value = {"some:perm"}
        from app.core.auth import check_permission as auth_check

        user = _make_user()
        db = MagicMock()
        result = auth_check(user, "some:perm", db)

        assert result is True
        mock_load.assert_called_once_with(user.id, db, user.tenant_id)

    def test_auth_check_permission_superuser_bypass(self):
        """Superuser should NOT hit the engine at all."""
        from app.core.auth import check_permission as auth_check

        user = _make_user(is_superuser=True, tenant_id=None)
        # No db needed — should bypass
        assert auth_check(user, "any:perm", db=None) is True

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
    @patch("app.core.permission_engine._current_permission_cache_revision", return_value=7)
    @patch("app.core.permission_engine._load_permissions_from_db")
    @patch("app.services.permission_management.permission_cache_service.get_permission_cache_service")
    def test_cache_hit(self, mock_get_cache, mock_db_load, mock_revision):
        """When cache has data, DB should NOT be queried."""
        cache = MagicMock()
        cache.get_user_permissions.return_value = {"cached:perm"}
        mock_get_cache.return_value = cache

        result = load_permissions(1, MagicMock(), tenant_id=10)

        assert result == {"cached:perm"}
        mock_revision.assert_called_once()
        cache.get_user_permissions.assert_called_once_with(1, 10, revision=7)
        mock_db_load.assert_not_called()

    @patch("app.core.permission_engine._current_permission_cache_revision", return_value=7)
    @patch("app.core.permission_engine._load_permissions_from_db")
    @patch("app.services.permission_management.permission_cache_service.get_permission_cache_service")
    def test_cache_miss_loads_from_db(self, mock_get_cache, mock_db_load, mock_revision):
        """When cache misses, DB is queried and result is cached."""
        cache = MagicMock()
        cache.get_user_permissions.return_value = None
        mock_get_cache.return_value = cache
        mock_db_load.return_value = {"db:perm1", "db:perm2"}
        db = MagicMock()

        result = load_permissions(1, db, tenant_id=10)

        assert result == {"db:perm1", "db:perm2"}
        mock_revision.assert_called_once()
        cache.get_user_permissions.assert_called_once_with(1, 10, revision=7)
        mock_db_load.assert_called_once_with(1, db, 10)
        cache.set_user_permissions.assert_called_once_with(
            1,
            {"db:perm1", "db:perm2"},
            10,
            revision=7,
        )

    def test_inactive_assigned_permission_is_denied_with_warning(self, db_session, caplog):
        """PERM-12: disabled permission codes must not silently disappear."""
        import logging

        from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole

        user = User(
            username="perm12_user",
            email="perm12@example.com",
            password_hash="x",
            is_active=True,
        )
        role = Role(role_code="PERM12_ROLE", role_name="PERM12 Role", is_active=True)
        inactive_permission = ApiPermission(
            perm_code="sales:export",
            perm_name="Sales Export",
            module="sales",
            is_active=False,
        )
        active_permission = ApiPermission(
            perm_code="sales:read",
            perm_name="Sales Read",
            module="sales",
            is_active=True,
        )
        db_session.add_all([user, role, inactive_permission, active_permission])
        db_session.flush()
        db_session.add_all(
            [
                UserRole(user_id=user.id, role_id=role.id),
                RoleApiPermission(role_id=role.id, permission_id=inactive_permission.id),
                RoleApiPermission(role_id=role.id, permission_id=active_permission.id),
            ]
        )
        db_session.commit()

        with caplog.at_level(logging.WARNING, logger="app.core.permission_engine"):
            permissions = _load_permissions_from_db(user.id, db_session)

        assert permissions == {"sales:read"}
        assert "Inactive API permissions assigned to user" in caplog.text
        assert "sales:export" in caplog.text


# ---------------------------------------------------------------------------
# Integration: auth.py delegation
# ---------------------------------------------------------------------------

class TestAuthDelegation:
    """Verify that auth.py's check_permission delegates to the engine for data loading."""

    @patch("app.core.auth._load_user_permissions_from_db")
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

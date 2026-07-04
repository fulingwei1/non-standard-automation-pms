from unittest.mock import MagicMock, patch

from app.services.role_management.service import RoleManagementService


def test_role_permission_invalidation_queries_affected_users():
    """PERM-13: role permission updates must invalidate affected user caches."""
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.all.return_value = [(101,), (202,)]
    cache_service = MagicMock()

    with patch(
        "app.services.permission_management.permission_cache_service.get_permission_cache_service",
        return_value=cache_service,
    ):
        RoleManagementService(db)._invalidate_permission_cache(role_id=7, tenant_id=3)

    cache_service.invalidate_role_and_users.assert_called_once_with(
        7,
        user_ids=[101, 202],
        tenant_id=3,
    )


def test_permission_engine_ignores_stale_revisioned_cache(monkeypatch):
    """PERM-13: another worker's stale memory cache must not survive a DB revision bump."""
    from app.core import permission_engine

    class FakePermissionCache:
        def __init__(self):
            self.set_calls = []

        def get_user_permissions(self, user_id, tenant_id=None, revision=None):
            if revision is None:
                return {"old:read"}
            if revision == 1:
                return {"old:read"}
            return None

        def set_user_permissions(self, user_id, permissions, tenant_id=None, revision=None):
            self.set_calls.append((user_id, set(permissions), tenant_id, revision))
            return True

    fake_cache = FakePermissionCache()
    monkeypatch.setattr(
        "app.services.permission_management.permission_cache_service.get_permission_cache_service",
        lambda: fake_cache,
    )
    monkeypatch.setattr(
        permission_engine,
        "_current_permission_cache_revision",
        lambda db, tenant_id: 2,
    )
    monkeypatch.setattr(
        permission_engine,
        "_load_permissions_from_db",
        lambda user_id, db, tenant_id: {"fresh:read"},
    )

    permissions = permission_engine.load_permissions(9, MagicMock(), tenant_id=3)

    assert permissions == {"fresh:read"}
    assert fake_cache.set_calls == [(9, {"fresh:read"}, 3, 2)]


def test_auth_check_permission_uses_revisioned_permission_engine(monkeypatch):
    """PERM-13: auth.check_permission must not bypass revisioned cache checks."""
    from app.core import auth

    user = MagicMock()
    user.id = 9
    user.username = "perm13"
    user.is_superuser = False
    user.is_tenant_admin = False
    user.tenant_id = 3
    user.roles = []

    class StaleCache:
        def get_user_permissions(self, user_id, tenant_id=None):
            return {"old:read"}

    monkeypatch.setattr(
        "app.services.permission_cache_service.get_permission_cache_service",
        lambda: StaleCache(),
    )
    monkeypatch.setattr(
        auth,
        "_load_user_permissions_from_db",
        lambda user_id, db, tenant_id: {"fresh:read"},
    )

    assert auth.check_permission(user, "fresh:read", db=MagicMock()) is True

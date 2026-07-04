from unittest.mock import MagicMock


def _user():
    user = MagicMock()
    user.id = 14
    user.username = "perm14"
    user.is_superuser = False
    user.is_tenant_admin = False
    user.tenant_id = 3
    user.roles = []
    return user


def test_auth_check_permission_accepts_view_alias_from_db(monkeypatch):
    from app.core import auth

    monkeypatch.setattr(
        auth,
        "_load_user_permissions_from_db",
        lambda user_id, db, tenant_id: {"project:view"},
    )

    assert auth.check_permission(_user(), "project:read", db=MagicMock()) is True


def test_auth_check_permission_accepts_view_alias_from_cache(monkeypatch):
    from app.core import auth

    class Cache:
        def get_user_permissions(self, user_id, tenant_id=None):
            return {"project:view"}

    monkeypatch.setattr(
        "app.services.permission_cache_service.get_permission_cache_service",
        lambda: Cache(),
    )

    assert auth.check_permission(_user(), "project:read", db=None) is True


def test_permission_engine_check_permission_accepts_view_alias(monkeypatch):
    from app.core import permission_engine

    monkeypatch.setattr(
        permission_engine,
        "load_permissions",
        lambda user_id, db, tenant_id=None: {"project:view"},
    )

    assert (
        permission_engine.check_permission_for_user(
            14,
            "project:read",
            MagicMock(),
            tenant_id=3,
        )
        is True
    )

# -*- coding: utf-8 -*-
"""用户角色分配的租户安全测试。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.users.utils import replace_user_roles
from app.models.user import Role, User, UserRole


def _build_db(target_user, roles, old_role_ids=None):
    db = MagicMock()

    user_query = MagicMock()
    user_query.filter.return_value.first.return_value = target_user

    old_links = [SimpleNamespace(role_id=role_id) for role_id in (old_role_ids or [])]
    user_role_query = MagicMock()
    user_role_query.filter.return_value.all.return_value = old_links
    user_role_query.filter.return_value.delete.return_value = len(old_links)

    role_query = MagicMock()
    role_query.filter.return_value.all.return_value = roles

    def query_side_effect(model):
        if model is User:
            return user_query
        if model is UserRole:
            return user_role_query
        if model is Role:
            return role_query
        raise AssertionError(f"unexpected model: {model}")

    db.query.side_effect = query_side_effect
    return db


def test_replace_user_roles_invalidates_cache_with_target_tenant():
    target_user = SimpleNamespace(id=7, tenant_id=11)
    shared_role = SimpleNamespace(id=20, role_code="PM", tenant_id=None, is_system=False)
    acting_user = SimpleNamespace(id=1, tenant_id=11, is_superuser=False)
    db = _build_db(target_user=target_user, roles=[shared_role], old_role_ids=[9])
    cache_service = MagicMock()

    with patch(
        "app.services.permission_cache_service.get_permission_cache_service",
        return_value=cache_service,
    ):
        replace_user_roles(db, user_id=7, role_ids=[20], acting_user=acting_user)

    cache_service.invalidate_user_role_change.assert_called_once_with(
        7,
        [9],
        [20],
        tenant_id=11,
    )


def test_replace_user_roles_rejects_cross_tenant_role_assignment():
    target_user = SimpleNamespace(id=7, tenant_id=11)
    other_tenant_role = SimpleNamespace(id=30, role_code="TENANT_B_PM", tenant_id=22, is_system=False)
    acting_user = SimpleNamespace(id=1, tenant_id=11, is_superuser=False)
    db = _build_db(target_user=target_user, roles=[other_tenant_role], old_role_ids=[9])

    with pytest.raises(HTTPException) as exc_info:
        replace_user_roles(db, user_id=7, role_ids=[30], acting_user=acting_user)

    assert exc_info.value.status_code == 403
    db.add.assert_not_called()

# -*- coding: utf-8 -*-
"""权限码与数据范围统一的回归测试。"""

import json
from unittest.mock import MagicMock, patch

from app.core.auth import check_permission
from app.models.permission import DataScopeRule
from app.services.data_scope.user_scope import UserScopeService
from app.services.permission_service import PermissionService


def _build_user(*, user_id: int = 1, tenant_id: int = 10, roles=None):
    user = MagicMock()
    user.id = user_id
    user.username = "tester"
    user.is_superuser = False
    user.tenant_id = tenant_id
    user.roles = roles or []
    return user


def _build_role(scope: str):
    role = MagicMock()
    role.is_active = True
    role.data_scope = scope

    user_role = MagicMock()
    user_role.role = role
    return user_role


def test_auth_check_permission_accepts_legacy_view_permission_codes():
    user = _build_user()
    db = MagicMock()

    with patch(
        "app.services.permission_cache_service.get_permission_cache_service"
    ) as mock_cache, patch("app.core.auth._load_user_permissions_from_db") as mock_load:
        mock_cache.return_value.get_user_permissions.return_value = None
        mock_load.return_value = {"project:view"}

        assert check_permission(user, "project:read", db) is True
        assert check_permission(user, "project:view", db) is True


def test_permission_service_get_user_permissions_canonicalizes_cached_view_codes():
    db = MagicMock()
    cache_service = MagicMock()
    cache_service.get_user_permissions.return_value = {"project:view", "task:view"}

    with patch(
        "app.services.permission_service.get_permission_cache_service",
        return_value=cache_service,
    ):
        permissions = PermissionService.get_user_permissions(db, user_id=1, tenant_id=10)

    assert set(permissions) == {"project:read", "task:read"}


def test_user_scope_normalizes_department_alias():
    db = MagicMock()
    user = _build_user(roles=[_build_role("DEPARTMENT")])

    assert UserScopeService.get_user_data_scope(db, user) == "DEPT"


def test_user_scope_preserves_custom_scope_when_no_wider_scope_exists():
    db = MagicMock()
    user = _build_user(roles=[_build_role("CUSTOM")])

    assert UserScopeService.get_user_data_scope(db, user) == "CUSTOM"


def test_data_scope_rule_get_scope_config_dict_parses_json_string():
    rule = DataScopeRule(
        rule_code="CUSTOM_RULE",
        rule_name="自定义规则",
        scope_type="CUSTOM",
        scope_config=json.dumps({"conditions": [{"type": "user_ids", "values": [1]}]}),
    )

    assert rule.get_scope_config_dict() == {"conditions": [{"type": "user_ids", "values": [1]}]}

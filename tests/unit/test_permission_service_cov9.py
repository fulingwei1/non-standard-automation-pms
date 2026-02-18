# -*- coding: utf-8 -*-
"""第九批: test_permission_service_cov9.py - PermissionService 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.permission_service")

from app.services.permission_service import PermissionService


@pytest.fixture
def mock_db():
    return MagicMock()


def make_role(id=1, code="ADMIN", name="管理员"):
    role = MagicMock()
    role.id = id
    role.code = code
    role.name = name
    return role


def make_user(id=1, username="test_user", is_superuser=False):
    user = MagicMock()
    user.id = id
    user.username = username
    user.is_superuser = is_superuser
    user.tenant_id = None
    return user


class TestGetUserEffectiveRoles:
    """测试获取用户有效角色"""

    def test_get_user_effective_roles_no_roles(self, mock_db):
        # UserRole query returns empty
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = PermissionService.get_user_effective_roles(mock_db, user_id=1)
        assert isinstance(result, list)


class TestGetUserPermissions:
    """测试获取用户权限"""

    def test_get_user_permissions_no_roles(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = PermissionService.get_user_permissions(mock_db, user_id=1)
        assert isinstance(result, (list, set))


class TestCheckPermission:
    """测试权限检查"""

    def test_check_permission_superuser(self, mock_db):
        user = make_user(is_superuser=True)
        result = PermissionService.check_permission(mock_db, user_id=1, permission_code="any_perm", user=user)
        assert result is True

    def test_check_permission_no_perm(self, mock_db):
        user = make_user(is_superuser=False)
        with patch.object(PermissionService, "get_user_permissions", return_value=set()):
            result = PermissionService.check_permission(mock_db, user_id=1, permission_code="admin_only", user=user)
            assert result is False

    def test_check_permission_has_perm(self, mock_db):
        user = make_user(is_superuser=False)
        with patch.object(PermissionService, "get_user_permissions", return_value={"view_reports"}):
            result = PermissionService.check_permission(mock_db, user_id=1, permission_code="view_reports", user=user)
            assert result is True


class TestCheckAnyPermission:
    """测试任一权限检查"""

    def test_check_any_permission_has_one(self, mock_db):
        user = make_user()
        with patch.object(PermissionService, "get_user_permissions", return_value={"view_ecn"}):
            result = PermissionService.check_any_permission(
                mock_db, user_id=1, permission_codes=["view_ecn", "admin_ecn"], user=user
            )
            assert result is True

    def test_check_any_permission_has_none(self, mock_db):
        user = make_user()
        with patch.object(PermissionService, "get_user_permissions", return_value=set()):
            result = PermissionService.check_any_permission(
                mock_db, user_id=1, permission_codes=["admin_only"], user=user
            )
            assert result is False


class TestGetUserMenus:
    """测试获取用户菜单"""

    def test_get_user_menus_empty(self, mock_db):
        # RoleMenu and MenuPermission queries return empty
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.all.return_value = []
        result = PermissionService.get_user_menus(mock_db, user_id=1)
        assert isinstance(result, list)


class TestGetUserDataScopes:
    """测试获取用户数据范围"""

    def test_get_user_data_scopes_no_roles(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = PermissionService.get_user_data_scopes(mock_db, user_id=1)
        assert isinstance(result, dict)

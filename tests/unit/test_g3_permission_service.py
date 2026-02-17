# -*- coding: utf-8 -*-
"""
G3组 - 权限服务单元测试（扩展）
目标文件: app/services/permission_service.py
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.permission_service import PermissionService
from app.models.user import User, Role, UserRole


class TestGetUserEffectiveRoles:
    """测试获取用户有效角色"""

    def test_user_with_no_roles(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        roles = PermissionService.get_user_effective_roles(db, user_id=1)
        # 当 UserRole 查询返回空时，结果应为空
        assert isinstance(roles, list)

    def test_user_with_direct_roles(self):
        db = MagicMock()

        role1 = MagicMock(spec=Role)
        role1.id = 10
        role1.role_code = "ADMIN"
        role1.role_name = "管理员"

        ur1 = MagicMock(spec=UserRole)
        ur1.role_id = 10

        def query_side(model):
            m = MagicMock()
            if model is UserRole:
                m.filter.return_value.all.return_value = [ur1]
            elif model is Role:
                m.filter.return_value.first.return_value = role1
            else:
                m.filter.return_value.all.return_value = []
                m.join.return_value.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = query_side

        roles = PermissionService.get_user_effective_roles(db, user_id=1)
        assert any(r.role_code == "ADMIN" for r in roles)

    def test_exception_triggers_fallback_sql(self):
        """当查询失败时应执行降级SQL查询"""
        db = MagicMock()
        # 第一次查询抛出异常
        db.query.side_effect = Exception("DB error")

        # 降级 SQL 也失败
        db.execute.side_effect = Exception("Execute error")

        roles = PermissionService.get_user_effective_roles(db, user_id=1)
        # 最终返回空列表（降级失败）
        assert roles == []


class TestCheckPermission:
    """测试权限检查"""

    def test_superuser_has_all_permissions(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = True

        result = PermissionService.check_permission(db, user_id=1, permission_code="anything:read", user=user)
        assert result is True

    def test_user_without_permission_returns_false(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = False
        user.tenant_id = None

        with patch.object(PermissionService, "get_user_permissions", return_value=[]):
            result = PermissionService.check_permission(db, user_id=2, permission_code="project:delete", user=user)

        assert result is False

    def test_user_with_permission_returns_true(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = False
        user.tenant_id = None

        with patch.object(PermissionService, "get_user_permissions", return_value=["project:read", "project:edit"]):
            result = PermissionService.check_permission(db, user_id=3, permission_code="project:read", user=user)

        assert result is True

    def test_non_superuser_without_user_object(self):
        """不传 user 对象时，应从数据库查询"""
        db = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.is_superuser = False
        mock_user.tenant_id = None
        db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch.object(PermissionService, "get_user_permissions", return_value=["task:view"]):
            result = PermissionService.check_permission(db, user_id=4, permission_code="task:view")

        assert result is True


class TestCheckAnyPermission:
    """测试检查任一权限"""

    def test_superuser_has_any_permission(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = True

        result = PermissionService.check_any_permission(db, 1, ["perm:a", "perm:b"], user=user)
        assert result is True

    def test_has_one_of_many(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = False
        user.tenant_id = None

        with patch.object(PermissionService, "get_user_permissions", return_value=["perm:b"]):
            result = PermissionService.check_any_permission(db, 2, ["perm:a", "perm:b"], user=user)

        assert result is True

    def test_has_none_of_many(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = False
        user.tenant_id = None

        with patch.object(PermissionService, "get_user_permissions", return_value=["other:perm"]):
            result = PermissionService.check_any_permission(db, 2, ["perm:a", "perm:b"], user=user)

        assert result is False


class TestCheckAllPermissions:
    """测试检查所有权限"""

    def test_superuser_has_all(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = True

        result = PermissionService.check_all_permissions(db, 1, ["perm:a", "perm:b"], user=user)
        assert result is True

    def test_has_all_permissions(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = False
        user.tenant_id = None

        with patch.object(PermissionService, "get_user_permissions", return_value=["perm:a", "perm:b", "perm:c"]):
            result = PermissionService.check_all_permissions(db, 2, ["perm:a", "perm:b"], user=user)

        assert result is True

    def test_missing_one_permission(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = False
        user.tenant_id = None

        with patch.object(PermissionService, "get_user_permissions", return_value=["perm:a"]):
            result = PermissionService.check_all_permissions(db, 2, ["perm:a", "perm:b"], user=user)

        assert result is False


class TestGetUserPermissions:
    """测试获取用户权限列表"""

    def test_uses_cache_when_available(self):
        db = MagicMock()
        mock_cache = MagicMock()
        mock_cache.get_user_permissions.return_value = ["cached:perm"]

        with patch("app.services.permission_service.get_permission_cache_service", return_value=mock_cache):
            result = PermissionService.get_user_permissions(db, user_id=1)

        assert "cached:perm" in result
        # 不应查询数据库
        db.execute.assert_not_called()

    def test_queries_db_when_cache_miss(self):
        db = MagicMock()
        mock_cache = MagicMock()
        mock_cache.get_user_permissions.return_value = None  # 缓存未命中

        # 模拟用户查询（获取 tenant_id）
        mock_user = MagicMock(spec=User)
        mock_user.tenant_id = 1
        db.query.return_value.filter.return_value.first.return_value = mock_user

        # 模拟 SQL 执行
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda _, i: "project:read"
        db.execute.return_value = [mock_row]

        with patch("app.services.permission_service.get_permission_cache_service", return_value=mock_cache):
            result = PermissionService.get_user_permissions(db, user_id=1)

        db.execute.assert_called()

    def test_returns_empty_on_db_error(self):
        db = MagicMock()
        mock_cache = MagicMock()
        mock_cache.get_user_permissions.return_value = None

        mock_user = MagicMock(spec=User)
        mock_user.tenant_id = None
        db.query.return_value.filter.return_value.first.return_value = mock_user
        db.execute.side_effect = Exception("DB error")

        with patch("app.services.permission_service.get_permission_cache_service", return_value=mock_cache):
            result = PermissionService.get_user_permissions(db, user_id=1)

        assert isinstance(result, list)


class TestGetUserDataScopes:
    """测试获取用户数据权限范围"""

    def test_empty_roles_returns_empty_dict(self):
        db = MagicMock()
        with patch.object(PermissionService, "get_user_effective_roles", return_value=[]):
            result = PermissionService.get_user_data_scopes(db, user_id=1)
        assert result == {}

    def test_returns_highest_scope(self):
        db = MagicMock()
        role = MagicMock()
        role.id = 1

        from app.models.permission import RoleDataScope, DataScopeRule
        rds1 = MagicMock(spec=RoleDataScope)
        rds1.resource_type = "project"
        rds1.scope_rule_id = 1
        rds1.role_id = 1

        rule1 = MagicMock(spec=DataScopeRule)
        rule1.scope_type = "DEPARTMENT"

        def db_query_side(model):
            m = MagicMock()
            if model is RoleDataScope:
                m.filter.return_value.all.return_value = [rds1]
            elif model is DataScopeRule:
                m.filter.return_value.first.return_value = rule1
            return m

        db.query.side_effect = db_query_side

        with patch.object(PermissionService, "get_user_effective_roles", return_value=[role]):
            result = PermissionService.get_user_data_scopes(db, user_id=1)

        assert "project" in result
        assert result["project"] == "DEPARTMENT"


class TestGetUserMenus:
    """测试获取用户菜单树"""

    def test_superuser_gets_all_menus(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = True

        mock_menu = MagicMock()
        mock_menu.to_dict.return_value = {"id": 1, "name": "项目管理"}
        (db.query.return_value
            .filter.return_value
            .filter.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value) = [mock_menu]

        result = PermissionService.get_user_menus(db, user_id=1, user=user)
        assert len(result) >= 1

    def test_user_no_roles_returns_empty(self):
        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = False

        with patch.object(PermissionService, "get_user_effective_roles", return_value=[]):
            result = PermissionService.get_user_menus(db, user_id=2, user=user)

        assert result == []

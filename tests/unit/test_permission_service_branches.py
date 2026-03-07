# -*- coding: utf-8 -*-
"""
权限服务模块分支测试 (Branch Coverage Tests)

目标: 将权限服务模块的分支覆盖率从0%提升到70%以上

测试范围:
- app/services/permission_service.py - 权限检查核心服务
- app/services/permission_cache_service.py - 权限缓存服务
- app/core/permissions/timesheet.py - 工时权限业务逻辑
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User, Role, UserRole, ApiPermission, RoleApiPermission
from app.models.permission import (
    MenuPermission,
    RoleMenu,
    DataScopeRule,
    RoleDataScope,
)
from app.models.organization import (
    Department,
    EmployeeOrgAssignment,
    Position,
    PositionRole,
)
from app.models.project import Project
from app.models.rd_project import RdProject
from app.models.timesheet import Timesheet
from app.services.permission_service import PermissionService
from app.services.permission_cache_service import (
    PermissionCacheService,
    get_permission_cache_service,
)
from app.core.permissions.timesheet import (
    is_timesheet_admin,
    get_user_manageable_dimensions,
    apply_timesheet_access_filter,
    check_timesheet_approval_permission,
    check_bulk_timesheet_approval_permission,
    has_timesheet_approval_access,
)


# ============================================================
# 1. PermissionService 分支测试
# ============================================================


class TestPermissionServiceBranches:
    """权限服务分支测试"""

    # 1.1 用户不存在分支
    def test_get_user_permissions_user_not_found(self, db_session: Session):
        """测试用户不存在时的权限获取"""
        # 用户ID不存在
        permissions = PermissionService.get_user_permissions(db_session, 99999)
        assert permissions == []

    # 1.2 角色不存在分支
    def test_get_user_effective_roles_no_roles(self, db_session: Session):
        """测试用户没有角色的情况"""
        user = User(
            username="norole_user",
            password_hash="test_hash",
            is_superuser=False,
        )
        db_session.add(user)
        db_session.flush()

        roles = PermissionService.get_user_effective_roles(db_session, user.id)
        assert roles == []

    # 1.3 角色未激活分支
    def test_get_user_effective_roles_inactive_role(self, db_session: Session):
        """测试用户角色未激活的情况"""
        user = User(username="test_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        # 创建未激活的角色
        role = Role(
            role_code="INACTIVE_ROLE",
            role_name="Inactive Role",
            is_active=False,  # 未激活
        )
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))
        db_session.flush()

        roles = PermissionService.get_user_effective_roles(db_session, user.id)
        assert len(roles) == 0  # 未激活角色不应返回

    # 1.4 多角色权限合并分支
    def test_get_user_permissions_multiple_roles(self, db_session: Session):
        """测试多角色权限合并逻辑"""
        user = User(username="multi_role_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        # 创建两个角色
        role1 = Role(role_code="ROLE1", role_name="Role 1", is_active=True)
        role2 = Role(role_code="ROLE2", role_name="Role 2", is_active=True)
        db_session.add_all([role1, role2])
        db_session.flush()

        # 分配角色
        db_session.add(UserRole(user_id=user.id, role_id=role1.id))
        db_session.add(UserRole(user_id=user.id, role_id=role2.id))
        db_session.flush()

        # 创建权限
        perm1 = ApiPermission(
            perm_code="test:perm1", perm_name="Permission 1", is_active=True
        )
        perm2 = ApiPermission(
            perm_code="test:perm2", perm_name="Permission 2", is_active=True
        )
        db_session.add_all([perm1, perm2])
        db_session.flush()

        # 角色权限关联
        db_session.add(RoleApiPermission(role_id=role1.id, permission_id=perm1.id))
        db_session.add(RoleApiPermission(role_id=role2.id, permission_id=perm2.id))
        db_session.flush()

        permissions = PermissionService.get_user_permissions(db_session, user.id)
        assert "test:perm1" in permissions
        assert "test:perm2" in permissions

    # 1.5 权限拒绝分支
    def test_check_permission_denied(self, db_session: Session):
        """测试权限拒绝情况"""
        user = User(
            username="no_perm_user",
            password_hash="test_hash",
            is_superuser=False,
        )
        db_session.add(user)
        db_session.flush()

        has_perm = PermissionService.check_permission(
            db_session, user.id, "nonexistent:permission", user
        )
        assert has_perm is False

    # 1.6 超级管理员分支
    def test_check_permission_superuser(self, db_session: Session):
        """测试超级管理员拥有所有权限"""
        user = User(
            username="superuser",
            password_hash="test_hash",
            is_superuser=True,
        )
        db_session.add(user)
        db_session.flush()

        # 超级管理员应该拥有任何权限
        has_perm = PermissionService.check_permission(
            db_session, user.id, "any:permission", user
        )
        assert has_perm is True

    # 1.7 通配符权限分支 (暂不测试,需要看代码是否支持)

    # 1.8 租户隔离分支
    def test_get_user_permissions_tenant_isolation(self, db_session: Session):
        """测试租户隔离权限查询"""
        user = User(
            username="tenant_user",
            password_hash="test_hash",
            tenant_id=1,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(role_code="TENANT_ROLE", role_name="Tenant Role", is_active=True)
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))

        # 租户专属权限
        perm_tenant = ApiPermission(
            perm_code="tenant:specific",
            perm_name="Tenant Specific",
            is_active=True,
            tenant_id=1,
        )
        # 系统级权限
        perm_system = ApiPermission(
            perm_code="system:global",
            perm_name="System Global",
            is_active=True,
            tenant_id=None,
        )
        db_session.add_all([perm_tenant, perm_system])
        db_session.flush()

        db_session.add(RoleApiPermission(role_id=role.id, permission_id=perm_tenant.id))
        db_session.add(RoleApiPermission(role_id=role.id, permission_id=perm_system.id))
        db_session.flush()

        # 获取租户1的权限
        permissions = PermissionService.get_user_permissions(
            db_session, user.id, tenant_id=1
        )
        assert "tenant:specific" in permissions
        assert "system:global" in permissions

    # 1.9 SQL异常降级处理分支
    def test_get_user_effective_roles_sql_error_fallback(self, db_session: Session):
        """测试SQL异常时的降级处理"""
        user = User(username="fallback_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(role_code="TEST_ROLE", role_name="Test Role", is_active=True)
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))
        db_session.flush()

        # Mock 抛出异常，触发降级逻辑
        with patch.object(
            db_session, "query", side_effect=[SQLAlchemyError("DB Error"), Mock()]
        ):
            # 第一个query抛异常,第二个query是降级查询(execute)
            with patch.object(
                db_session,
                "execute",
                return_value=MagicMock(
                    __iter__=lambda self: iter(
                        [
                            MagicMock(
                                id=role.id,
                                role_code=role.role_code,
                                role_name=role.role_name,
                            )
                        ]
                    )
                ),
            ):
                roles = PermissionService.get_user_effective_roles(
                    db_session, user.id
                )
                # 降级查询应该返回角色
                assert len(roles) > 0

    # 1.10 角色继承查询失败回退分支
    def test_get_user_permissions_inheritance_fallback(self, db_session: Session):
        """测试角色继承查询失败时回退到简单查询"""
        user = User(username="inherit_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(role_code="PARENT_ROLE", role_name="Parent Role", is_active=True)
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))

        perm = ApiPermission(
            perm_code="test:inherit", perm_name="Test Inherit", is_active=True
        )
        db_session.add(perm)
        db_session.flush()

        db_session.add(RoleApiPermission(role_id=role.id, permission_id=perm.id))
        db_session.flush()

        # Mock execute 第一次抛异常(继承查询),第二次成功(简单查询)
        original_execute = db_session.execute

        def side_effect_execute(sql, *args, **kwargs):
            sql_str = str(sql)
            if "RECURSIVE" in sql_str:
                raise SQLAlchemyError("Recursive query failed")
            else:
                return original_execute(sql, *args, **kwargs)

        with patch.object(db_session, "execute", side_effect=side_effect_execute):
            permissions = PermissionService.get_user_permissions(db_session, user.id)
            # 简单查询应该返回权限
            assert "test:inherit" in permissions

    # 1.11 check_any_permission 分支
    def test_check_any_permission_granted(self, db_session: Session):
        """测试check_any_permission有任一权限时返回True"""
        user = User(username="any_perm_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(role_code="ANY_ROLE", role_name="Any Role", is_active=True)
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))

        perm = ApiPermission(
            perm_code="test:any1", perm_name="Test Any 1", is_active=True
        )
        db_session.add(perm)
        db_session.flush()

        db_session.add(RoleApiPermission(role_id=role.id, permission_id=perm.id))
        db_session.flush()

        # 有一个权限就返回True
        has_any = PermissionService.check_any_permission(
            db_session,
            user.id,
            ["test:any1", "test:any2", "test:any3"],
            user,
        )
        assert has_any is True

    def test_check_any_permission_denied(self, db_session: Session):
        """测试check_any_permission全部没有权限时返回False"""
        user = User(
            username="no_any_perm_user",
            password_hash="test_hash",
            is_superuser=False,
        )
        db_session.add(user)
        db_session.flush()

        has_any = PermissionService.check_any_permission(
            db_session,
            user.id,
            ["test:none1", "test:none2"],
            user,
        )
        assert has_any is False

    # 1.12 check_all_permissions 分支
    def test_check_all_permissions_granted(self, db_session: Session):
        """测试check_all_permissions全部权限都有时返回True"""
        user = User(username="all_perm_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(role_code="ALL_ROLE", role_name="All Role", is_active=True)
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))

        perm1 = ApiPermission(
            perm_code="test:all1", perm_name="Test All 1", is_active=True
        )
        perm2 = ApiPermission(
            perm_code="test:all2", perm_name="Test All 2", is_active=True
        )
        db_session.add_all([perm1, perm2])
        db_session.flush()

        db_session.add(RoleApiPermission(role_id=role.id, permission_id=perm1.id))
        db_session.add(RoleApiPermission(role_id=role.id, permission_id=perm2.id))
        db_session.flush()

        has_all = PermissionService.check_all_permissions(
            db_session,
            user.id,
            ["test:all1", "test:all2"],
            user,
        )
        assert has_all is True

    def test_check_all_permissions_denied(self, db_session: Session):
        """测试check_all_permissions缺少某个权限时返回False"""
        user = User(username="partial_perm_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(role_code="PARTIAL_ROLE", role_name="Partial Role", is_active=True)
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))

        perm1 = ApiPermission(
            perm_code="test:partial1", perm_name="Test Partial 1", is_active=True
        )
        db_session.add(perm1)
        db_session.flush()

        db_session.add(RoleApiPermission(role_id=role.id, permission_id=perm1.id))
        db_session.flush()

        # 有partial1但没有partial2
        has_all = PermissionService.check_all_permissions(
            db_session,
            user.id,
            ["test:partial1", "test:partial2"],
            user,
        )
        assert has_all is False

    # 1.13 菜单权限分支
    def test_get_user_menus_superuser(self, db_session: Session):
        """测试超级管理员获取所有菜单"""
        user = User(
            username="menu_superuser",
            password_hash="test_hash",
            is_superuser=True,
        )
        db_session.add(user)
        db_session.flush()

        menu = MenuPermission(
            menu_code="TEST_MENU",
            menu_name="Test Menu",
            is_active=True,
            is_visible=True,
            parent_id=None,
            sort_order=1,
        )
        db_session.add(menu)
        db_session.flush()

        menus = PermissionService.get_user_menus(db_session, user.id, user)
        assert len(menus) > 0

    def test_get_user_menus_no_roles(self, db_session: Session):
        """测试无角色用户获取空菜单"""
        user = User(
            username="no_menu_user",
            password_hash="test_hash",
            is_superuser=False,
        )
        db_session.add(user)
        db_session.flush()

        menus = PermissionService.get_user_menus(db_session, user.id, user)
        assert menus == []

    def test_get_user_menus_with_roles(self, db_session: Session):
        """测试有角色用户获取对应菜单"""
        user = User(username="menu_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(role_code="MENU_ROLE", role_name="Menu Role", is_active=True)
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))

        menu = MenuPermission(
            menu_code="USER_MENU",
            menu_name="User Menu",
            is_active=True,
            is_visible=True,
            parent_id=None,
            sort_order=1,
        )
        db_session.add(menu)
        db_session.flush()

        db_session.add(RoleMenu(role_id=role.id, menu_id=menu.id, is_active=True))
        db_session.flush()

        menus = PermissionService.get_user_menus(db_session, user.id, user)
        assert len(menus) > 0
        assert menus[0]["code"] == "USER_MENU"

    # 1.14 数据权限范围分支
    def test_get_user_data_scopes_all(self, db_session: Session):
        """测试全部数据权限"""
        user = User(username="data_scope_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(role_code="DATA_ROLE", role_name="Data Role", is_active=True)
        db_session.add(role)
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role.id))

        scope_rule = DataScopeRule(
            rule_name="All Data",
            scope_type="ALL",
            description="All data scope",
        )
        db_session.add(scope_rule)
        db_session.flush()

        db_session.add(
            RoleDataScope(
                role_id=role.id,
                resource_type="project",
                scope_rule_id=scope_rule.id,
                is_active=True,
            )
        )
        db_session.flush()

        scopes = PermissionService.get_user_data_scopes(db_session, user.id)
        assert scopes.get("project") == "ALL"

    def test_get_user_data_scopes_priority(self, db_session: Session):
        """测试数据权限优先级(取最大范围)"""
        user = User(username="scope_priority_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role1 = Role(role_code="SCOPE_ROLE1", role_name="Scope Role 1", is_active=True)
        role2 = Role(role_code="SCOPE_ROLE2", role_name="Scope Role 2", is_active=True)
        db_session.add_all([role1, role2])
        db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id=role1.id))
        db_session.add(UserRole(user_id=user.id, role_id=role2.id))

        # 创建两个范围规则: OWN < DEPARTMENT
        scope_own = DataScopeRule(rule_name="Own", scope_type="OWN")
        scope_dept = DataScopeRule(rule_name="Department", scope_type="DEPARTMENT")
        db_session.add_all([scope_own, scope_dept])
        db_session.flush()

        db_session.add(
            RoleDataScope(
                role_id=role1.id,
                resource_type="timesheet",
                scope_rule_id=scope_own.id,
                is_active=True,
            )
        )
        db_session.add(
            RoleDataScope(
                role_id=role2.id,
                resource_type="timesheet",
                scope_rule_id=scope_dept.id,
                is_active=True,
            )
        )
        db_session.flush()

        scopes = PermissionService.get_user_data_scopes(db_session, user.id)
        # 应该取更大的范围DEPARTMENT
        assert scopes.get("timesheet") == "DEPARTMENT"

    # 1.15 岗位默认角色分支
    def test_get_user_effective_roles_with_position_roles(self, db_session: Session):
        """测试获取岗位默认角色"""
        user = User(username="position_user", password_hash="test_hash", employee_id=1)
        db_session.add(user)
        db_session.flush()

        # 创建岗位和角色
        position = Position(
            position_code="POS001",
            position_name="Test Position",
            is_active=True,
        )
        db_session.add(position)
        db_session.flush()

        role = Role(
            role_code="POSITION_ROLE", role_name="Position Role", is_active=True
        )
        db_session.add(role)
        db_session.flush()

        # 岗位角色关联
        db_session.add(
            PositionRole(
                position_id=position.id,
                role_id=role.id,
                is_active=True,
            )
        )

        # 员工岗位分配
        db_session.add(
            EmployeeOrgAssignment(
                employee_id=user.employee_id,
                position_id=position.id,
                is_active=True,
            )
        )
        db_session.flush()

        roles = PermissionService.get_user_effective_roles(db_session, user.id)
        role_codes = [r.role_code for r in roles]
        assert "POSITION_ROLE" in role_codes


# ============================================================
# 2. PermissionCacheService 分支测试
# ============================================================


class TestPermissionCacheServiceBranches:
    """权限缓存服务分支测试"""

    # 2.1 缓存命中分支
    def test_cache_hit(self, db_session: Session):
        """测试缓存命中"""
        cache_service = get_permission_cache_service()
        user_id = 1
        tenant_id = 1
        permissions = {"test:read", "test:write"}

        # 设置缓存
        cache_service.set_user_permissions(user_id, permissions, tenant_id)

        # 获取缓存(应该命中)
        cached = cache_service.get_user_permissions(user_id, tenant_id)
        assert cached == permissions

    # 2.2 缓存未命中分支
    def test_cache_miss(self, db_session: Session):
        """测试缓存未命中"""
        cache_service = get_permission_cache_service()
        user_id = 9999
        tenant_id = 1

        cached = cache_service.get_user_permissions(user_id, tenant_id)
        assert cached is None

    # 2.3 缓存失效分支
    def test_cache_invalidate_user_permissions(self, db_session: Session):
        """测试用户权限缓存失效"""
        cache_service = get_permission_cache_service()
        user_id = 1
        tenant_id = 1
        permissions = {"test:read"}

        cache_service.set_user_permissions(user_id, permissions, tenant_id)

        # 失效缓存
        result = cache_service.invalidate_user_permissions(user_id, tenant_id)
        assert result is True

        # 再次获取应该为空
        cached = cache_service.get_user_permissions(user_id, tenant_id)
        assert cached is None

    # 2.4 批量失效分支
    def test_invalidate_tenant_all_users(self, db_session: Session):
        """测试失效租户所有用户权限缓存"""
        cache_service = get_permission_cache_service()
        tenant_id = 1

        # 设置多个用户的缓存
        cache_service.set_user_permissions(1, {"perm1"}, tenant_id)
        cache_service.set_user_permissions(2, {"perm2"}, tenant_id)

        # 失效租户所有用户
        count = cache_service.invalidate_tenant_user_permissions(tenant_id)
        assert count >= 0

    # 2.5 角色权限缓存分支
    def test_role_permissions_cache(self, db_session: Session):
        """测试角色权限缓存"""
        cache_service = get_permission_cache_service()
        role_id = 1
        tenant_id = 1
        role_data = {"permissions": ["test:read"], "menus": ["menu1"]}

        cache_service.set_role_permissions(role_id, role_data, tenant_id)

        cached = cache_service.get_role_permissions(role_id, tenant_id)
        assert cached == role_data

    # 2.6 角色-用户关联缓存分支
    def test_role_user_ids_cache(self, db_session: Session):
        """测试角色-用户关联缓存"""
        cache_service = get_permission_cache_service()
        role_id = 1
        tenant_id = 1
        user_ids = [1, 2, 3]

        cache_service.set_role_user_ids(role_id, user_ids, tenant_id)

        cached = cache_service.get_role_user_ids(role_id, tenant_id)
        assert cached == user_ids

    # 2.7 用户-角色关联缓存分支
    def test_user_role_ids_cache(self, db_session: Session):
        """测试用户-角色关联缓存"""
        cache_service = get_permission_cache_service()
        user_id = 1
        tenant_id = 1
        role_ids = [1, 2]

        cache_service.set_user_role_ids(user_id, role_ids, tenant_id)

        cached = cache_service.get_user_role_ids(user_id, tenant_id)
        assert cached == role_ids

    # 2.8 角色变更时批量失效分支
    def test_invalidate_role_and_users(self, db_session: Session):
        """测试角色变更时失效角色和相关用户缓存"""
        cache_service = get_permission_cache_service()
        role_id = 1
        tenant_id = 1
        user_ids = [1, 2, 3]

        # 设置缓存
        cache_service.set_role_permissions(role_id, {"perms": []}, tenant_id)
        for uid in user_ids:
            cache_service.set_user_permissions(uid, {"test"}, tenant_id)

        # 批量失效
        count = cache_service.invalidate_role_and_users(role_id, user_ids, tenant_id)
        assert count > 0

    # 2.9 用户角色变更缓存更新分支
    def test_invalidate_user_role_change(self, db_session: Session):
        """测试用户角色变更时更新缓存"""
        cache_service = get_permission_cache_service()
        user_id = 1
        tenant_id = 1
        old_roles = [1, 2]
        new_roles = [2, 3]

        count = cache_service.invalidate_user_role_change(
            user_id, old_roles, new_roles, tenant_id
        )
        assert count > 0

    # 2.10 租户全部缓存失效分支
    def test_invalidate_tenant_all(self, db_session: Session):
        """测试失效租户所有权限缓存"""
        cache_service = get_permission_cache_service()
        tenant_id = 1

        # 设置各种缓存
        cache_service.set_user_permissions(1, {"perm"}, tenant_id)
        cache_service.set_role_permissions(1, {}, tenant_id)

        count = cache_service.invalidate_tenant(tenant_id)
        assert count >= 0

    # 2.11 系统级缓存(tenant_id=None)分支
    def test_cache_system_level(self, db_session: Session):
        """测试系统级缓存(tenant_id=None)"""
        cache_service = get_permission_cache_service()
        user_id = 1
        permissions = {"system:admin"}

        cache_service.set_user_permissions(user_id, permissions, tenant_id=None)

        cached = cache_service.get_user_permissions(user_id, tenant_id=None)
        assert cached == permissions

    # 2.12 缓存统计信息分支
    def test_get_stats(self, db_session: Session):
        """测试获取缓存统计信息"""
        cache_service = get_permission_cache_service()
        stats = cache_service.get_stats()

        assert "cache_type" in stats
        assert stats["cache_type"] == "permission"
        assert "tenant_isolation" in stats
        assert stats["tenant_isolation"] is True

    # 2.13 Redis不可用降级分支
    @patch("app.services.cache_service.CacheService.get")
    def test_cache_redis_unavailable_fallback(
        self, mock_get, db_session: Session
    ):
        """测试Redis不可用时降级处理"""
        mock_get.return_value = None  # 模拟Redis返回空

        cache_service = get_permission_cache_service()
        cached = cache_service.get_user_permissions(1, 1)
        assert cached is None


# ============================================================
# 3. Timesheet Permission 分支测试
# ============================================================


class TestTimesheetPermissionBranches:
    """工时权限业务逻辑分支测试"""

    # 3.1 工时管理员检查分支
    def test_is_timesheet_admin_superuser(self, db_session: Session):
        """测试超级管理员是工时管理员"""
        user = User(
            username="super_admin",
            password_hash="test_hash",
            is_superuser=True,
        )
        db_session.add(user)
        db_session.flush()

        assert is_timesheet_admin(user) is True

    def test_is_timesheet_admin_by_role_code(self, db_session: Session):
        """测试通过角色代码判断工时管理员"""
        user = User(username="admin_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(
            role_code="timesheet_admin",
            role_name="Timesheet Admin",
            is_active=True,
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)
        db_session.flush()

        # 模拟关系加载
        user.roles = [user_role]
        user_role.role = role

        assert is_timesheet_admin(user) is True

    def test_is_timesheet_admin_by_role_name(self, db_session: Session):
        """测试通过角色名称判断工时管理员"""
        user = User(username="hr_admin", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        role = Role(
            role_code="OTHER_CODE",
            role_name="人事管理员",
            is_active=True,
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)
        db_session.flush()

        user.roles = [user_role]
        user_role.role = role

        assert is_timesheet_admin(user) is True

    def test_is_timesheet_admin_false(self, db_session: Session):
        """测试普通用户不是工时管理员"""
        user = User(
            username="normal_user",
            password_hash="test_hash",
            is_superuser=False,
        )
        db_session.add(user)
        db_session.flush()

        user.roles = []

        assert is_timesheet_admin(user) is False

    # 3.2 可管理维度分支
    def test_get_user_manageable_dimensions_admin(self, db_session: Session):
        """测试管理员可管理所有维度"""
        user = User(
            username="admin",
            password_hash="test_hash",
            is_superuser=True,
        )
        db_session.add(user)
        db_session.flush()

        dims = get_user_manageable_dimensions(db_session, user)
        assert dims["is_admin"] is True

    def test_get_user_manageable_dimensions_project_manager(
        self, db_session: Session
    ):
        """测试项目经理可管理项目维度"""
        user = User(username="pm_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        project = Project(
            code="PJ001",
            name="Test Project",
            pm_id=user.id,
        )
        db_session.add(project)
        db_session.flush()

        dims = get_user_manageable_dimensions(db_session, user)
        assert project.id in dims["project_ids"]

    def test_get_user_manageable_dimensions_rd_manager(self, db_session: Session):
        """测试研发项目经理可管理研发项目维度"""
        user = User(username="rd_pm", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        rd_project = RdProject(
            project_code="RD001",
            project_name="R&D Project",
            project_manager_id=user.id,
        )
        db_session.add(rd_project)
        db_session.flush()

        dims = get_user_manageable_dimensions(db_session, user)
        assert rd_project.id in dims["rd_project_ids"]

    def test_get_user_manageable_dimensions_department_manager(
        self, db_session: Session
    ):
        """测试部门经理可管理部门维度"""
        user = User(username="dept_mgr", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        dept = Department(
            dept_code="DEPT001",
            dept_name="Test Department",
            manager_id=user.id,
        )
        db_session.add(dept)
        db_session.flush()

        dims = get_user_manageable_dimensions(db_session, user)
        assert dept.id in dims["department_ids"]

    def test_get_user_manageable_dimensions_subordinates(self, db_session: Session):
        """测试获取直接下属维度"""
        manager = User(username="manager", password_hash="test_hash")
        db_session.add(manager)
        db_session.flush()

        subordinate = User(
            username="subordinate",
            password_hash="test_hash",
            reporting_to=manager.id,
        )
        db_session.add(subordinate)
        db_session.flush()

        dims = get_user_manageable_dimensions(db_session, manager)
        assert subordinate.id in dims["subordinate_user_ids"]

    # 3.3 工时访问过滤分支
    def test_apply_timesheet_access_filter_admin(self, db_session: Session):
        """测试管理员访问所有工时"""
        user = User(
            username="admin",
            password_hash="test_hash",
            is_superuser=True,
        )
        db_session.add(user)
        db_session.flush()

        query = db_session.query(Timesheet)
        filtered_query = apply_timesheet_access_filter(query, db_session, user)

        # 管理员不应该被过滤
        assert filtered_query == query

    def test_apply_timesheet_access_filter_own(self, db_session: Session):
        """测试普通用户只能访问自己的工时"""
        user = User(username="normal", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        user.roles = []

        timesheet = Timesheet(
            user_id=user.id,
            hours=8.0,
            work_date="2024-01-01",
        )
        db_session.add(timesheet)
        db_session.flush()

        query = db_session.query(Timesheet)
        filtered_query = apply_timesheet_access_filter(query, db_session, user)

        results = filtered_query.all()
        assert all(ts.user_id == user.id for ts in results)

    # 3.4 工时审批权限分支
    def test_check_timesheet_approval_permission_admin(self, db_session: Session):
        """测试管理员可审批所有工时"""
        admin = User(
            username="admin",
            password_hash="test_hash",
            is_superuser=True,
        )
        other_user = User(username="other", password_hash="test_hash")
        db_session.add_all([admin, other_user])
        db_session.flush()

        timesheet = Timesheet(
            user_id=other_user.id,
            hours=8.0,
            work_date="2024-01-01",
        )
        db_session.add(timesheet)
        db_session.flush()

        can_approve = check_timesheet_approval_permission(db_session, timesheet, admin)
        assert can_approve is True

    def test_check_timesheet_approval_permission_self_deny(self, db_session: Session):
        """测试不能审批自己的工时"""
        user = User(username="self_user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        user.roles = []

        timesheet = Timesheet(
            user_id=user.id,
            hours=8.0,
            work_date="2024-01-01",
        )
        db_session.add(timesheet)
        db_session.flush()

        can_approve = check_timesheet_approval_permission(db_session, timesheet, user)
        assert can_approve is False

    def test_check_timesheet_approval_permission_project_manager(
        self, db_session: Session
    ):
        """测试项目经理可审批项目工时"""
        pm = User(username="pm", password_hash="test_hash")
        member = User(username="member", password_hash="test_hash")
        db_session.add_all([pm, member])
        db_session.flush()

        project = Project(
            code="PJ001",
            name="Test Project",
            pm_id=pm.id,
        )
        db_session.add(project)
        db_session.flush()

        timesheet = Timesheet(
            user_id=member.id,
            project_id=project.id,
            hours=8.0,
            work_date="2024-01-01",
        )
        db_session.add(timesheet)
        db_session.flush()

        can_approve = check_timesheet_approval_permission(db_session, timesheet, pm)
        assert can_approve is True

    def test_check_timesheet_approval_permission_rd_manager(self, db_session: Session):
        """测试研发项目经理可审批研发工时"""
        rd_pm = User(username="rd_pm", password_hash="test_hash")
        member = User(username="member", password_hash="test_hash")
        db_session.add_all([rd_pm, member])
        db_session.flush()

        rd_project = RdProject(
            project_code="RD001",
            project_name="R&D Project",
            project_manager_id=rd_pm.id,
        )
        db_session.add(rd_project)
        db_session.flush()

        timesheet = Timesheet(
            user_id=member.id,
            rd_project_id=rd_project.id,
            hours=8.0,
            work_date="2024-01-01",
        )
        db_session.add(timesheet)
        db_session.flush()

        can_approve = check_timesheet_approval_permission(db_session, timesheet, rd_pm)
        assert can_approve is True

    def test_check_timesheet_approval_permission_department_manager(
        self, db_session: Session
    ):
        """测试部门经理可审批部门工时"""
        dept_mgr = User(username="dept_mgr", password_hash="test_hash")
        member = User(username="member", password_hash="test_hash")
        db_session.add_all([dept_mgr, member])
        db_session.flush()

        dept = Department(
            dept_code="DEPT001",
            dept_name="Test Department",
            manager_id=dept_mgr.id,
        )
        db_session.add(dept)
        db_session.flush()

        timesheet = Timesheet(
            user_id=member.id,
            department_id=dept.id,
            hours=8.0,
            work_date="2024-01-01",
        )
        db_session.add(timesheet)
        db_session.flush()

        can_approve = check_timesheet_approval_permission(
            db_session, timesheet, dept_mgr
        )
        assert can_approve is True

    def test_check_timesheet_approval_permission_direct_manager(
        self, db_session: Session
    ):
        """测试直接上级可审批下属工时"""
        manager = User(username="manager", password_hash="test_hash")
        subordinate = User(
            username="subordinate",
            password_hash="test_hash",
            reporting_to=manager.id,
        )
        db_session.add_all([manager, subordinate])
        db_session.flush()

        timesheet = Timesheet(
            user_id=subordinate.id,
            hours=8.0,
            work_date="2024-01-01",
        )
        db_session.add(timesheet)
        db_session.flush()

        can_approve = check_timesheet_approval_permission(
            db_session, timesheet, manager
        )
        assert can_approve is True

    def test_check_timesheet_approval_permission_denied(self, db_session: Session):
        """测试无权限审批工时"""
        user1 = User(username="user1", password_hash="test_hash")
        user2 = User(username="user2", password_hash="test_hash")
        db_session.add_all([user1, user2])
        db_session.flush()

        user1.roles = []

        timesheet = Timesheet(
            user_id=user2.id,
            hours=8.0,
            work_date="2024-01-01",
        )
        db_session.add(timesheet)
        db_session.flush()

        can_approve = check_timesheet_approval_permission(db_session, timesheet, user1)
        assert can_approve is False

    # 3.5 批量审批权限分支
    def test_check_bulk_timesheet_approval_permission_all_granted(
        self, db_session: Session
    ):
        """测试批量审批全部有权限"""
        admin = User(
            username="admin",
            password_hash="test_hash",
            is_superuser=True,
        )
        user = User(username="user", password_hash="test_hash")
        db_session.add_all([admin, user])
        db_session.flush()

        timesheets = [
            Timesheet(user_id=user.id, hours=8.0, work_date="2024-01-01"),
            Timesheet(user_id=user.id, hours=8.0, work_date="2024-01-02"),
        ]
        db_session.add_all(timesheets)
        db_session.flush()

        can_approve = check_bulk_timesheet_approval_permission(
            db_session, timesheets, admin
        )
        assert can_approve is True

    def test_check_bulk_timesheet_approval_permission_partial_denied(
        self, db_session: Session
    ):
        """测试批量审批部分无权限则失败"""
        pm = User(username="pm", password_hash="test_hash")
        user1 = User(username="user1", password_hash="test_hash")
        user2 = User(username="user2", password_hash="test_hash")
        db_session.add_all([pm, user1, user2])
        db_session.flush()

        project = Project(code="PJ001", name="Test Project", pm_id=pm.id)
        db_session.add(project)
        db_session.flush()

        timesheets = [
            Timesheet(
                user_id=user1.id, project_id=project.id, hours=8.0, work_date="2024-01-01"
            ),
            Timesheet(
                user_id=user2.id, hours=8.0, work_date="2024-01-02"
            ),  # 无项目关联
        ]
        db_session.add_all(timesheets)
        db_session.flush()

        can_approve = check_bulk_timesheet_approval_permission(
            db_session, timesheets, pm
        )
        # 第二条没有权限,应该返回False
        assert can_approve is False

    def test_check_bulk_timesheet_approval_permission_empty(self, db_session: Session):
        """测试批量审批空列表"""
        user = User(username="user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        can_approve = check_bulk_timesheet_approval_permission(db_session, [], user)
        assert can_approve is False

    # 3.6 工时审批访问权限分支
    def test_has_timesheet_approval_access_admin(self, db_session: Session):
        """测试管理员有审批访问权限"""
        admin = User(
            username="admin",
            password_hash="test_hash",
            is_superuser=True,
        )
        db_session.add(admin)
        db_session.flush()

        has_access = has_timesheet_approval_access(admin, db_session)
        assert has_access is True

    def test_has_timesheet_approval_access_target_subordinate(
        self, db_session: Session
    ):
        """测试对下属有审批访问权限"""
        manager = User(username="manager", password_hash="test_hash")
        subordinate = User(
            username="subordinate",
            password_hash="test_hash",
            reporting_to=manager.id,
        )
        db_session.add_all([manager, subordinate])
        db_session.flush()

        has_access = has_timesheet_approval_access(
            manager, db_session, target_user_id=subordinate.id
        )
        assert has_access is True

    def test_has_timesheet_approval_access_self_deny(self, db_session: Session):
        """测试对自己无审批访问权限"""
        user = User(username="user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        user.roles = []

        has_access = has_timesheet_approval_access(
            user, db_session, target_user_id=user.id
        )
        assert has_access is False

    def test_has_timesheet_approval_access_target_department(
        self, db_session: Session
    ):
        """测试对部门有审批访问权限"""
        dept_mgr = User(username="dept_mgr", password_hash="test_hash")
        db_session.add(dept_mgr)
        db_session.flush()

        dept = Department(
            dept_code="DEPT001",
            dept_name="Test Department",
            manager_id=dept_mgr.id,
        )
        db_session.add(dept)
        db_session.flush()

        has_access = has_timesheet_approval_access(
            dept_mgr, db_session, target_department_id=dept.id
        )
        assert has_access is True

    def test_has_timesheet_approval_access_any_manager(self, db_session: Session):
        """测试任何一种经理都有审批访问权限"""
        pm = User(username="pm", password_hash="test_hash")
        db_session.add(pm)
        db_session.flush()

        project = Project(code="PJ001", name="Test Project", pm_id=pm.id)
        db_session.add(project)
        db_session.flush()

        # 不指定目标用户或部门,只要是任何一种经理就有权限
        has_access = has_timesheet_approval_access(pm, db_session)
        assert has_access is True

    def test_has_timesheet_approval_access_no_permission(self, db_session: Session):
        """测试无任何审批访问权限"""
        user = User(username="user", password_hash="test_hash")
        db_session.add(user)
        db_session.flush()

        user.roles = []

        has_access = has_timesheet_approval_access(user, db_session)
        assert has_access is False

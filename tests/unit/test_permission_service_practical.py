# -*- coding: utf-8 -*-
"""
实用测试：PermissionService权限服务。
这些测试基于实际接口创建，确保可以运行。
"""

import pytest
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.base import get_session
from app.models.organization import Employee
from app.models.user import User, Permission, Role, RolePermission
from app.models.permission import DataScopeRule
from app.services.permission_service import PermissionService


@pytest.fixture(scope="function")
def test_employee(db_session: Session):
    """创建测试员工用户。"""
    employee = Employee(
        name="Test Engineer",
        employee_code="E001",
        department="研发部",
        employment_status="active",
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture(scope="function")
def test_user_with_role(db_session: Session, test_employee):
    """创建带角色的测试用户。"""
    # 创建角色
    role = Role(
        role_name="Test Role",
        role_code="TEST_ROLE",
        is_active=True,
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    # 创建权限
    perm1 = Permission(
        permission_name="test:project:read",
        permission_code="project:read",
        module="PROJECT",
        action="read",
    )
    db_session.add(perm1)
    db_session.commit()
    db_session.refresh(perm1)

    # 创建角色权限关联
    role_perm1 = RolePermission(
        role_id=role.id,
        permission_id=perm1.id,
    )
    db_session.add(role_perm1)
    db_session.commit()

    user = User(
        username="testuser",
        password_hash=get_password_hash("testpass"),
        employee_id=test_employee.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Note: Many-to-many relationship might need UserRole table
    from app.models.user import UserRole

    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    db_session.commit()

    return user


class TestPermissionService:
    """PermissionService权限服务测试。"""

    def test_check_permission_superuser_has_all(
        self, db_session: Session, test_user_with_role
    ):
        """测试超级用户拥有所有权限。"""
        # 将用户设为超级用户
        db_session.query(User).filter(User.id == test_user_with_role.id).update(
            {"is_superuser": True}
        )
        db_session.commit()

        result = PermissionService.check_permission(
            db_session, test_user_with_role.id, "project:read", "PROJECT"
        )
        assert result is True

    def test_check_permission_user_has_permission(
        self, db_session: Session, test_user_with_role
    ):
        """测试用户有特定权限。"""
        result = PermissionService.check_permission(
            db_session, test_user_with_role.id, "project:read", "PROJECT"
        )
        assert result is True

        # 测试无权限
        result = PermissionService.check_permission(
            db_session, test_user_with_role.id, "project:delete", "PROJECT"
        )
        assert result is False

    def test_check_permission_user_no_user(self, db_session: Session):
        """测试不存在的用户没有权限。"""
        result = PermissionService.check_permission(
            db_session, 9999, "project:read", "PROJECT"
        )
        assert result is False

    def test_get_user_permissions_basic(self, db_session: Session, test_user_with_role):
        """测试获取用户基本权限。"""

        # 创建数据范围规则
        scope_rule = DataScopeRule(
            rule_name="Test Scope Rule",
            rule_code="ALL_PROJECTS",
            scope_type="PROJECT",
            description="测试：所有项目访问权限",
            is_active=True,
        )
        db_session.add(scope_rule)
        db_session.commit()
        db_session.refresh(scope_rule)

        # 创建权限
        perm = Permission(
            permission_name="test:project:write",
            permission_code="project:write",
            module="PROJECT",
            action="write",
        )
        db_session.add(perm)
        db_session.commit()
        db_session.refresh(perm)

        # Associate with role
        test_role = db_session.query(Role).first()  # Should be the one from fixture
        role_perm = RolePermission(role_id=test_role.id, permission_id=perm.id)
        db_session.add(role_perm)
        db_session.commit()

        result = PermissionService.get_user_permissions(
            db_session, test_user_with_role.id
        )
        assert "project:write" in result

    def test_get_user_effective_roles_with_roles(
        self, db_session: Session, test_user_with_role
    ):
        """测试用户的有效角色。"""
        result = PermissionService.get_user_effective_roles(
            db_session, test_user_with_role.id
        )
        assert len(result) > 0

    def test_check_any_permission_specific_permission(
        self, db_session: Session, test_user_with_role
    ):
        """测试普通用户有特定权限返回True。"""
        result = PermissionService.check_any_permission(
            db_session, test_user_with_role.id, ["project:read"], "PROJECT"
        )
        assert result is True

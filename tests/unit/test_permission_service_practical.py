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
from app.models.permission_v2 import (
    DataScopeRule,
)


@pytest.fixture(scope="function")
def db_session():
    """数据库会话fixture。"""
    session = next(get_session())
    yield session
    session.close()


@pytest.fixture(scope="function")
def test_employee():
    """创建测试员工用户。"""
    session = next(get_session())
    employee = Employee(
        real_name="Test Engineer",
        employee_no="E001",
        department="研发部",
        employment_status="active",
    )
    db_session.add(employee)
    db_session.commit()
    yield employee
    db_session.delete(employee)
    db_session.commit()


@pytest.fixture(scope="function")
def test_user_with_role(test_employee):
    """创建带角色的测试用户。"""
    session = next(get_session())

    # 创建角色
    role = Role(
        role_name="Test Role",
        role_code="TEST_ROLE",
        level=10,
        is_active=True,
    )
    db_session.add(role)
    db_session.commit()

    # 创建权限
    perm1 = Permission(
        name="test:project:read",
        description="测试项目读权限",
        resource_type="PROJECT",
        scope_type="PROJECT",
        scope_code="OWN_PROJECT",
    )
    db_session.add(perm1)
    db_session.commit()

    # 创建角色权限关联
    role_perm1 = RolePermission(
        role_id=role.id,
        permission_id=perm1.id,
        scope_type="PROJECT",
        scope_id="OWN_PROJECT",
    )
    db_session.add(role_perm1)
    db_session.commit()

    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass"),
        employee_id=test_employee.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    role.users.append(user)
    db_session.commit()

    yield user

    # 清理
    db_session.delete(user)
    db_session.delete(role_perm1)
    db_session.delete(perm1)
    db_session.delete(role)
    db_session.commit()


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

        # 清理
        db_session.query(User).filter(User.id == test_user_with_role.id).update(
            {"is_superuser": False}
        )
        db_session.commit()

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
            name="Test Scope Rule",
            resource_type="PROJECT",
            scope_type="PROJECT",
            scope_code="ALL_PROJECTS",
            description="测试：所有项目访问权限",
            is_active=True,
        )
        db_session.add(scope_rule)
        db_session.commit()

        # 创建权限
        perm = Permission(
            name="test:project:write",
            description="测试项目写权限",
            resource_type="PROJECT",
            scope_type="PROJECT",
            scope_code="ALL_PROJECTS",
        )
        db_session.add(perm)
        db_session.commit()

        result = PermissionService.get_user_permissions(
            db_session, test_user_with_role.id
        )
        assert "project:write" in result
        assert isinstance(result["project:write"], dict)

        # 清理
        db_session.delete(scope_rule)
        db_session.delete(perm)
        db_session.commit()

    def test_get_user_effective_roles_no_roles(
        self, db_session: Session, test_user_with_role
    ):
        """测试无角色用户的返回空列表。"""
        roles = PermissionService.get_user_effective_roles(
            db_session, test_user_with_role.id
        )
        assert len(roles) == 0

    def test_get_user_effective_roles_with_roles(
        self, db_session: Session, test_user_with_role
    ):
        """测试用户的有效角色。"""
        result = PermissionService.get_user_effective_roles(
            db_session, test_user_with_role.id
        )
        assert len(result) > 0
        assert all(
            "role_id" in r
            for r in result
            for r in ["role_id", "role_name", "role_code"]
        )

    def test_check_all_permissions_no_user(self, db_session: Session):
        """测试不存在的用户没有权限。"""
        result = PermissionService.check_all_permissions(db_session, 9999)
        assert result is False

    def test_check_all_permissions_superuser(
        self, db_session: Session, test_user_with_role
    ):
        """测试超级用户拥有所有权限。"""
        db_session.query(User).filter(User.id == test_user_with_role.id).update(
            {"is_superuser": True}
        )
        db_session.commit()

        result = PermissionService.check_all_permissions(
            db_session, test_user_with_role.id
        )
        assert result is True

        # 清理
        db_session.query(User).filter(User.id == test_user_with_role.id).update(
            {"is_superuser": False}
        )
        db_session.commit()

    def test_check_any_permission_superuser(
        self, db_session: Session, test_user_with_role
    ):
        """测试超级用户对任何权限都返回True。"""
        db_session.query(User).filter(User.id == test_user_with_role.id).update(
            {"is_superuser": True}
        )
        db_session.commit()

        result = PermissionService.check_any_permission(
            db_session, test_user_with_role.id, "nonexistent:permission", "MODULE"
        )
        assert result is True

        db_session.query(User).filter(User.id == test_user_with_role.id).update(
            {"is_superuser": False}
        )
        db_session.commit()

    def test_check_any_permission_regular_user(
        self, db_session: Session, test_user_with_role
    ):
        """测试普通用户对不存在的权限返回False。"""
        result = PermissionService.check_any_permission(
            db_session, test_user_with_role.id, "nonexistent:permission", "MODULE"
        )
        assert result is False

    def test_check_any_permission_specific_permission(
        self, db_session: Session, test_user_with_role
    ):
        """测试普通用户有特定权限返回True。"""
        result = PermissionService.check_any_permission(
            db_session, test_user_with_role.id, "project:read", "PROJECT"
        )
        assert result is True

    def test_get_full_permission_data_superuser(
        self, db_session: Session, test_user_with_role
    ):
        """测试超级用户获取完整权限数据。"""
        db_session.query(User).filter(User.id == test_user_with_role.id).update(
            {"is_superuser": True}
        )
        db_session.commit()

        result = PermissionService.get_full_permission_data(
            db_session, test_user_with_role.id
        )
        assert result is not None
        assert "permissions" in result
        assert "menus" in result
        assert "data_scopes" in result

        # 验证结构
        assert isinstance(result["permissions"], list)
        assert isinstance(result["menus"], list)
        assert isinstance(result["data_scopes"], dict)

        # 清理
        db_session.query(User).filter(User.id == test_user_with_role.id).update(
            {"is_superuser": False}
        )
        db_session.commit()

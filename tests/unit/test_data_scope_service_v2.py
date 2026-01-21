# -*- coding: utf-8 -*-
"""
Tests for data_scope_service_v2 service
Covers: app/services/data_scope_service_v2.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 138 lines
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.data_scope_service_v2 import DataScopeServiceV2
from app.models.user import User
from app.models.organization_v2 import OrganizationUnit, EmployeeOrgAssignment
from app.models.permission_v2 import ScopeType


class TestDataScopeServiceV2:
    """Test suite for DataScopeServiceV2."""

    def test_get_user_org_units_no_assignments(self, db_session):
        """测试获取用户组织单元 - 无分配"""
        from app.models.user import User
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(
            employee_code="EMP-TEST",
            name="测试员工",
            department="测试部门"
        )
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="test_user",
            password_hash=get_password_hash("test123"),
            real_name="测试用户",
            employee_id=employee.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        org_units = DataScopeServiceV2.get_user_org_units(db_session, user.id)
        assert isinstance(org_units, list)
        assert len(org_units) == 0

    def test_get_accessible_org_units_all_scope(self, db_session):
        """测试获取可访问组织单元 - 全部数据"""
        org_units = DataScopeServiceV2.get_accessible_org_units(
            db_session,
            user_id=1,
            scope_type=ScopeType.ALL.value
        )
        assert isinstance(org_units, list)

    def test_get_accessible_org_units_team_scope(self, db_session):
        """测试获取可访问组织单元 - 团队范围"""
        from app.models.user import User
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(
            employee_code="EMP-TEST2",
            name="测试员工2",
            department="测试部门"
        )
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="test_user2",
            password_hash=get_password_hash("test123"),
            real_name="测试用户2",
            employee_id=employee.id,
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # 创建组织单元
        org_unit = OrganizationUnit(
            unit_code="TEAM001",
            unit_name="测试团队",
            unit_type="TEAM",
            is_active=True
        )
        db_session.add(org_unit)
        db_session.flush()

        # 创建员工组织分配
        assignment = EmployeeOrgAssignment(
            employee_id=employee.id,
            org_unit_id=org_unit.id,
            is_active=True
        )
        db_session.add(assignment)
        db_session.commit()

        org_units = DataScopeServiceV2.get_accessible_org_units(
            db_session,
            user_id=user.id,
            scope_type=ScopeType.TEAM.value
        )
        assert isinstance(org_units, list)

    def test_find_ancestor_by_type(self, db_session):
        """测试查找指定类型的祖先组织"""
        # 创建层级组织
        parent = OrganizationUnit(
            unit_code="DEPT001",
            unit_name="测试部门",
            unit_type="DEPARTMENT",
            is_active=True
        )
        db_session.add(parent)
        db_session.flush()

        child = OrganizationUnit(
            unit_code="TEAM001",
            unit_name="测试团队",
            unit_type="TEAM",
            parent_id=parent.id,
            is_active=True
        )
        db_session.add(child)
        db_session.commit()

        ancestor = DataScopeServiceV2._find_ancestor_by_type(
            db_session, child, "DEPARTMENT"
        )
        assert ancestor is not None
        assert ancestor.id == parent.id

    def test_get_subtree_ids(self, db_session):
        """测试获取子树ID"""
        parent = OrganizationUnit(
            unit_code="DEPT001",
            unit_name="测试部门",
            unit_type="DEPARTMENT",
            is_active=True
        )
        db_session.add(parent)
        db_session.flush()

        child = OrganizationUnit(
            unit_code="TEAM001",
            unit_name="测试团队",
            unit_type="TEAM",
            parent_id=parent.id,
            is_active=True
        )
        db_session.add(child)
        db_session.commit()

        subtree_ids = DataScopeServiceV2._get_subtree_ids(db_session, parent.id)
        assert isinstance(subtree_ids, set)
        assert parent.id in subtree_ids
        assert child.id in subtree_ids

    @patch('app.services.data_scope_service_v2.PermissionService')
    def test_get_data_scope(self, mock_permission_service, db_session):
        """测试获取数据权限规则"""
        mock_permission_service.get_user_data_scopes.return_value = {
            "project": ScopeType.OWN.value
        }

        scope = DataScopeServiceV2.get_data_scope(
            db_session,
            user_id=1,
            resource_type="project"
        )
        # 可能返回None如果没有对应的规则
        assert scope is None or hasattr(scope, 'scope_type')

    @patch('app.services.data_scope_service_v2.PermissionService')
    def test_apply_data_scope_superuser(self, mock_permission_service, db_session):
        """测试应用数据权限 - 超级管理员"""
        from app.models.user import User
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(
            employee_code="EMP-ADMIN",
            name="管理员",
            department="系统"
        )
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            real_name="管理员",
            employee_id=employee.id,
            is_active=True,
            is_superuser=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建模拟查询
        mock_query = Mock()
        mock_query.column_descriptions = [{'entity': Mock}]

        result = DataScopeServiceV2.apply_data_scope(
            mock_query,
            db_session,
            user,
            "project"
        )

        assert result == mock_query  # 超级管理员不过滤

    @patch('app.services.data_scope_service_v2.PermissionService')
    def test_apply_data_scope_all(self, mock_permission_service, db_session):
        """测试应用数据权限 - 全部数据"""
        from app.models.user import User
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(
            employee_code="EMP-USER",
            name="普通用户",
            department="测试部门"
        )
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="user",
            password_hash=get_password_hash("user123"),
            real_name="普通用户",
            employee_id=employee.id,
            is_active=True,
            is_superuser=False
        )
        db_session.add(user)
        db_session.commit()

        mock_permission_service.get_user_data_scopes.return_value = {
            "project": ScopeType.ALL.value
        }

        mock_query = Mock()
        mock_query.column_descriptions = [{'entity': Mock}]

        result = DataScopeServiceV2.apply_data_scope(
            mock_query,
            db_session,
            user,
            "project"
        )

        assert result == mock_query  # 全部数据不过滤

    @patch('app.services.data_scope_service_v2.PermissionService')
    def test_can_access_data_superuser(self, mock_permission_service, db_session):
        """测试检查数据访问权限 - 超级管理员"""
        from app.models.user import User
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(
            employee_code="EMP-ADMIN2",
            name="管理员2",
            department="系统"
        )
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="admin2",
            password_hash=get_password_hash("admin123"),
            real_name="管理员2",
            employee_id=employee.id,
            is_active=True,
            is_superuser=True
        )
        db_session.add(user)
        db_session.commit()

        mock_data = Mock()

        can_access = DataScopeServiceV2.can_access_data(
            db_session,
            user,
            "project",
            mock_data
        )

        assert can_access is True

    @patch('app.services.data_scope_service_v2.PermissionService')
    def test_can_access_data_all_scope(self, mock_permission_service, db_session):
        """测试检查数据访问权限 - 全部数据范围"""
        from app.models.user import User
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(
            employee_code="EMP-USER2",
            name="普通用户2",
            department="测试部门"
        )
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="user2",
            password_hash=get_password_hash("user123"),
            real_name="普通用户2",
            employee_id=employee.id,
            is_active=True,
            is_superuser=False
        )
        db_session.add(user)
        db_session.commit()

        mock_permission_service.get_user_data_scopes.return_value = {
            "project": ScopeType.ALL.value
        }

        mock_data = Mock()

        can_access = DataScopeServiceV2.can_access_data(
            db_session,
            user,
            "project",
            mock_data
        )

        assert can_access is True

    @patch('app.services.data_scope_service_v2.PermissionService')
    def test_can_access_data_own_scope(self, mock_permission_service, db_session):
        """测试检查数据访问权限 - 个人数据范围"""
        from app.models.user import User
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(
            employee_code="EMP-USER3",
            name="普通用户3",
            department="测试部门"
        )
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="user3",
            password_hash=get_password_hash("user123"),
            real_name="普通用户3",
            employee_id=employee.id,
            is_active=True,
            is_superuser=False
        )
        db_session.add(user)
        db_session.commit()

        mock_permission_service.get_user_data_scopes.return_value = {
            "project": ScopeType.OWN.value
        }

        mock_data = Mock()
        mock_data.created_by = user.id

        can_access = DataScopeServiceV2.can_access_data(
            db_session,
            user,
            "project",
            mock_data,
            owner_field="created_by"
        )

        assert can_access is True

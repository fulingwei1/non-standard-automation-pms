# -*- coding: utf-8 -*-
"""
Tests for DataScopeService
"""

from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.data_scope import DataScopeService
from app.models.user import User
from app.models.organization import OrganizationUnit
from app.models.permission import ScopeType


class TestDataScopeService:
    """Test suite for DataScopeService."""

    def test_get_user_org_units_no_assignments(self, db_session: Session):
        """测试获取用户组织单元 - 无分配"""
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(
            employee_code="EMP-TEST", name="测试员工", department="测试部门"
        )
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="test_user",
            password_hash=get_password_hash("test123"),
            real_name="测试用户",
            employee_id=employee.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        org_units = DataScopeService.get_user_org_units(db_session, user.id)
        assert isinstance(org_units, list)
        assert len(org_units) == 0

    def test_get_accessible_org_units_all_scope(self, db_session: Session):
        """测试获取可访问组织单元 - 全部数据"""
        org_units = DataScopeService.get_accessible_org_units(
            db_session, user_id=1, scope_type=ScopeType.ALL.value
        )
        assert isinstance(org_units, list)

    def test_get_subtree_ids(self, db_session: Session):
        """测试获取子树ID"""
        parent = OrganizationUnit(
            unit_code="DEPT001",
            unit_name="测试部门",
            unit_type="DEPARTMENT",
            is_active=True,
        )
        db_session.add(parent)
        db_session.flush()

        child = OrganizationUnit(
            unit_code="TEAM001",
            unit_name="测试团队",
            unit_type="TEAM",
            parent_id=parent.id,
            is_active=True,
        )
        db_session.add(child)
        db_session.commit()

        subtree_ids = DataScopeService._get_subtree_ids(db_session, parent.id)
        assert isinstance(subtree_ids, set)
        assert parent.id in subtree_ids
        assert child.id in subtree_ids

    @patch("app.services.data_scope_service.PermissionService")
    def test_apply_data_scope_superuser(
        self, mock_permission_service, db_session: Session
    ):
        """测试应用数据权限 - 超级管理员"""
        from app.models.organization import Employee
        from app.core.security import get_password_hash

        employee = Employee(employee_code="EMP-ADMIN", name="管理员", department="系统")
        db_session.add(employee)
        db_session.flush()

        user = User(
            username="admin_scope",
            password_hash=get_password_hash("admin123"),
            real_name="管理员",
            employee_id=employee.id,
            is_active=True,
            is_superuser=True,
        )
        db_session.add(user)
        db_session.commit()

        # 创建模拟查询
        mock_query = Mock()
        mock_query.column_descriptions = [{"entity": Mock}]

        result = DataScopeService.apply_data_scope(
            mock_query, db_session, user, "project"
        )

        assert result == mock_query  # 超级管理员不过滤

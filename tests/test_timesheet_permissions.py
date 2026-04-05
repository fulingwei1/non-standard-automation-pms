# -*- coding: utf-8 -*-
"""
工时审批权限测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.core.permissions.timesheet import (
    is_timesheet_admin,
    get_user_manageable_dimensions,
    check_timesheet_approval_permission,
    check_bulk_timesheet_approval_permission,
    has_timesheet_approval_access,
)


class MockUser:
    """模拟用户对象"""
    def __init__(self, id: int, employee_id: int = None, roles=None, reporting_to=None, department_id=None):
        self.id = id
        self.employee_id = employee_id
        self.roles = roles
        self.reporting_to = reporting_to
        self.department_id = department_id


class MockRole:
    def __init__(self, role_code: str = None, role_name: str = None):
        self.role_code = role_code
        self.role_name = role_name


class MockUserRole:
    def __init__(self, role):
        self.role = role


class TestIsTimesheetAdmin:
    """测试 is_timesheet_admin 函数"""

    @patch('app.core.permissions.timesheet.is_superuser')
    def test_superuser_is_admin(self, mock_superuser):
        """超级管理员是工时管理员"""
        mock_superuser.return_value = True
        user = MockUser(id=1)
        assert is_timesheet_admin(user) is True

    def test_admin_role_code_is_admin(self):
        """具有 admin 角色代码的用户"""
        user = MockUser(id=1, roles=[MockUserRole(MockRole(role_code="admin"))])
        assert is_timesheet_admin(user) is True

    def test_timesheet_admin_role_code(self):
        """具有 timesheet_admin 角色代码的用户"""
        user = MockUser(id=1, roles=[MockUserRole(MockRole(role_code="timesheet_admin"))])
        assert is_timesheet_admin(user) is True

    def test_hr_admin_role_code(self):
        """具有 hr_admin 角色代码的用户"""
        user = MockUser(id=1, roles=[MockUserRole(MockRole(role_code="hr_admin"))])
        assert is_timesheet_admin(user) is True

    def test_admin_role_name(self):
        """具有管理员角色名称的用户"""
        user = MockUser(id=1, roles=[MockUserRole(MockRole(role_name="管理员"))])
        assert is_timesheet_admin(user) is True

    def test_timesheet_admin_role_name(self):
        """具有工时管理员角色名称的用户"""
        user = MockUser(id=1, roles=[MockUserRole(MockRole(role_name="工时管理员"))])
        assert is_timesheet_admin(user) is True

    def test_regular_user_with_roles(self):
        """普通用户有非管理角色"""
        user = MockUser(id=1, roles=[MockUserRole(MockRole(role_code="user"))])
        assert is_timesheet_admin(user) is False

    def test_user_without_roles(self):
        """没有角色的用户"""
        user = MockUser(id=1, roles=None)
        assert is_timesheet_admin(user) is False


class MockDb:
    """模拟数据库会话"""
    def __init__(self):
        self.query_results = {}
    
    def query(self, model):
        mock_query = MagicMock()
        if model in self.query_results:
            mock_query.filter.return_value.all.return_value = self.query_results[model]
        else:
            mock_query.filter.return_value.all.return_value = []
        return mock_query


class TestGetUserManageableDimensions:
    """测试 get_user_manageable_dimensions 函数"""

    @patch('app.core.permissions.timesheet.is_timesheet_admin')
    def test_admin_returns_all_dimensions(self, mock_admin):
        """管理员返回所有维度"""
        mock_admin.return_value = True
        db = MockDb()
        user = MockUser(id=1)
        
        result = get_user_manageable_dimensions(db, user)
        
        assert result["is_admin"] is True
        assert result["project_ids"] == set()
        assert result["rd_project_ids"] == set()
        assert result["department_ids"] == set()
        assert result["subordinate_user_ids"] == set()


class TestCheckTimesheetApprovalPermission:
    """测试 check_timesheet_approval_permission 函数"""

    @patch('app.core.permissions.timesheet.is_timesheet_admin')
    @patch('app.core.permissions.timesheet.get_user_manageable_dimensions')
    def test_admin_can_approve_any(self, mock_dims, mock_admin):
        """管理员可以审批任何工时"""
        mock_admin.return_value = True
        
        db = MockDb()
        user = MockUser(id=1)
        timesheet = MagicMock()
        timesheet.user_id = 2
        timesheet.project_id = None
        timesheet.rd_project_id = None
        timesheet.department_id = None
        
        assert check_timesheet_approval_permission(db, timesheet, user) is True

    @patch('app.core.permissions.timesheet.is_timesheet_admin')
    @patch('app.core.permissions.timesheet.get_user_manageable_dimensions')
    def test_cannot_approve_own_timesheet(self, mock_dims, mock_admin):
        """不能审批自己的工时"""
        mock_admin.return_value = False
        mock_dims.return_value = {
            "is_admin": False,
            "project_ids": set(),
            "rd_project_ids": set(),
            "department_ids": set(),
            "subordinate_user_ids": set(),
        }
        
        db = MockDb()
        user = MockUser(id=1)
        timesheet = MagicMock()
        timesheet.user_id = 1  # 自己的工时
        
        assert check_timesheet_approval_permission(db, timesheet, user) is False

    @patch('app.core.permissions.timesheet.is_timesheet_admin')
    @patch('app.core.permissions.timesheet.get_user_manageable_dimensions')
    def test_pm_can_approve_project_timesheet(self, mock_dims, mock_admin):
        """项目经理可以审批项目工时"""
        mock_admin.return_value = False
        mock_dims.return_value = {
            "is_admin": False,
            "project_ids": {100},
            "rd_project_ids": set(),
            "department_ids": set(),
            "subordinate_user_ids": set(),
        }
        
        db = MockDb()
        user = MockUser(id=1)
        timesheet = MagicMock()
        timesheet.user_id = 2
        timesheet.project_id = 100
        timesheet.rd_project_id = None
        timesheet.department_id = None
        
        assert check_timesheet_approval_permission(db, timesheet, user) is True


class TestCheckBulkTimesheetApprovalPermission:
    """测试 check_bulk_timesheet_approval_permission 函数"""

    def test_empty_list_returns_false(self):
        """空列表返回 False"""
        db = MockDb()
        user = MockUser(id=1)
        assert check_bulk_timesheet_approval_permission(db, [], user) is False

    @patch('app.core.permissions.timesheet.check_timesheet_approval_permission')
    def test_all_permitted(self, mock_check):
        """所有工时都允许审批"""
        mock_check.return_value = True
        db = MockDb()
        user = MockUser(id=1)
        timesheets = [MagicMock(), MagicMock()]
        
        assert check_bulk_timesheet_approval_permission(db, timesheets, user) is True

    @patch('app.core.permissions.timesheet.check_timesheet_approval_permission')
    def test_one_not_permitted(self, mock_check):
        """有一条不允许则返回 False"""
        mock_check.side_effect = [True, False]
        db = MockDb()
        user = MockUser(id=1)
        timesheets = [MagicMock(), MagicMock()]
        
        assert check_bulk_timesheet_approval_permission(db, timesheets, user) is False


class TestHasTimesheetApprovalAccess:
    """测试 has_timesheet_approval_access 函数"""

    @patch('app.core.permissions.timesheet.is_timesheet_admin')
    def test_admin_has_access(self, mock_admin):
        """管理员有审批权限"""
        mock_admin.return_value = True
        db = MockDb()
        user = MockUser(id=1)
        
        assert has_timesheet_approval_access(user, db) is True

    @patch('app.core.permissions.timesheet.is_timesheet_admin')
    @patch('app.core.permissions.timesheet.get_user_manageable_dimensions')
    def test_manager_has_access(self, mock_dims, mock_admin):
        """经理有审批权限"""
        mock_admin.return_value = False
        mock_dims.return_value = {
            "is_admin": False,
            "project_ids": {100},
            "rd_project_ids": set(),
            "department_ids": set(),
            "subordinate_user_ids": set(),
        }
        
        db = MockDb()
        user = MockUser(id=1)
        
        assert has_timesheet_approval_access(user, db) is True

    @patch('app.core.permissions.timesheet.is_timesheet_admin')
    @patch('app.core.permissions.timesheet.get_user_manageable_dimensions')
    def test_regular_user_no_access(self, mock_dims, mock_admin):
        """普通用户没有审批权限"""
        mock_admin.return_value = False
        mock_dims.return_value = {
            "is_admin": False,
            "project_ids": set(),
            "rd_project_ids": set(),
            "department_ids": set(),
            "subordinate_user_ids": set(),
        }
        
        db = MockDb()
        user = MockUser(id=1)
        
        assert has_timesheet_approval_access(user, db) is False
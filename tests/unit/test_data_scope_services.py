# -*- coding: utf-8 -*-
"""
数据权限服务单元测试
测试 app/services/data_scope/ 模块
"""

from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest
from sqlalchemy.orm import Session

from app.models.enums import DataScopeEnum
from app.models.organization import Department
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.services.data_scope import (
    DataScopeService,
    ProjectFilterService,
    UserScopeService,
)


class TestUserScopeService:
    """测试 UserScopeService 类"""

    def test_get_user_data_scope_superuser(self):
        """测试超级管理员返回 ALL 权限"""
        mock_db = MagicMock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.is_superuser = True

        result = UserScopeService.get_user_data_scope(mock_db, mock_user)

        assert result == DataScopeEnum.ALL.value

    def test_get_user_data_scope_all(self):
        """测试用户有 ALL 权限的角色"""
        mock_db = MagicMock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_role = Mock()
        mock_role.is_active = True
        mock_role.data_scope = DataScopeEnum.ALL.value

        mock_user_role = Mock()
        mock_user_role.role = mock_role

        mock_user.roles = [mock_user_role]

        result = UserScopeService.get_user_data_scope(mock_db, mock_user)

        assert result == DataScopeEnum.ALL.value

    def test_get_user_data_scope_dept(self):
        """测试用户有 DEPT 权限的角色"""
        mock_db = MagicMock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_role = Mock()
        mock_role.is_active = True
        mock_role.data_scope = DataScopeEnum.DEPT.value

        mock_user_role = Mock()
        mock_user_role.role = mock_role

        mock_user.roles = [mock_user_role]

        result = UserScopeService.get_user_data_scope(mock_db, mock_user)

        assert result == DataScopeEnum.DEPT.value

    def test_get_user_data_scope_subordinate(self):
        """测试用户有 SUBORDINATE 权限的角色"""
        mock_db = MagicMock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_role = Mock()
        mock_role.is_active = True
        mock_role.data_scope = DataScopeEnum.SUBORDINATE.value

        mock_user_role = Mock()
        mock_user_role.role = mock_role

        mock_user.roles = [mock_user_role]

        result = UserScopeService.get_user_data_scope(mock_db, mock_user)

        assert result == DataScopeEnum.SUBORDINATE.value

    def test_get_user_data_scope_project(self):
        """测试用户有 PROJECT 权限的角色"""
        mock_db = MagicMock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_role = Mock()
        mock_role.is_active = True
        mock_role.data_scope = DataScopeEnum.PROJECT.value

        mock_user_role = Mock()
        mock_user_role.role = mock_role

        mock_user.roles = [mock_user_role]

        result = UserScopeService.get_user_data_scope(mock_db, mock_user)

        assert result == DataScopeEnum.PROJECT.value

    def test_get_user_data_scope_own_default(self):
        """测试无角色时默认返回 OWN 权限"""
        mock_db = MagicMock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.roles = []

        result = UserScopeService.get_user_data_scope(mock_db, mock_user)

        assert result == DataScopeEnum.OWN.value

    def test_get_user_data_scope_inactive_role(self):
        """测试非激活角色被忽略"""
        mock_db = MagicMock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_role = Mock()
        mock_role.is_active = False  # 非激活
        mock_role.data_scope = DataScopeEnum.ALL.value

        mock_user_role = Mock()
        mock_user_role.role = mock_role

        mock_user.roles = [mock_user_role]

        result = UserScopeService.get_user_data_scope(mock_db, mock_user)

        assert result == DataScopeEnum.OWN.value

    def test_get_user_data_scope_multiple_roles_returns_widest(self):
        """测试多角色时返回最宽松的权限"""
        mock_db = MagicMock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_role1 = Mock()
        mock_role1.is_active = True
        mock_role1.data_scope = DataScopeEnum.OWN.value

        mock_role2 = Mock()
        mock_role2.is_active = True
        mock_role2.data_scope = DataScopeEnum.DEPT.value

        mock_user_role1 = Mock()
        mock_user_role1.role = mock_role1

        mock_user_role2 = Mock()
        mock_user_role2.role = mock_role2

        mock_user.roles = [mock_user_role1, mock_user_role2]

        result = UserScopeService.get_user_data_scope(mock_db, mock_user)

        assert result == DataScopeEnum.DEPT.value

    def test_get_user_project_ids(self):
        """测试获取用户参与的项目ID列表"""
        mock_db = MagicMock(spec=Session)

        mock_db.query.return_value.filter.return_value.all.return_value = [
        (1,),
        (2,),
        (3,),
        ]

        result = UserScopeService.get_user_project_ids(mock_db, user_id=100)

        assert result == {1, 2, 3}

    def test_get_user_project_ids_no_projects(self):
        """测试用户未参与任何项目"""
        mock_db = MagicMock(spec=Session)

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = UserScopeService.get_user_project_ids(mock_db, user_id=100)

        assert result == set()

    def test_get_subordinate_ids(self):
        """测试获取用户下属ID列表"""
        mock_db = MagicMock(spec=Session)

        mock_db.query.return_value.filter.return_value.all.return_value = [
        (10,),
        (20,),
        ]

        result = UserScopeService.get_subordinate_ids(mock_db, user_id=1)

        assert result == {10, 20}

    def test_get_subordinate_ids_no_subordinates(self):
        """测试用户无下属"""
        mock_db = MagicMock(spec=Session)

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = UserScopeService.get_subordinate_ids(mock_db, user_id=1)

        assert result == set()


class TestProjectFilterService:
    """测试 ProjectFilterService 类"""

    def test_filter_projects_superuser_no_filter(self):
        """测试超级管理员不过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()

        mock_user = Mock(spec=User)
        mock_user.is_superuser = True

        result = ProjectFilterService.filter_projects_by_scope(
        mock_db, mock_query, mock_user
        )

        assert result == mock_query
        mock_query.filter.assert_not_called()

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_filter_projects_all_scope(self, mock_get_scope):
        """测试 ALL 权限不过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_get_scope.return_value = DataScopeEnum.ALL.value

        result = ProjectFilterService.filter_projects_by_scope(
        mock_db, mock_query, mock_user
        )

        assert result == mock_query

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_filter_projects_dept_scope(self, mock_get_scope):
        """测试 DEPT 权限过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.id = 1
        mock_user.department = "技术部"

        mock_get_scope.return_value = DataScopeEnum.DEPT.value

        mock_dept = Mock(spec=Department)
        mock_dept.id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_dept

        result = ProjectFilterService.filter_projects_by_scope(
        mock_db, mock_query, mock_user
        )

        mock_query.filter.assert_called()

    @patch.object(UserScopeService, "get_user_data_scope")
    @patch.object(UserScopeService, "get_subordinate_ids")
    def test_filter_projects_subordinate_scope(
        self, mock_get_subordinates, mock_get_scope
    ):
        """测试 SUBORDINATE 权限过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_get_scope.return_value = DataScopeEnum.SUBORDINATE.value
        mock_get_subordinates.return_value = {10, 20}

        result = ProjectFilterService.filter_projects_by_scope(
        mock_db, mock_query, mock_user
        )

        mock_query.filter.assert_called()

    @patch.object(UserScopeService, "get_user_data_scope")
    @patch.object(UserScopeService, "get_user_project_ids")
    def test_filter_projects_project_scope(self, mock_get_projects, mock_get_scope):
        """测试 PROJECT 权限过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_get_scope.return_value = DataScopeEnum.PROJECT.value
        mock_get_projects.return_value = {1, 2, 3}

        result = ProjectFilterService.filter_projects_by_scope(
        mock_db, mock_query, mock_user
        )

        mock_query.filter.assert_called()

    @patch.object(UserScopeService, "get_user_data_scope")
    @patch.object(UserScopeService, "get_user_project_ids")
    def test_filter_projects_project_scope_no_projects(
        self, mock_get_projects, mock_get_scope
    ):
        """测试 PROJECT 权限无项目时返回空"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_get_scope.return_value = DataScopeEnum.PROJECT.value
        mock_get_projects.return_value = set()  # 无项目

        result = ProjectFilterService.filter_projects_by_scope(
        mock_db, mock_query, mock_user
        )

        # 应该过滤为永不匹配的条件
        mock_query.filter.assert_called()

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_filter_projects_own_scope(self, mock_get_scope):
        """测试 OWN 权限过滤"""
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_get_scope.return_value = DataScopeEnum.OWN.value

        result = ProjectFilterService.filter_projects_by_scope(
        mock_db, mock_query, mock_user
        )

        mock_query.filter.assert_called()

    def test_filter_own_projects(self):
        """测试过滤自己的项目"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query

        mock_user = Mock(spec=User)
        mock_user.id = 1

        result = ProjectFilterService._filter_own_projects(mock_query, mock_user)

        mock_query.filter.assert_called()


class TestCheckProjectAccess:
    """测试项目访问权限检查"""

    def test_check_access_superuser(self):
        """测试超级管理员总是有权限"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.is_superuser = True

        result = ProjectFilterService.check_project_access(mock_db, mock_user, 1)

        assert result is True

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_check_access_all_scope(self, mock_get_scope):
        """测试 ALL 权限总是有权限"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_get_scope.return_value = DataScopeEnum.ALL.value

        result = ProjectFilterService.check_project_access(mock_db, mock_user, 1)

        assert result is True

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_check_access_dept_scope_same_dept(self, mock_get_scope):
        """测试 DEPT 权限同部门有权限"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.department = "技术部"

        mock_get_scope.return_value = DataScopeEnum.DEPT.value

        mock_project = Mock(spec=Project)
        mock_project.dept_id = 10

        mock_dept = Mock(spec=Department)
        mock_dept.id = 10

        mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_project,
        mock_dept,
        ]

        result = ProjectFilterService.check_project_access(mock_db, mock_user, 1)

        assert result is True

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_check_access_dept_scope_different_dept(self, mock_get_scope):
        """测试 DEPT 权限不同部门无权限"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.department = "技术部"

        mock_get_scope.return_value = DataScopeEnum.DEPT.value

        mock_project = Mock(spec=Project)
        mock_project.dept_id = 20  # 不同部门

        mock_dept = Mock(spec=Department)
        mock_dept.id = 10

        mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_project,
        mock_dept,
        ]

        result = ProjectFilterService.check_project_access(mock_db, mock_user, 1)

        assert result is False

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_check_access_own_scope_is_creator(self, mock_get_scope):
        """测试 OWN 权限是创建人"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_get_scope.return_value = DataScopeEnum.OWN.value

        mock_project = Mock(spec=Project)
        mock_project.created_by = 1  # 创建人是自己
        mock_project.pm_id = 2

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = ProjectFilterService.check_project_access(mock_db, mock_user, 1)

        assert result is True

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_check_access_own_scope_is_pm(self, mock_get_scope):
        """测试 OWN 权限是项目经理"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_get_scope.return_value = DataScopeEnum.OWN.value

        mock_project = Mock(spec=Project)
        mock_project.created_by = 2
        mock_project.pm_id = 1  # 项目经理是自己

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = ProjectFilterService.check_project_access(mock_db, mock_user, 1)

        assert result is True

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_check_access_own_scope_no_access(self, mock_get_scope):
        """测试 OWN 权限无关项目"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_get_scope.return_value = DataScopeEnum.OWN.value

        mock_project = Mock(spec=Project)
        mock_project.created_by = 2
        mock_project.pm_id = 3

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = ProjectFilterService.check_project_access(mock_db, mock_user, 1)

        assert result is False

    @patch.object(UserScopeService, "get_user_data_scope")
    def test_check_access_project_not_found(self, mock_get_scope):
        """测试项目不存在"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.is_superuser = False

        mock_get_scope.return_value = DataScopeEnum.OWN.value

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = ProjectFilterService.check_project_access(mock_db, mock_user, 999)

        assert result is False


class TestDataScopeService:
    """测试 DataScopeService 向后兼容类"""

    def test_has_all_methods(self):
        """测试包含所有方法"""
        # User scope methods
        assert hasattr(DataScopeService, "get_user_data_scope")
        assert hasattr(DataScopeService, "get_user_project_ids")
        assert hasattr(DataScopeService, "get_subordinate_ids")

        # Project filter methods
        assert hasattr(DataScopeService, "filter_projects_by_scope")
        assert hasattr(DataScopeService, "check_project_access")
        assert hasattr(DataScopeService, "_filter_own_projects")

        # Issue filter methods
        assert hasattr(DataScopeService, "filter_issues_by_scope")

        # Generic filter methods
        assert hasattr(DataScopeService, "filter_by_scope")
        assert hasattr(DataScopeService, "check_customer_access")

        # Custom rule methods
        assert hasattr(DataScopeService, "get_custom_rule")
        assert hasattr(DataScopeService, "apply_custom_filter")
        assert hasattr(DataScopeService, "validate_scope_config")

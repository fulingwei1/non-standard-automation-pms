# -*- coding: utf-8 -*-
"""
项目权限检查扩展测试

测试 DataScopeService 的项目访问权限功能
（原 app/core/permissions/project.py 已迁移到 app/services/data_scope/）
"""

import pytest
from unittest.mock import MagicMock, patch


class MockUser:
    """模拟用户对象"""

    def __init__(
        self,
        is_superuser: bool = False,
        user_id: int = 1,
        username: str = "test_user",
        tenant_id: int = None,
        roles: list = None,
    ):
        self.is_superuser = is_superuser
        self.id = user_id
        self.username = username
        self.tenant_id = tenant_id
        self.roles = roles or []


@pytest.mark.unit
class TestDataScopeServiceProjectAccess:
    """测试 DataScopeService.check_project_access 方法"""

    def test_superuser_always_has_access(self):
        """测试超级用户始终有项目访问权限"""
        from app.services.data_scope import DataScopeService

        user = MockUser(is_superuser=True)
        db = MagicMock()

        # 超级用户检查直接返回 True，不需要额外 mock
        result = DataScopeService.check_project_access(db, user, 1)
        assert result is True

    def test_user_with_all_scope_has_access(self):
        """测试 ALL 范围用户有访问权限"""
        from app.services.data_scope import DataScopeService

        user = MockUser(is_superuser=False)
        db = MagicMock()

        # Mock UserScopeService.get_user_data_scope 返回 ALL
        with patch(
            "app.services.data_scope.project_filter.UserScopeService.get_user_data_scope",
            return_value="ALL"
        ):
            result = DataScopeService.check_project_access(db, user, 1)
            assert result is True

    def test_user_with_own_scope_access_own_project(self):
        """测试 OWN 范围用户可以访问自己的项目"""
        from app.services.data_scope import DataScopeService

        user = MockUser(is_superuser=False, user_id=100)
        db = MagicMock()

        # Mock 项目存在且用户是项目负责人
        mock_project = MagicMock()
        mock_project.pm_id = 100  # 用户是项目经理
        mock_project.created_by = 100
        db.query.return_value.filter.return_value.first.return_value = mock_project

        # Mock get_user_data_scope 返回 OWN
        # Mock get_user_project_ids 返回用户参与的项目
        with patch(
            "app.services.data_scope.project_filter.UserScopeService.get_user_data_scope",
            return_value="OWN"
        ):
            with patch(
                "app.services.data_scope.project_filter.UserScopeService.get_user_project_ids",
                return_value={1}
            ):
                result = DataScopeService.check_project_access(db, user, 1)
                assert result is True

    def test_user_with_own_scope_cannot_access_others_project(self):
        """测试 OWN 范围用户不能访问别人的项目"""
        from app.services.data_scope import DataScopeService

        user = MockUser(is_superuser=False, user_id=100)
        db = MagicMock()

        # Mock 项目存在但用户不是项目负责人
        mock_project = MagicMock()
        mock_project.pm_id = 999
        mock_project.created_by = 888
        db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch(
            "app.services.data_scope.project_filter.UserScopeService.get_user_data_scope",
            return_value="OWN"
        ):
            with patch(
                "app.services.data_scope.project_filter.UserScopeService.get_user_project_ids",
                return_value=set()
            ):
                result = DataScopeService.check_project_access(db, user, 1)
                assert result is False


@pytest.mark.unit
class TestProjectFilterService:
    """测试 ProjectFilterService"""

    def test_filter_projects_returns_query(self):
        """测试项目过滤返回查询对象"""
        from app.services.data_scope import ProjectFilterService

        user = MockUser(is_superuser=True)
        db = MagicMock()
        query = MagicMock()

        with patch.object(
            ProjectFilterService, 'filter_projects_by_scope', return_value=query
        ):
            result = ProjectFilterService.filter_projects_by_scope(db, user, query)
            assert result is not None

    def test_get_accessible_project_ids_superuser(self):
        """测试超级用户获取所有可访问项目"""
        from app.services.data_scope import DataScopeService

        user = MockUser(is_superuser=True)
        db = MagicMock()

        # Mock 数据库返回项目列表
        db.query.return_value.filter.return_value.all.return_value = [
            (1,), (2,), (3,)
        ]

        result = DataScopeService.get_accessible_project_ids(db, user)
        assert result == {1, 2, 3}


@pytest.mark.unit
class TestUserScopeService:
    """测试 UserScopeService"""

    def test_get_user_data_scope_superuser(self):
        """测试超级用户获取 ALL 范围"""
        from app.services.data_scope import UserScopeService

        user = MockUser(is_superuser=True)
        db = MagicMock()

        # UserScopeService.get_user_data_scope 接受 2 个参数: db, user
        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "ALL"

    def test_get_user_data_scope_normal_user_no_roles(self):
        """测试普通用户无角色获取 OWN 范围"""
        from app.services.data_scope import UserScopeService

        user = MockUser(is_superuser=False, roles=[])
        db = MagicMock()

        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "OWN"

    def test_get_subordinate_ids(self):
        """测试获取下属ID"""
        from app.services.data_scope import UserScopeService

        db = MagicMock()

        # Mock 查询返回下属
        db.query.return_value.filter.return_value.all.return_value = [(2,), (3,)]

        # UserScopeService.get_subordinate_ids 接受 2 个参数: db, user_id
        result = UserScopeService.get_subordinate_ids(db, 1)
        assert result == {2, 3}

    def test_get_subordinate_ids_empty(self):
        """测试无下属返回空集合"""
        from app.services.data_scope import UserScopeService

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = UserScopeService.get_subordinate_ids(db, 1)
        assert result == set()

    def test_get_user_project_ids(self):
        """测试获取用户参与的项目ID"""
        from app.services.data_scope import UserScopeService

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [(1,), (2,)]

        result = UserScopeService.get_user_project_ids(db, 100)
        assert result == {1, 2}


@pytest.mark.unit
class TestDataScopeServiceExports:
    """测试 DataScopeService 导出的方法"""

    def test_all_methods_available(self):
        """测试所有方法都可用"""
        from app.services.data_scope import DataScopeService

        # 用户权限范围方法
        assert hasattr(DataScopeService, 'get_user_data_scope')
        assert hasattr(DataScopeService, 'get_user_project_ids')
        assert hasattr(DataScopeService, 'get_subordinate_ids')

        # 项目过滤方法
        assert hasattr(DataScopeService, 'filter_projects_by_scope')
        assert hasattr(DataScopeService, 'check_project_access')
        assert hasattr(DataScopeService, 'get_accessible_project_ids')
        assert hasattr(DataScopeService, 'filter_related_by_project')

        # 问题过滤方法
        assert hasattr(DataScopeService, 'filter_issues_by_scope')

        # 通用过滤方法
        assert hasattr(DataScopeService, 'filter_by_scope')
        assert hasattr(DataScopeService, 'check_customer_access')

        # 自定义规则方法
        assert hasattr(DataScopeService, 'get_custom_rule')
        assert hasattr(DataScopeService, 'apply_custom_filter')
        assert hasattr(DataScopeService, 'validate_scope_config')

    def test_subservices_available(self):
        """测试子服务类可用"""
        from app.services.data_scope import (
            DataScopeConfig,
            DATA_SCOPE_CONFIGS,
            UserScopeService,
            ProjectFilterService,
            IssueFilterService,
            GenericFilterService,
            CustomRuleService,
        )

        assert DataScopeConfig is not None
        assert DATA_SCOPE_CONFIGS is not None
        assert UserScopeService is not None
        assert ProjectFilterService is not None
        assert IssueFilterService is not None
        assert GenericFilterService is not None
        assert CustomRuleService is not None

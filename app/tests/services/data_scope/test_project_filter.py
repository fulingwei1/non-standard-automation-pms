# -*- coding: utf-8 -*-
"""
ProjectFilterService 测试

测试 app/services/data_scope/project_filter.py 中的核心功能
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


class MockUser:
    def __init__(self, id=1, username="test", department=None, is_superuser=False):
        self.id = id
        self.username = username
        self.department = department
        self.is_superuser = is_superuser
        self.is_active = True


class TestProjectFilterService:
    """ProjectFilterService 测试类"""

    def test_get_accessible_project_ids_superuser(self):
        """测试：超级管理员可以访问所有项目"""
        from app.services.data_scope.user_scope import UserScopeService
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=True)
        
        # Mock 查询返回结果
        mock_db.query.return_value.filter.return_value.all.return_value = [(1,), (2,), (3,)]
        
        from app.services.data_scope.project_filter import ProjectFilterService
        result = ProjectFilterService.get_accessible_project_ids(mock_db, mock_user)
        
        # 超级管理员应该返回所有项目ID
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_get_accessible_project_ids_all_scope(self):
        """测试：ALL 权限可以访问所有项目"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        
        mock_db.query.return_value.filter.return_value.all.return_value = [(1,), (2,), (3,)]
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.ALL.value):
            from app.services.data_scope.project_filter import ProjectFilterService
            result = ProjectFilterService.get_accessible_project_ids(mock_db, mock_user)
            
        # ALL 权限应该返回所有项目ID
        assert 1 in result
        assert 2 in result

    def test_get_accessible_project_ids_own_scope(self):
        """测试：OWN 权限只能访问自己创建/负责的项目"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        
        mock_db.query.return_value.filter.return_value.all.return_value = [(1,), (2,)]
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.OWN.value):
            with patch.object(UserScopeService, 'get_user_project_ids', return_value={3}):
                from app.services.data_scope.project_filter import ProjectFilterService
                result = ProjectFilterService.get_accessible_project_ids(mock_db, mock_user)
                
        # 应该返回项目ID
        assert len(result) > 0

    def test_get_accessible_project_ids_project_scope(self):
        """测试：PROJECT 权限只能访问参与的项目"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.PROJECT.value):
            with patch.object(UserScopeService, 'get_user_project_ids', return_value={1, 2}):
                from app.services.data_scope.project_filter import ProjectFilterService
                result = ProjectFilterService.get_accessible_project_ids(mock_db, mock_user)
                
        # PROJECT 应该返回用户参与的项目ID
        assert 1 in result
        assert 2 in result

    def test_check_project_access_superuser(self):
        """测试：超级管理员可以访问任何项目"""
        mock_user = MockUser(id=1, is_superuser=True)
        
        from app.services.data_scope.project_filter import ProjectFilterService
        result = ProjectFilterService.check_project_access(Mock(), mock_user, project_id=1)
        
        assert result is True

    def test_check_project_access_own(self):
        """测试：OWN 权限检查项目访问权限"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        
        # Mock 项目 - 用户是创建人
        mock_project = Mock()
        mock_project.id = 1
        mock_project.created_by = 1  # 用户自己创建
        mock_project.pm_id = 2
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.OWN.value):
            from app.services.data_scope.project_filter import ProjectFilterService
            result = ProjectFilterService.check_project_access(mock_db, mock_user, project_id=1)
            
        # 用户是创建人，应该有权限
        assert result is True
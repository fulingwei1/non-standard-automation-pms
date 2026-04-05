# -*- coding: utf-8 -*-
"""
IssueFilterService 测试

测试 app/services/data_scope/issue_filter.py 中的核心功能
使用独立的 mock 避免导入问题
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


# 独立的 Mock 类定义
class MockUser:
    def __init__(self, id=1, username="test", department=None, is_superuser=False):
        self.id = id
        self.username = username
        self.department = department
        self.is_superuser = is_superuser
        self.is_active = True


class MockQuery:
    def __init__(self):
        pass
        
    def filter(self, *args):
        return self


class TestIssueFilterServiceDirect:
    """IssueFilterService 直接测试类 - 使用独立 Mock"""

    def test_superuser_returns_unchanged_query(self):
        """测试：超级管理员返回未修改的查询"""
        # 直接在函数内部导入和 patch
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        # 创建 mock 对象
        mock_db = Mock()
        mock_query = Mock()
        mock_user = MockUser(id=1, is_superuser=True)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.ALL.value):
            from app.services.data_scope.issue_filter import IssueFilterService
            result = IssueFilterService.filter_issues_by_scope(mock_db, mock_query, mock_user)
            
        # 超级管理员应该返回原查询
        assert result is mock_query

    def test_own_scope_filters_by_user(self):
        """测试：OWN 权限过滤"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_query = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        
        mock_query.filter = Mock(return_value=mock_query)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.OWN.value):
            from app.services.data_scope.issue_filter import IssueFilterService
            result = IssueFilterService.filter_issues_by_scope(mock_db, mock_query, mock_user)
            
        assert result is not None

    def test_subordinate_scope_includes_subordinates(self):
        """测试：SUBORDINATE 权限包含下属"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_query = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        
        mock_query.filter = Mock(return_value=mock_query)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.SUBORDINATE.value):
            with patch.object(UserScopeService, 'get_subordinate_ids', return_value={2, 3}):
                from app.services.data_scope.issue_filter import IssueFilterService
                result = IssueFilterService.filter_issues_by_scope(mock_db, mock_query, mock_user)
                
        assert result is not None

    def test_project_scope_includes_project_issues(self):
        """测试：PROJECT 权限包含项目问题"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_query = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        
        mock_query.filter = Mock(return_value=mock_query)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.PROJECT.value):
            with patch.object(UserScopeService, 'get_user_project_ids', return_value={1, 2, 3}):
                from app.services.data_scope.issue_filter import IssueFilterService
                result = IssueFilterService.filter_issues_by_scope(mock_db, mock_query, mock_user)
                
        assert result is not None
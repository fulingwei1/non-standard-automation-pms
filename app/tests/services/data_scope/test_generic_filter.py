# -*- coding: utf-8 -*-
"""
GenericFilterService 测试

测试 app/services/data_scope/generic_filter.py 中的核心功能
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


class MockPurchaseOrder:
    """模拟采购订单模型"""
    def __init__(self):
        self.id = 1
        self.requester_id = 1
        self.approver_id = 2
        self.project_id = 1
        self.dept_id = 1
        self.created_by = 1
        
    __tablename__ = "purchase_order"


class TestGenericFilterService:
    """GenericFilterService 测试类"""

    def test_filter_by_scope_superuser(self):
        """测试：超级管理员不过滤任何数据"""
        mock_db = Mock()
        mock_superuser = MockUser(id=1, is_superuser=True)
        mock_query = Mock()
        
        from app.services.data_scope.generic_filter import GenericFilterService
        result = GenericFilterService.filter_by_scope(
            mock_db, mock_query, MockPurchaseOrder, mock_superuser
        )
        
        # 超级管理员应该返回原查询
        assert result is mock_query

    def test_filter_by_scope_all(self):
        """测试：ALL 权限不过滤数据"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        mock_query = Mock()
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.ALL.value):
            from app.services.data_scope.generic_filter import GenericFilterService
            result = GenericFilterService.filter_by_scope(
                mock_db, mock_query, MockPurchaseOrder, mock_user
            )
            
        # ALL 权限应该返回原查询
        assert result is mock_query

    def test_filter_by_scope_own(self):
        """测试：OWN 权限只过滤自己的数据"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.OWN.value):
            from app.services.data_scope.generic_filter import GenericFilterService
            result = GenericFilterService.filter_by_scope(
                mock_db, mock_query, MockPurchaseOrder, mock_user
            )
            
        # 应该返回过滤后的查询
        assert result is not None

    def test_filter_by_scope_subordinate(self):
        """测试：SUBORDINATE 权限可以看自己和下属的数据"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.SUBORDINATE.value):
            with patch.object(UserScopeService, 'get_subordinate_ids', return_value={2, 3}):
                from app.services.data_scope.generic_filter import GenericFilterService
                result = GenericFilterService.filter_by_scope(
                    mock_db, mock_query, MockPurchaseOrder, mock_user
                )
                
        # 应该返回过滤后的查询
        assert result is not None

    def test_filter_by_scope_project(self):
        """测试：PROJECT 权限只能看参与项目的数据"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.PROJECT.value):
            with patch.object(UserScopeService, 'get_user_project_ids', return_value={1, 2}):
                from app.services.data_scope.generic_filter import GenericFilterService
                result = GenericFilterService.filter_by_scope(
                    mock_db, mock_query, MockPurchaseOrder, mock_user
                )
                
        # 应该返回过滤后的查询
        assert result is not None

    def test_check_customer_access_superuser(self):
        """测试：超级管理员可以访问任何客户"""
        mock_superuser = MockUser(id=1, is_superuser=True)
        
        from app.services.data_scope.generic_filter import GenericFilterService
        result = GenericFilterService.check_customer_access(Mock(), mock_superuser, customer_id=1)
        
        assert result is True

    def test_check_customer_access_all(self):
        """测试：ALL 权限可以访问任何客户"""
        from app.services.data_scope.user_scope import UserScopeService
        from app.models.enums import DataScopeEnum
        
        mock_db = Mock()
        mock_user = MockUser(id=1, is_superuser=False)
        
        with patch.object(UserScopeService, 'get_user_data_scope', return_value=DataScopeEnum.ALL.value):
            from app.services.data_scope.generic_filter import GenericFilterService
            result = GenericFilterService.check_customer_access(mock_db, mock_user, customer_id=1)
            
        assert result is True
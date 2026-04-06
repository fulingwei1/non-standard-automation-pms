# -*- coding: utf-8 -*-
"""
毛利率权限服务测试

测试不同角色用户查看毛利率数据的权限控制
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class MockUser:
    """模拟用户对象"""
    def __init__(self, user_id=1, roles=None, is_superuser=False, is_system_admin=False):
        self.id = user_id
        self.roles = roles or []
        self.is_superuser = is_superuser
        self.is_system_admin = is_system_admin


class MockRole:
    """模拟角色对象"""
    def __init__(self, role_code):
        self.role_code = role_code


class TestMarginPermissionService:
    """毛利率权限服务测试"""

    def test_get_user_roles_with_no_roles(self):
        """测试用户没有角色的场景"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.roles = None
        user_roles = MarginPermissionService.get_user_roles(user)
        assert user_roles == set()

    def test_get_user_roles_with_empty_roles(self):
        """测试用户角色为空列表"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.roles = []
        user_roles = MarginPermissionService.get_user_roles(user)
        assert user_roles == set()

    def test_get_user_roles_with_valid_roles(self):
        """测试用户有有效角色"""
        from app.services.margin_permission_service import MarginPermissionService
        
        # 创建模拟用户 - roles 有 all 方法
        user = MagicMock()
        mock_role = MagicMock()
        mock_role.role = MagicMock()
        mock_role.role.role_code = "SALES"
        user.roles = MagicMock()
        user.roles.all = MagicMock(return_value=[mock_role])
        
        user_roles = MarginPermissionService.get_user_roles(user)
        assert "SALES" in user_roles

    def test_can_view_all_margins_superuser(self):
        """测试超级管理员可以查看所有毛利率"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.is_superuser = True
        user.is_system_admin = False
        
        result = MarginPermissionService.can_view_all_margins(user)
        assert result is True

    def test_can_view_all_margins_system_admin(self):
        """测试系统管理员可以查看所有毛利率"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.is_superuser = False
        user.is_system_admin = True
        
        result = MarginPermissionService.can_view_all_margins(user)
        assert result is True

    def test_can_view_all_margins_finance_role(self):
        """测试财务角色可以查看所有毛利率"""
        from app.services.margin_permission_service import MarginPermissionService, ROLE_FINANCE
        
        role = MagicMock()
        role.role_code = ROLE_FINANCE
        
        user = MagicMock()
        user.is_superuser = False
        user.is_system_admin = False
        user.roles = [role]
        
        result = MarginPermissionService.can_view_all_margins(user)
        assert result is True

    def test_can_view_all_margins_management_role(self):
        """测试管理层角色可以查看所有毛利率"""
        from app.services.margin_permission_service import MarginPermissionService, ROLE_MANAGEMENT
        
        role = MagicMock()
        role.role_code = ROLE_MANAGEMENT
        
        user = MagicMock()
        user.is_superuser = False
        user.is_system_admin = False
        user.roles = [role]
        
        result = MarginPermissionService.can_view_all_margins(user)
        assert result is True

    def test_can_view_all_margins_no_full_access(self):
        """测试没有完整访问权限的角色"""
        from app.services.margin_permission_service import MarginPermissionService, ROLE_SALES
        
        # 直接 patch get_user_roles 方法返回销售角色
        with patch('app.services.margin_permission_service.is_superuser', return_value=False):
            with patch('app.services.margin_permission_service.is_system_admin', return_value=False):
                with patch.object(MarginPermissionService, 'get_user_roles', return_value={ROLE_SALES}):
                    user = MagicMock()
                    user.is_superuser = False
                    user.is_system_admin = False
                    
                    result = MarginPermissionService.can_view_all_margins(user)
                    assert result is False

    def test_get_accessible_project_ids_full_access(self):
        """测试有完整访问权限的用户获取所有项目"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.id = 1
        user.is_superuser = True
        
        # Mock db session
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1,), (2,), (3,)]
        mock_db.execute.return_value = mock_result
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=True):
            result = MarginPermissionService.get_accessible_project_ids(user, mock_db)
            assert len(result) == 3

    def test_get_accessible_project_ids_sales_role(self):
        """测试销售角色只能访问自己负责的项目"""
        from app.services.margin_permission_service import MarginPermissionService, ROLE_SALES
        
        role = MagicMock()
        role.role_code = ROLE_SALES
        
        user = MagicMock()
        user.id = 1
        user.is_superuser = False
        user.is_system_admin = False
        user.roles = [role]
        
        # Mock db session
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1,), (2,)]
        mock_db.execute.return_value = mock_result
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=False):
            with patch.object(MarginPermissionService, 'get_user_roles', return_value={ROLE_SALES}):
                result = MarginPermissionService.get_accessible_project_ids(user, mock_db)
                assert len(result) == 2

    def test_get_accessible_project_ids_with_filter(self):
        """测试带项目ID过滤的访问权限"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.id = 1
        user.is_superuser = True
        
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1,), (2,), (3,)]
        mock_db.execute.return_value = mock_result
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=True):
            # 提供过滤列表
            result = MarginPermissionService.get_accessible_project_ids(
                user, mock_db, project_ids=[1, 3]
            )
            assert 1 in result
            assert 3 in result

    def test_can_view_project_margin_full_access(self):
        """测试有完整权限的用户可以查看项目毛利率"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.is_superuser = True
        
        mock_db = MagicMock()
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=True):
            result = MarginPermissionService.can_view_project_margin(user, 1, mock_db)
            assert result is True

    def test_can_view_project_margin_no_access(self):
        """测试没有权限的用户不能查看项目毛利率"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.id = 1
        user.is_superuser = False
        
        mock_db = MagicMock()
        
        # Mock empty accessible ids
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=False):
            with patch.object(MarginPermissionService, 'get_accessible_project_ids', return_value=[]):
                result = MarginPermissionService.can_view_project_margin(user, 1, mock_db)
                assert result is False

    def test_get_margin_visibility_level_full(self):
        """测试完整访问级别的毛利率可见性"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.is_superuser = True
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=True):
            result = MarginPermissionService.get_margin_visibility_level(user)
            assert result == "full"

    def test_get_margin_visibility_level_own(self):
        """测试只能看自己项目的可见性"""
        from app.services.margin_permission_service import MarginPermissionService, ROLE_SALES
        
        role = MagicMock()
        role.role_code = ROLE_SALES
        
        user = MagicMock()
        user.is_superuser = False
        user.roles = [role]
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=False):
            with patch.object(MarginPermissionService, 'get_user_roles', return_value={ROLE_SALES}):
                result = MarginPermissionService.get_margin_visibility_level(user)
                assert result == "own"

    def test_get_margin_visibility_level_none(self):
        """测试无访问权限"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.is_superuser = False
        user.roles = []
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=False):
            with patch.object(MarginPermissionService, 'get_user_roles', return_value=set()):
                result = MarginPermissionService.get_margin_visibility_level(user)
                assert result == "none"

    def test_filter_margin_data_full_access(self):
        """测试完整权限用户不过滤数据"""
        from app.services.margin_permission_service import MarginPermissionService
        
        user = MagicMock()
        user.is_superuser = True
        
        margin_data = {"project_id": 1, "margin_rate": 25.0, "secret_info": "xxx"}
        mock_db = MagicMock()
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=True):
            result = MarginPermissionService.filter_margin_data(user, margin_data, mock_db)
            assert result == margin_data

    def test_filter_margin_data_limited_access(self):
        """测试受限用户过滤数据（当前返回原始数据）"""
        from app.services.margin_permission_service import MarginPermissionService
        
        role = MagicMock()
        role.role_code = "SALES"
        
        user = MagicMock()
        user.is_superuser = False
        user.roles = [role]
        
        margin_data = {"project_id": 1, "margin_rate": 25.0, "secret_info": "xxx"}
        mock_db = MagicMock()
        
        with patch.object(MarginPermissionService, 'can_view_all_margins', return_value=False):
            with patch.object(MarginPermissionService, 'get_user_roles', return_value={"SALES"}):
                result = MarginPermissionService.filter_margin_data(user, margin_data, mock_db)
                # 当前实现返回相同数据
                assert result == margin_data


class TestMarginPermissionConstants:
    """测试权限服务常量定义"""

    def test_role_constants_defined(self):
        """测试角色常量已定义"""
        from app.services.margin_permission_service import (
            ROLE_SALES,
            ROLE_PRESALES,
            ROLE_PM,
            ROLE_FINANCE,
            ROLE_MANAGEMENT,
            ROLE_ADMIN,
        )
        
        assert ROLE_SALES == "SALES"
        assert ROLE_PRESALES == "PRESALES"
        assert ROLE_PM == "PM"
        assert ROLE_FINANCE == "FINANCE"
        assert ROLE_MANAGEMENT == "MANAGEMENT"
        assert ROLE_ADMIN == "ADMIN"

    def test_full_access_roles_set(self):
        """测试完整访问角色集合"""
        from app.services.margin_permission_service import FULL_ACCESS_ROLES
        
        assert "FINANCE" in FULL_ACCESS_ROLES
        assert "MANAGEMENT" in FULL_ACCESS_ROLES
        assert "ADMIN" in FULL_ACCESS_ROLES
        assert len(FULL_ACCESS_ROLES) == 3


class TestMarginPermissionConvenienceFunctions:
    """测试便捷函数"""

    def test_can_view_project_margin_function(self):
        """测试便捷函数 can_view_project_margin"""
        from app.services.margin_permission_service import can_view_project_margin
        
        user = MagicMock()
        user.is_superuser = True
        
        mock_db = MagicMock()
        
        with patch('app.services.margin_permission_service.MarginPermissionService.can_view_project_margin', return_value=True) as mock:
            result = can_view_project_margin(user, 1, mock_db)
            assert result is True

    def test_get_accessible_project_ids_function(self):
        """测试便捷函数 get_accessible_project_ids"""
        from app.services.margin_permission_service import get_accessible_project_ids
        
        user = MagicMock()
        user.is_superuser = True
        
        mock_db = MagicMock()
        
        with patch('app.services.margin_permission_service.MarginPermissionService.get_accessible_project_ids', return_value=[1, 2, 3]) as mock:
            result = get_accessible_project_ids(user, mock_db)
            assert result == [1, 2, 3]

    def test_get_margin_visibility_level_function(self):
        """测试便捷函数 get_margin_visibility_level"""
        from app.services.margin_permission_service import get_margin_visibility_level
        
        user = MagicMock()
        
        with patch('app.services.margin_permission_service.MarginPermissionService.get_margin_visibility_level', return_value="full") as mock:
            result = get_margin_visibility_level(user)
            assert result == "full"
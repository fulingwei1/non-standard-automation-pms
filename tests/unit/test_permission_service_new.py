# -*- coding: utf-8 -*-
"""
测试权限服务

测试 app/services/permission_management/permission_service.py
"""

import pytest
from unittest.mock import MagicMock, patch, create_autospec
from sqlalchemy.orm import Session
import sys

# Setup proper module hierarchy before any imports
class MockPermissionCacheService:
    pass

# Setup modules
if 'app.services.permission_management' not in sys.modules:
    sys.modules['app.services.permission_management'] = MagicMock()
    sys.modules['app.services.permission_management.permission_cache_service'] = MockPermissionCacheService()

# Now mock the permission engine module 
if 'app.core.permission_engine' not in sys.modules:
    sys.modules['app.core.permission_engine'] = MagicMock()

# Import after mocking
from app.services.permission_management import permission_service


class TestPermissionService:
    """测试 PermissionService"""

    def test_permission_service_class_exists(self):
        """测试 PermissionService 类存在"""
        assert hasattr(permission_service, 'PermissionService')
        assert permission_service.PermissionService is not None

    def test_check_permission_method_exists(self):
        """测试 check_permission 方法存在"""
        assert hasattr(permission_service.PermissionService, 'check_permission')
        assert callable(permission_service.PermissionService.check_permission)

    def test_check_any_permission_method_exists(self):
        """测试 check_any_permission 方法存在"""
        assert hasattr(permission_service.PermissionService, 'check_any_permission')

    def test_check_all_permissions_method_exists(self):
        """测试 check_all_permissions 方法存在"""
        assert hasattr(permission_service.PermissionService, 'check_all_permissions')

    def test_get_user_permissions_method_exists(self):
        """测试 get_user_permissions 方法存在"""
        assert hasattr(permission_service.PermissionService, 'get_user_permissions')

    def test_get_user_effective_roles_method_exists(self):
        """测试 get_user_effective_roles 方法存在"""
        assert hasattr(permission_service.PermissionService, 'get_user_effective_roles')

    def test_get_user_menus_method_exists(self):
        """测试 get_user_menus 方法存在"""
        assert hasattr(permission_service.PermissionService, 'get_user_menus')

    def test_get_user_data_scopes_method_exists(self):
        """测试 get_user_data_scopes 方法存在"""
        assert hasattr(permission_service.PermissionService, 'get_user_data_scopes')

    def test_get_full_permission_data_method_exists(self):
        """测试 get_full_permission_data 方法存在"""
        assert hasattr(permission_service.PermissionService, 'get_full_permission_data')

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = MagicMock(spec=Session)
        return db

    def test_check_permission_superuser(self, mock_db):
        """测试超级管理员直接放行"""
        mock_user = MagicMock()
        mock_user.is_superuser = True
        mock_user.tenant_id = 1
        
        result = permission_service.PermissionService.check_permission(
            db=mock_db,
            user_id=1,
            permission_code="any:permission",
            user=mock_user
        )
        
        assert result is True

    def test_check_permission_normal_user(self, mock_db):
        """测试普通用户权限检查"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = 1
        
        with patch.object(permission_service.PermissionService, 'get_user_permissions') as mock_get:
            mock_get.return_value = ["sales:read", "sales:write"]
            
            result = permission_service.PermissionService.check_permission(
                db=mock_db,
                user_id=1,
                permission_code="sales:read",
                user=mock_user
            )
            
            assert result is True

    def test_check_permission_not_have(self, mock_db):
        """测试用户没有权限"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = 1
        
        with patch.object(permission_service.PermissionService, 'get_user_permissions') as mock_get:
            mock_get.return_value = ["sales:read"]
            
            result = permission_service.PermissionService.check_permission(
                db=mock_db,
                user_id=1,
                permission_code="sales:delete",
                user=mock_user
            )
            
            assert result is False

    def test_check_any_permission_true(self, mock_db):
        """测试任一权限检查返回 True"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = 1
        
        with patch.object(permission_service.PermissionService, 'get_user_permissions') as mock_get:
            mock_get.return_value = ["sales:read", "customer:read"]
            
            result = permission_service.PermissionService.check_any_permission(
                db=mock_db,
                user_id=1,
                permission_codes=["sales:write", "customer:read"],
                user=mock_user
            )
            
            assert result is True

    def test_check_all_permissions_true(self, mock_db):
        """测试所有权限检查返回 True"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = 1
        
        with patch.object(permission_service.PermissionService, 'get_user_permissions') as mock_get:
            mock_get.return_value = ["sales:read", "sales:write", "sales:delete"]
            
            result = permission_service.PermissionService.check_all_permissions(
                db=mock_db,
                user_id=1,
                permission_codes=["sales:read", "sales:write"],
                user=mock_user
            )
            
            assert result is True

    def test_get_user_permissions_returns_list(self, mock_db):
        """测试获取用户权限返回列表"""
        with patch('app.services.permission_management.permission_service.load_permissions') as mock_load:
            mock_load.return_value = {"sales:read", "sales:write"}
            
            result = permission_service.PermissionService.get_user_permissions(
                db=mock_db,
                user_id=1,
                tenant_id=1
            )
            
            assert isinstance(result, list)
            assert "sales:read" in result


class TestPermissionServiceCompat:
    """测试兼容层函数"""

    def test_check_permission_compat_exists(self):
        """测试兼容函数存在"""
        assert hasattr(permission_service, 'check_permission_compat')
        assert callable(permission_service.check_permission_compat)

    def test_has_module_permission_exists(self):
        """测试模块权限检查函数存在"""
        assert hasattr(permission_service, 'has_module_permission')
        assert callable(permission_service.has_module_permission)


class TestPermissionServiceMenu:
    """测试菜单和权限数据获取"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = MagicMock(spec=Session)
        return db

    def test_get_user_data_scopes_empty(self, mock_db):
        """测试用户无角色时返回空"""
        # 模拟用户无角色
        with patch.object(permission_service.PermissionService, 'get_user_effective_roles', return_value=[]):
            result = permission_service.PermissionService.get_user_data_scopes(mock_db, 1)
            
            assert result == {}

    def test_get_full_permission_data(self, mock_db):
        """测试获取完整权限数据"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = 1
        
        with patch.object(permission_service.PermissionService, 'get_user_permissions', return_value=["sales:read"]):
            with patch.object(permission_service.PermissionService, 'get_user_effective_roles', return_value=[]):
                with patch.object(permission_service.PermissionService, 'get_user_menus', return_value=[]):
                    with patch.object(permission_service.PermissionService, 'get_user_data_scopes', return_value={}):
                        result = permission_service.PermissionService.get_full_permission_data(mock_db, 1, mock_user)
                        
                        assert 'permissions' in result
                        assert 'menus' in result
                        assert 'dataScopes' in result
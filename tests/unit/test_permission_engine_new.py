# -*- coding: utf-8 -*-
"""
测试权限引擎

测试 app/core/permission_engine.py
"""

import pytest
from unittest.mock import MagicMock, patch, create_autospec
from sqlalchemy.orm import Session
import sys

# Create proper mock modules
class MockNotificationHandlers:
    pass

class MockEmailHandler:
    pass
    
class MockSMSHandler:
    pass

# First set up proper module hierarchy
if 'app.services.notification_handlers' not in sys.modules:
    sys.modules['app.services.notification_handlers'] = MockNotificationHandlers()
if 'app.services.notification_handlers.email_handler' not in sys.modules:
    sys.modules['app.services.notification_handlers.email_handler'] = MockEmailHandler()
if 'app.services.notification_handlers.sms_handler' not in sys.modules:
    sys.modules['app.services.notification_handlers.sms_handler'] = MockSMSHandler()

# Now import the target module
from app.core import permission_engine


class TestPermissionEngine:
    """测试统一权限引擎"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = MagicMock(spec=Session)
        return db

    def test_load_permissions_function_exists(self):
        """测试 load_permissions 函数存在"""
        assert hasattr(permission_engine, 'load_permissions')
        assert callable(permission_engine.load_permissions)

    def test_check_permission_for_user_exists(self):
        """测试 check_permission_for_user 函数存在"""
        assert hasattr(permission_engine, 'check_permission_for_user')
        assert callable(permission_engine.check_permission_for_user)

    def test_check_any_permission_for_user_exists(self):
        """测试 check_any_permission_for_user 函数存在"""
        assert hasattr(permission_engine, 'check_any_permission_for_user')
        assert callable(permission_engine.check_permission_for_user)

    def test_check_all_permissions_for_user_exists(self):
        """测试 check_all_permissions_for_user 函数存在"""
        assert hasattr(permission_engine, 'check_all_permissions_for_user')
        assert callable(permission_engine.check_all_permissions_for_user)

    def test_load_permissions_from_db_exists(self):
        """测试内部函数 _load_permissions_from_db 存在"""
        assert hasattr(permission_engine, '_load_permissions_from_db')

    def test_load_permissions_returns_set(self, mock_db):
        """测试 load_permissions 返回集合类型（无缓存情况）"""
        with patch.object(permission_engine, '_load_permissions_from_db') as mock_load:
            mock_load.return_value = {"sales:read", "sales:write"}
            
            with patch('app.core.permission_engine.get_permission_cache_service', side_effect=Exception("no cache")):
                result = permission_engine.load_permissions(
                    user_id=1,
                    db=mock_db,
                    tenant_id=1
                )
            
            assert isinstance(result, set)

    def test_load_permissions_with_tenant(self, mock_db):
        """测试带租户参数的权限加载"""
        with patch.object(permission_engine, '_load_permissions_from_db') as mock_load:
            mock_load.return_value = {"sales:read"}
            
            with patch('app.core.permission_engine.get_permission_cache_service', side_effect=Exception("no cache")):
                result = permission_engine.load_permissions(
                    user_id=1,
                    db=mock_db,
                    tenant_id=1
                )
            
            mock_load.assert_called_once_with(1, mock_db, 1)

    def test_load_permissions_without_tenant(self, mock_db):
        """测试不带租户参数的权限加载（超管场景）"""
        with patch.object(permission_engine, '_load_permissions_from_db') as mock_load:
            mock_load.return_value = {"sales:read", "admin:all"}
            
            with patch('app.core.permission_engine.get_permission_cache_service', side_effect=Exception("no cache")):
                result = permission_engine.load_permissions(
                    user_id=1,
                    db=mock_db,
                    tenant_id=None
                )
            
            mock_load.assert_called_once_with(1, mock_db, None)

    def test_check_permission_for_user_true(self, mock_db):
        """测试权限检查返回 True"""
        with patch.object(permission_engine, 'load_permissions') as mock_load_perms:
            mock_load_perms.return_value = {"sales:read", "sales:write"}
            
            result = permission_engine.check_permission_for_user(
                user_id=1,
                permission_code="sales:read",
                db=mock_db,
                tenant_id=1
            )
            
            assert result is True

    def test_check_permission_for_user_false(self, mock_db):
        """测试权限检查返回 False"""
        with patch.object(permission_engine, 'load_permissions') as mock_load_perms:
            mock_load_perms.return_value = {"sales:read"}
            
            result = permission_engine.check_permission_for_user(
                user_id=1,
                permission_code="sales:write",
                db=mock_db,
                tenant_id=1
            )
            
            assert result is False

    def test_check_any_permission_for_user_true(self, mock_db):
        """测试任一权限检查返回 True"""
        with patch.object(permission_engine, 'load_permissions') as mock_load_perms:
            mock_load_perms.return_value = {"sales:read", "customer:read"}
            
            result = permission_engine.check_any_permission_for_user(
                user_id=1,
                permission_codes=["sales:write", "customer:read"],
                db=mock_db,
                tenant_id=1
            )
            
            assert result is True

    def test_check_any_permission_for_user_false(self, mock_db):
        """测试任一权限检查返回 False"""
        with patch.object(permission_engine, 'load_permissions') as mock_load_perms:
            mock_load_perms.return_value = {"sales:read"}
            
            result = permission_engine.check_any_permission_for_user(
                user_id=1,
                permission_codes=["sales:write", "customer:read"],
                db=mock_db,
                tenant_id=1
            )
            
            assert result is False

    def test_check_all_permissions_for_user_true(self, mock_db):
        """测试所有权限检查返回 True"""
        with patch.object(permission_engine, 'load_permissions') as mock_load_perms:
            mock_load_perms.return_value = {"sales:read", "sales:write", "sales:delete"}
            
            result = permission_engine.check_all_permissions_for_user(
                user_id=1,
                permission_codes=["sales:read", "sales:write"],
                db=mock_db,
                tenant_id=1
            )
            
            assert result is True

    def test_check_all_permissions_for_user_false(self, mock_db):
        """测试所有权限检查返回 False"""
        with patch.object(permission_engine, 'load_permissions') as mock_load_perms:
            mock_load_perms.return_value = {"sales:read"}
            
            result = permission_engine.check_all_permissions_for_user(
                user_id=1,
                permission_codes=["sales:read", "sales:write"],
                db=mock_db,
                tenant_id=1
            )
            
            assert result is False

    def test_load_permissions_cache_error(self, mock_db):
        """测试缓存错误时回退到数据库"""
        with patch.object(permission_engine, '_load_permissions_from_db') as mock_db_load:
            mock_db_load.return_value = {"db:permission"}
            
            with patch('app.core.permission_engine.get_permission_cache_service', side_effect=Exception("Cache error")):
                result = permission_engine.load_permissions(
                    user_id=1,
                    db=mock_db,
                    tenant_id=1
                )
                
                # 应该回退到数据库
                mock_db_load.assert_called_once()
                assert result == {"db:permission"}
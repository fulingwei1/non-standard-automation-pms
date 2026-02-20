# -*- coding: utf-8 -*-
"""
权限管理服务单元测试

覆盖 PermissionManagementService 的主要功能
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import List

from app.services.permission_management import PermissionManagementService


class TestPermissionManagementService(unittest.TestCase):
    """权限管理服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.db_mock = MagicMock()
        self.service = PermissionManagementService(self.db_mock)
    
    def test_list_permissions_basic(self):
        """测试基础权限列表查询"""
        # 准备测试数据
        mock_permission = MagicMock()
        mock_permission.id = 1
        mock_permission.perm_code = "test:read"
        mock_permission.module = "test"
        
        query_mock = MagicMock()
        query_mock.count.return_value = 1
        query_mock.all.return_value = [mock_permission]
        
        # 配置链式调用
        self.db_mock.query.return_value.filter.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        
        # 执行测试
        result = self.service.list_permissions(
            tenant_id=1,
            page=1,
            page_size=10,
        )
        
        # 验证结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0].perm_code, "test:read")
    
    def test_list_permissions_with_filters(self):
        """测试带筛选条件的权限列表查询"""
        query_mock = MagicMock()
        query_mock.count.return_value = 0
        query_mock.all.return_value = []
        
        # 配置链式调用
        self.db_mock.query.return_value.filter.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        
        # 执行测试（带多个筛选条件）
        result = self.service.list_permissions(
            tenant_id=1,
            page=1,
            page_size=10,
            module="users",
            action="read",
            keyword="user",
            is_active=True,
        )
        
        # 验证过滤条件被调用
        self.assertTrue(query_mock.filter.called)
        self.assertEqual(result["total"], 0)
    
    def test_list_modules(self):
        """测试获取模块列表"""
        # 准备测试数据
        query_mock = MagicMock()
        query_mock.all.return_value = [("users",), ("roles",), ("permissions",)]
        
        # 配置链式调用
        self.db_mock.query.return_value.filter.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.distinct.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        
        # 执行测试
        result = self.service.list_modules(tenant_id=1)
        
        # 验证结果
        self.assertEqual(len(result), 3)
        self.assertIn("users", result)
        self.assertIn("roles", result)
    
    def test_get_permission_found(self):
        """测试获取权限详情（存在）"""
        # 准备测试数据
        mock_permission = MagicMock()
        mock_permission.id = 1
        mock_permission.perm_code = "test:read"
        
        query_mock = MagicMock()
        query_mock.first.return_value = mock_permission
        
        # 配置链式调用
        self.db_mock.query.return_value.filter.return_value = query_mock
        
        # 执行测试
        result = self.service.get_permission(permission_id=1, tenant_id=1)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.perm_code, "test:read")
    
    def test_get_permission_not_found(self):
        """测试获取权限详情（不存在）"""
        query_mock = MagicMock()
        query_mock.first.return_value = None
        
        self.db_mock.query.return_value.filter.return_value = query_mock
        
        # 执行测试
        result = self.service.get_permission(permission_id=999, tenant_id=1)
        
        # 验证结果
        self.assertIsNone(result)
    
    def test_check_permission_code_exists(self):
        """测试检查权限编码是否存在"""
        # 场景1：存在
        mock_permission = MagicMock()
        query_mock = MagicMock()
        query_mock.first.return_value = mock_permission
        
        self.db_mock.query.return_value.filter.return_value = query_mock
        
        exists = self.service.check_permission_code_exists("test:read", 1)
        self.assertTrue(exists)
        
        # 场景2：不存在
        query_mock.first.return_value = None
        exists = self.service.check_permission_code_exists("test:write", 1)
        self.assertFalse(exists)
    
    def test_create_permission(self):
        """测试创建权限"""
        # 准备测试数据
        mock_permission = MagicMock()
        mock_permission.id = 1
        mock_permission.perm_code = "test:read"
        mock_permission.perm_name = "测试读取"
        
        # 配置 mock
        self.db_mock.add.return_value = None
        self.db_mock.commit.return_value = None
        self.db_mock.refresh.return_value = None
        
        # 模拟 ApiPermission 构造
        with patch('app.services.permission_management.permission_management_service.ApiPermission') as MockPermission:
            MockPermission.return_value = mock_permission
            
            # 执行测试
            result = self.service.create_permission(
                tenant_id=1,
                perm_code="test:read",
                perm_name="测试读取",
                module="test",
            )
            
            # 验证结果
            self.db_mock.add.assert_called_once()
            self.db_mock.commit.assert_called_once()
            self.db_mock.refresh.assert_called_once()
            self.assertEqual(result.perm_code, "test:read")
    
    def test_update_permission(self):
        """测试更新权限"""
        # 准备测试数据
        mock_permission = MagicMock()
        mock_permission.perm_name = "旧名称"
        mock_permission.module = "old_module"
        
        # 执行测试
        result = self.service.update_permission(
            permission=mock_permission,
            perm_name="新名称",
            module="new_module",
            is_active=False,
        )
        
        # 验证更新
        self.assertEqual(mock_permission.perm_name, "新名称")
        self.assertEqual(mock_permission.module, "new_module")
        self.assertEqual(mock_permission.is_active, False)
        self.db_mock.commit.assert_called_once()
        self.db_mock.refresh.assert_called_once()
    
    def test_count_roles_using_permission(self):
        """测试统计使用权限的角色数量"""
        query_mock = MagicMock()
        query_mock.count.return_value = 3
        
        self.db_mock.query.return_value.filter.return_value = query_mock
        
        # 执行测试
        count = self.service.count_roles_using_permission(permission_id=1)
        
        # 验证结果
        self.assertEqual(count, 3)
    
    def test_delete_permission(self):
        """测试删除权限"""
        mock_permission = MagicMock()
        mock_permission.id = 1
        
        # 执行测试
        self.service.delete_permission(mock_permission)
        
        # 验证删除操作
        self.db_mock.delete.assert_called_once_with(mock_permission)
        self.db_mock.commit.assert_called_once()
    
    def test_get_role(self):
        """测试获取角色"""
        # 准备测试数据
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.role_code = "admin"
        
        query_mock = MagicMock()
        query_mock.first.return_value = mock_role
        
        self.db_mock.query.return_value.filter.return_value = query_mock
        
        # 执行测试
        result = self.service.get_role(role_id=1, tenant_id=1)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.role_code, "admin")
    
    def test_get_role_permissions(self):
        """测试获取角色权限列表"""
        # 准备测试数据
        mock_perm1 = MagicMock()
        mock_perm1.id = 1
        mock_perm1.perm_code = "user:read"
        
        mock_perm2 = MagicMock()
        mock_perm2.id = 2
        mock_perm2.perm_code = "user:write"
        
        query_mock = MagicMock()
        query_mock.all.return_value = [mock_perm1, mock_perm2]
        
        # 配置链式调用
        self.db_mock.query.return_value.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        
        # 执行测试
        result = self.service.get_role_permissions(role_id=1)
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].perm_code, "user:read")
    
    def test_assign_role_permissions(self):
        """测试分配角色权限"""
        # 准备测试数据
        mock_permission = MagicMock()
        mock_permission.id = 1
        
        query_mock = MagicMock()
        query_mock.delete.return_value = None
        query_mock.first.return_value = mock_permission
        
        # 配置链式调用
        self.db_mock.query.return_value.filter.return_value = query_mock
        
        # 模拟 RoleApiPermission 构造
        with patch('app.services.permission_management.permission_management_service.RoleApiPermission') as MockRolePermission:
            # 执行测试
            valid_count = self.service.assign_role_permissions(
                role_id=1,
                permission_ids=[1, 2, 3],
                tenant_id=1,
            )
            
            # 验证删除旧关联
            query_mock.delete.assert_called_once()
            # 验证添加新关联
            self.db_mock.add.assert_called()
            self.db_mock.commit.assert_called_once()
    
    def test_invalidate_permission_cache(self):
        """测试清除权限缓存"""
        # 测试缓存失效（允许失败）
        with patch('app.services.permission_management.permission_management_service.get_permission_cache_service') as mock_cache:
            mock_cache_service = MagicMock()
            mock_cache.return_value = mock_cache_service
            
            # 执行测试
            self.service.invalidate_permission_cache(role_id=1, tenant_id=1)
            
            # 验证缓存失效被调用
            mock_cache_service.invalidate_role_and_users.assert_called_once_with(1, tenant_id=1)
    
    def test_get_user(self):
        """测试获取用户"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        
        query_mock = MagicMock()
        query_mock.first.return_value = mock_user
        
        self.db_mock.query.return_value.filter.return_value = query_mock
        
        # 执行测试
        result = self.service.get_user(user_id=1)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.username, "testuser")
    
    def test_get_user_permissions(self):
        """测试获取用户权限"""
        # 准备测试数据
        mock_permission = MagicMock()
        mock_permission.id = 1
        mock_permission.perm_code = "user:read"
        
        query_mock = MagicMock()
        query_mock.all.return_value = [mock_permission]
        
        # 配置链式调用
        self.db_mock.query.return_value.filter.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        
        # Mock PermissionService
        with patch('app.services.permission_management.permission_management_service.PermissionService') as MockPermissionService:
            MockPermissionService.get_user_permissions.return_value = ["user:read"]
            
            # 执行测试
            result = self.service.get_user_permissions(user_id=1, tenant_id=1)
            
            # 验证结果
            self.assertEqual(len(result), 1)
            MockPermissionService.get_user_permissions.assert_called_once()
    
    def test_check_user_permission(self):
        """测试检查用户权限"""
        mock_user = MagicMock()
        mock_user.id = 1
        
        # Mock PermissionService
        with patch('app.services.permission_management.permission_management_service.PermissionService') as MockPermissionService:
            MockPermissionService.check_permission.return_value = True
            
            # 执行测试
            has_permission = self.service.check_user_permission(
                user_id=1,
                permission_code="user:read",
                user=mock_user,
                tenant_id=1,
            )
            
            # 验证结果
            self.assertTrue(has_permission)
            MockPermissionService.check_permission.assert_called_once()


if __name__ == "__main__":
    unittest.main()

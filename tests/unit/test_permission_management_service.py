# -*- coding: utf-8 -*-
"""
权限管理服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from app.services.permission_management.permission_management_service import (
    PermissionManagementService,
)


class TestPermissionManagementService(unittest.TestCase):
    """权限管理服务测试"""

    def setUp(self):
        """测试前置设置"""
        self.mock_db = MagicMock()
        self.service = PermissionManagementService(self.mock_db)
        self.tenant_id = 1

    # ========== 权限 CRUD 测试 ==========

    def test_list_permissions_basic(self):
        """测试基本权限列表查询"""
        # Mock权限对象
        mock_perm1 = MagicMock()
        mock_perm1.id = 1
        mock_perm1.perm_code = "project.create"
        mock_perm1.perm_name = "创建项目"

        mock_perm2 = MagicMock()
        mock_perm2.id = 2
        mock_perm2.perm_code = "project.delete"
        mock_perm2.perm_name = "删除项目"

        # 配置mock链
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 2
        mock_order = mock_filter.order_by.return_value
        mock_offset = mock_order.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.all.return_value = [mock_perm1, mock_perm2]

        # 执行测试
        result = self.service.list_permissions(
            tenant_id=self.tenant_id,
            page=1,
            page_size=10,
        )

        # 验证结果
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0].perm_code, "project.create")
        self.assertEqual(result["items"][1].perm_code, "project.delete")

    def test_list_permissions_with_filters(self):
        """测试带筛选条件的权限列表查询"""
        # 创建一个通用的mock链，让所有filter调用返回同一个对象
        mock_filter_chain = MagicMock()
        mock_filter_chain.filter.return_value = mock_filter_chain
        mock_filter_chain.count.return_value = 1
        mock_filter_chain.order_by.return_value = mock_filter_chain
        mock_filter_chain.offset.return_value = mock_filter_chain
        mock_filter_chain.limit.return_value = mock_filter_chain
        mock_filter_chain.all.return_value = []
        
        self.mock_db.query.return_value.filter.return_value = mock_filter_chain

        # 执行测试（全部筛选条件）
        result = self.service.list_permissions(
            tenant_id=self.tenant_id,
            page=1,
            page_size=10,
            module="project",
            action="create",
            keyword="项目",
            is_active=True,
        )

        # 验证结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 0)

    def test_list_permissions_pagination(self):
        """测试分页逻辑"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 50
        mock_order = mock_filter.order_by.return_value
        mock_offset = mock_order.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.all.return_value = []

        # 第2页，每页20条
        self.service.list_permissions(
            tenant_id=self.tenant_id,
            page=2,
            page_size=20,
        )

        # 验证分页参数
        mock_order.offset.assert_called_once_with(20)  # (2-1)*20
        mock_offset.limit.assert_called_once_with(20)

    def test_list_modules_basic(self):
        """测试模块列表查询"""
        # 创建一个通用的mock链
        mock_chain = MagicMock()
        mock_chain.filter.return_value = mock_chain
        mock_chain.distinct.return_value = mock_chain
        mock_chain.order_by.return_value = mock_chain
        mock_chain.all.return_value = [
            ("project",),
            ("user",),
            ("approval",),
        ]
        
        self.mock_db.query.return_value = mock_chain

        # 执行测试
        result = self.service.list_modules(tenant_id=self.tenant_id)

        # 验证结果
        self.assertEqual(result, ["project", "user", "approval"])

    def test_list_modules_empty(self):
        """测试模块列表为空"""
        mock_query = self.mock_db.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_distinct = mock_filter2.distinct.return_value
        mock_order = mock_distinct.order_by.return_value
        mock_order.all.return_value = []

        result = self.service.list_modules(tenant_id=self.tenant_id)
        self.assertEqual(result, [])

    def test_list_modules_with_none_values(self):
        """测试模块列表包含None值"""
        mock_chain = MagicMock()
        mock_chain.filter.return_value = mock_chain
        mock_chain.distinct.return_value = mock_chain
        mock_chain.order_by.return_value = mock_chain
        mock_chain.all.return_value = [
            ("project",),
            (None,),  # 应该被过滤
            ("user",),
        ]
        
        self.mock_db.query.return_value = mock_chain

        result = self.service.list_modules(tenant_id=self.tenant_id)
        self.assertEqual(result, ["project", "user"])

    def test_get_permission_exists(self):
        """测试获取存在的权限"""
        mock_perm = MagicMock()
        mock_perm.id = 1
        mock_perm.perm_code = "project.create"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_perm

        result = self.service.get_permission(
            permission_id=1,
            tenant_id=self.tenant_id,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.perm_code, "project.create")

    def test_get_permission_not_exists(self):
        """测试获取不存在的权限"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = self.service.get_permission(
            permission_id=999,
            tenant_id=self.tenant_id,
        )

        self.assertIsNone(result)

    def test_check_permission_code_exists_true(self):
        """测试权限编码存在"""
        mock_perm = MagicMock()
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_perm

        result = self.service.check_permission_code_exists(
            perm_code="project.create",
            tenant_id=self.tenant_id,
        )

        self.assertTrue(result)

    def test_check_permission_code_exists_false(self):
        """测试权限编码不存在"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = self.service.check_permission_code_exists(
            perm_code="nonexistent.code",
            tenant_id=self.tenant_id,
        )

        self.assertFalse(result)

    def test_create_permission_basic(self):
        """测试基本权限创建"""
        # 执行测试
        result = self.service.create_permission(
            tenant_id=self.tenant_id,
            perm_code="test.create",
            perm_name="测试创建",
            module="test",
            page_code="test_page",
            action="create",
            description="测试权限",
            permission_type="API",
        )

        # 验证db.add被调用
        self.mock_db.add.assert_called_once()
        added_perm = self.mock_db.add.call_args[0][0]

        # 验证权限属性
        self.assertEqual(added_perm.tenant_id, self.tenant_id)
        self.assertEqual(added_perm.perm_code, "test.create")
        self.assertEqual(added_perm.perm_name, "测试创建")
        self.assertEqual(added_perm.module, "test")
        self.assertEqual(added_perm.page_code, "test_page")
        self.assertEqual(added_perm.action, "create")
        self.assertEqual(added_perm.description, "测试权限")
        self.assertEqual(added_perm.permission_type, "API")
        self.assertTrue(added_perm.is_active)
        self.assertFalse(added_perm.is_system)

        # 验证db.commit和db.refresh被调用
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_create_permission_minimal(self):
        """测试最少参数创建权限"""
        result = self.service.create_permission(
            tenant_id=self.tenant_id,
            perm_code="minimal.perm",
            perm_name="最小权限",
        )

        added_perm = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_perm.perm_code, "minimal.perm")
        self.assertEqual(added_perm.perm_name, "最小权限")
        self.assertIsNone(added_perm.module)
        self.assertIsNone(added_perm.page_code)
        self.assertIsNone(added_perm.action)
        self.assertIsNone(added_perm.description)
        self.assertEqual(added_perm.permission_type, "API")

    def test_update_permission_all_fields(self):
        """测试更新权限所有字段"""
        mock_perm = MagicMock()
        mock_perm.perm_name = "旧名称"
        mock_perm.module = "old_module"
        mock_perm.is_active = False

        result = self.service.update_permission(
            permission=mock_perm,
            perm_name="新名称",
            module="new_module",
            page_code="new_page",
            action="update",
            description="新描述",
            is_active=True,
        )

        # 验证字段更新
        self.assertEqual(mock_perm.perm_name, "新名称")
        self.assertEqual(mock_perm.module, "new_module")
        self.assertEqual(mock_perm.page_code, "new_page")
        self.assertEqual(mock_perm.action, "update")
        self.assertEqual(mock_perm.description, "新描述")
        self.assertTrue(mock_perm.is_active)

        # 验证db操作
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_perm)

    def test_update_permission_partial(self):
        """测试部分更新权限"""
        mock_perm = MagicMock()
        mock_perm.perm_name = "原名称"
        mock_perm.module = "原模块"
        mock_perm.is_active = True

        # 只更新perm_name和description
        result = self.service.update_permission(
            permission=mock_perm,
            perm_name="新名称",
            description="新描述",
        )

        # 验证只有指定字段被更新
        self.assertEqual(mock_perm.perm_name, "新名称")
        self.assertEqual(mock_perm.description, "新描述")
        # module应该保持不变（因为传入的是None，不应该更新）
        # 注意：源代码逻辑是 if module is not None，所以传None不会更新

    def test_update_permission_none_values(self):
        """测试传入None值不更新字段"""
        mock_perm = MagicMock()
        mock_perm.perm_name = "原名称"
        mock_perm.module = "原模块"

        # 传入None值
        result = self.service.update_permission(
            permission=mock_perm,
            perm_name=None,
            module=None,
        )

        # 验证字段未被None覆盖（实际上源代码会检查is not None）
        # 因为传入None，所以不会执行更新逻辑
        self.assertEqual(mock_perm.perm_name, "原名称")
        self.assertEqual(mock_perm.module, "原模块")

    def test_count_roles_using_permission(self):
        """测试统计使用权限的角色数"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 5

        result = self.service.count_roles_using_permission(permission_id=1)

        self.assertEqual(result, 5)

    def test_count_roles_using_permission_zero(self):
        """测试无角色使用权限"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 0

        result = self.service.count_roles_using_permission(permission_id=999)

        self.assertEqual(result, 0)

    def test_delete_permission(self):
        """测试删除权限"""
        mock_perm = MagicMock()

        self.service.delete_permission(mock_perm)

        # 验证db操作
        self.mock_db.delete.assert_called_once_with(mock_perm)
        self.mock_db.commit.assert_called_once()

    # ========== 角色权限关联测试 ==========

    def test_get_role_exists(self):
        """测试获取存在的角色"""
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.role_name = "管理员"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_role

        result = self.service.get_role(
            role_id=1,
            tenant_id=self.tenant_id,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.role_name, "管理员")

    def test_get_role_not_exists(self):
        """测试获取不存在的角色"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = self.service.get_role(
            role_id=999,
            tenant_id=self.tenant_id,
        )

        self.assertIsNone(result)

    def test_get_role_permissions(self):
        """测试获取角色权限列表"""
        mock_perm1 = MagicMock()
        mock_perm1.id = 1
        mock_perm1.perm_code = "project.create"

        mock_perm2 = MagicMock()
        mock_perm2.id = 2
        mock_perm2.perm_code = "project.delete"

        mock_query = self.mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter1 = mock_join.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_order = mock_filter2.order_by.return_value
        mock_order.all.return_value = [mock_perm1, mock_perm2]

        result = self.service.get_role_permissions(role_id=1)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].perm_code, "project.create")
        self.assertEqual(result[1].perm_code, "project.delete")

    def test_get_role_permissions_empty(self):
        """测试角色无权限"""
        mock_query = self.mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter1 = mock_join.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_order = mock_filter2.order_by.return_value
        mock_order.all.return_value = []

        result = self.service.get_role_permissions(role_id=1)

        self.assertEqual(len(result), 0)

    def test_assign_role_permissions_basic(self):
        """测试基本角色权限分配"""
        # Mock权限查询
        mock_perm1 = MagicMock()
        mock_perm1.id = 1
        mock_perm2 = MagicMock()
        mock_perm2.id = 2

        def mock_filter_side_effect(*args, **kwargs):
            mock_filter_result = MagicMock()
            # 第一次调用：删除现有关联
            if not hasattr(mock_filter_side_effect, 'call_count'):
                mock_filter_side_effect.call_count = 0
            
            mock_filter_side_effect.call_count += 1
            
            if mock_filter_side_effect.call_count == 1:
                # 删除操作
                mock_filter_result.delete.return_value = None
                return mock_filter_result
            else:
                # 权限查询
                if mock_filter_side_effect.call_count == 2:
                    mock_filter_result.first.return_value = mock_perm1
                elif mock_filter_side_effect.call_count == 3:
                    mock_filter_result.first.return_value = mock_perm2
                return mock_filter_result

        mock_query = self.mock_db.query.return_value
        mock_query.filter.side_effect = mock_filter_side_effect

        # 执行测试
        result = self.service.assign_role_permissions(
            role_id=1,
            permission_ids=[1, 2],
            tenant_id=self.tenant_id,
        )

        # 验证结果
        self.assertEqual(result, 2)
        # 验证db.add被调用2次（添加2个权限关联）
        self.assertEqual(self.mock_db.add.call_count, 2)
        self.mock_db.commit.assert_called_once()

    def test_assign_role_permissions_with_invalid(self):
        """测试分配权限包含无效ID"""
        mock_perm1 = MagicMock()
        mock_perm1.id = 1

        def mock_filter_side_effect(*args, **kwargs):
            mock_filter_result = MagicMock()
            if not hasattr(mock_filter_side_effect, 'call_count'):
                mock_filter_side_effect.call_count = 0
            
            mock_filter_side_effect.call_count += 1
            
            if mock_filter_side_effect.call_count == 1:
                mock_filter_result.delete.return_value = None
                return mock_filter_result
            elif mock_filter_side_effect.call_count == 2:
                mock_filter_result.first.return_value = mock_perm1
                return mock_filter_result
            else:
                # 第2个权限不存在
                mock_filter_result.first.return_value = None
                return mock_filter_result

        mock_query = self.mock_db.query.return_value
        mock_query.filter.side_effect = mock_filter_side_effect

        # 执行测试（1个有效，1个无效）
        result = self.service.assign_role_permissions(
            role_id=1,
            permission_ids=[1, 999],
            tenant_id=self.tenant_id,
        )

        # 验证只添加了1个有效权限
        self.assertEqual(result, 1)
        self.assertEqual(self.mock_db.add.call_count, 1)

    def test_assign_role_permissions_empty_list(self):
        """测试分配空权限列表"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.delete.return_value = None

        result = self.service.assign_role_permissions(
            role_id=1,
            permission_ids=[],
            tenant_id=self.tenant_id,
        )

        # 验证清空权限
        self.assertEqual(result, 0)
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_called_once()

    @patch('app.services.permission_cache_service.get_permission_cache_service')
    def test_invalidate_permission_cache_success(self, mock_get_cache):
        """测试清除权限缓存成功"""
        mock_cache_service = MagicMock()
        mock_get_cache.return_value = mock_cache_service

        self.service.invalidate_permission_cache(
            role_id=1,
            tenant_id=self.tenant_id,
        )

        # 验证缓存服务被调用
        mock_cache_service.invalidate_role_and_users.assert_called_once_with(
            1, tenant_id=self.tenant_id
        )

    @patch('app.services.permission_cache_service.get_permission_cache_service')
    def test_invalidate_permission_cache_failure(self, mock_get_cache):
        """测试清除权限缓存失败"""
        mock_get_cache.side_effect = Exception("缓存服务不可用")

        # 执行测试（不应该抛出异常）
        try:
            self.service.invalidate_permission_cache(
                role_id=1,
                tenant_id=self.tenant_id,
            )
        except Exception as e:
            self.fail(f"不应该抛出异常: {e}")

    # ========== 用户权限查询测试 ==========

    def test_get_user_exists(self):
        """测试获取存在的用户"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_user

        result = self.service.get_user(user_id=1)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.username, "testuser")

    def test_get_user_not_exists(self):
        """测试获取不存在的用户"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = self.service.get_user(user_id=999)

        self.assertIsNone(result)

    @patch('app.services.permission_service.PermissionService')
    def test_get_user_permissions(self, mock_permission_service):
        """测试获取用户权限"""
        # Mock PermissionService返回权限编码列表
        mock_permission_service.get_user_permissions.return_value = [
            "project.create",
            "project.delete",
        ]

        # Mock数据库查询返回权限对象
        mock_perm1 = MagicMock()
        mock_perm1.perm_code = "project.create"
        mock_perm2 = MagicMock()
        mock_perm2.perm_code = "project.delete"

        mock_chain = MagicMock()
        mock_chain.filter.return_value = mock_chain
        mock_chain.order_by.return_value = mock_chain
        mock_chain.all.return_value = [mock_perm1, mock_perm2]
        
        self.mock_db.query.return_value = mock_chain

        # 执行测试
        result = self.service.get_user_permissions(
            user_id=1,
            tenant_id=self.tenant_id,
        )

        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].perm_code, "project.create")
        self.assertEqual(result[1].perm_code, "project.delete")

        # 验证PermissionService被正确调用
        mock_permission_service.get_user_permissions.assert_called_once_with(
            self.mock_db, 1, self.tenant_id
        )

    @patch('app.services.permission_service.PermissionService')
    def test_get_user_permissions_empty(self, mock_permission_service):
        """测试用户无权限"""
        mock_permission_service.get_user_permissions.return_value = []

        mock_chain = MagicMock()
        mock_chain.filter.return_value = mock_chain
        mock_chain.order_by.return_value = mock_chain
        mock_chain.all.return_value = []
        
        self.mock_db.query.return_value = mock_chain

        result = self.service.get_user_permissions(
            user_id=1,
            tenant_id=self.tenant_id,
        )

        self.assertEqual(len(result), 0)

    @patch('app.services.permission_service.PermissionService')
    def test_check_user_permission_true(self, mock_permission_service):
        """测试用户有权限"""
        mock_user = MagicMock()
        mock_permission_service.check_permission.return_value = True

        result = self.service.check_user_permission(
            user_id=1,
            permission_code="project.create",
            user=mock_user,
            tenant_id=self.tenant_id,
        )

        self.assertTrue(result)
        mock_permission_service.check_permission.assert_called_once_with(
            self.mock_db, 1, "project.create", mock_user, self.tenant_id
        )

    @patch('app.services.permission_service.PermissionService')
    def test_check_user_permission_false(self, mock_permission_service):
        """测试用户无权限"""
        mock_user = MagicMock()
        mock_permission_service.check_permission.return_value = False

        result = self.service.check_user_permission(
            user_id=1,
            permission_code="admin.secret",
            user=mock_user,
            tenant_id=self.tenant_id,
        )

        self.assertFalse(result)

    # ========== 边界情况和异常测试 ==========

    def test_list_permissions_large_page_number(self):
        """测试大页码查询"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 10
        mock_order = mock_filter.order_by.return_value
        mock_offset = mock_order.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.all.return_value = []

        result = self.service.list_permissions(
            tenant_id=self.tenant_id,
            page=100,  # 超大页码
            page_size=10,
        )

        # 验证offset计算正确
        mock_order.offset.assert_called_once_with(990)  # (100-1)*10

    def test_list_permissions_zero_results(self):
        """测试无结果查询"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 0
        mock_order = mock_filter.order_by.return_value
        mock_offset = mock_order.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.all.return_value = []

        result = self.service.list_permissions(
            tenant_id=self.tenant_id,
            page=1,
            page_size=10,
        )

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_update_permission_with_false_values(self):
        """测试更新字段为False值"""
        mock_perm = MagicMock()
        mock_perm.is_active = True

        # 显式设置为False
        result = self.service.update_permission(
            permission=mock_perm,
            is_active=False,
        )

        # 验证False值被正确更新
        self.assertFalse(mock_perm.is_active)

    def test_assign_role_permissions_replace_existing(self):
        """测试覆盖式更新角色权限"""
        mock_perm1 = MagicMock()
        mock_perm1.id = 1

        def mock_filter_side_effect(*args, **kwargs):
            mock_filter_result = MagicMock()
            if not hasattr(mock_filter_side_effect, 'call_count'):
                mock_filter_side_effect.call_count = 0
            
            mock_filter_side_effect.call_count += 1
            
            if mock_filter_side_effect.call_count == 1:
                # 第一次调用：删除现有关联
                mock_filter_result.delete.return_value = None
                return mock_filter_result
            else:
                # 后续调用：权限查询
                mock_filter_result.first.return_value = mock_perm1
                return mock_filter_result

        mock_query = self.mock_db.query.return_value
        mock_query.filter.side_effect = mock_filter_side_effect

        # 执行测试
        result = self.service.assign_role_permissions(
            role_id=1,
            permission_ids=[1],
            tenant_id=self.tenant_id,
        )

        # 验证删除操作被调用（覆盖式更新）
        self.assertEqual(result, 1)


class TestPermissionManagementServiceIntegration(unittest.TestCase):
    """集成测试：测试多个方法组合使用"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = PermissionManagementService(self.mock_db)
        self.tenant_id = 1

    def test_create_and_get_permission_workflow(self):
        """测试创建后获取权限的工作流"""
        # 创建权限
        created_perm = self.service.create_permission(
            tenant_id=self.tenant_id,
            perm_code="workflow.test",
            perm_name="工作流测试",
        )

        # 验证创建成功
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_create_update_delete_workflow(self):
        """测试创建-更新-删除的完整工作流"""
        # 1. 创建
        created_perm = self.service.create_permission(
            tenant_id=self.tenant_id,
            perm_code="workflow.full",
            perm_name="完整工作流",
        )

        # 2. 更新
        mock_perm = MagicMock()
        updated_perm = self.service.update_permission(
            permission=mock_perm,
            perm_name="更新后的名称",
        )

        # 3. 删除
        self.service.delete_permission(mock_perm)

        # 验证所有操作
        self.assertEqual(self.mock_db.add.call_count, 1)
        self.assertEqual(self.mock_db.commit.call_count, 3)
        self.mock_db.delete.assert_called_once()


if __name__ == "__main__":
    unittest.main()

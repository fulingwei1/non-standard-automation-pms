# -*- coding: utf-8 -*-
"""
角色服务单元测试

目标：
1. 只mock外部依赖（db.query, db.execute等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率

测试策略：
- Mock数据库查询和操作
- 让业务逻辑真正执行
- 覆盖主要方法和边界情况
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime
from typing import List, Any

from sqlalchemy.orm import Session
from sqlalchemy.engine import Result, Row

from app.services.role_service import RoleService
from app.models.user import Role
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse


class TestRoleServiceToResponse(unittest.TestCase):
    """测试 _to_response() 方法"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock(spec=Session)
        self.service = RoleService(db=self.mock_db)

    def test_to_response_with_permissions_and_parent(self):
        """测试转换为响应对象（包含权限和父角色）"""
        # 准备测试数据
        role = Role(
            id=1,
            role_code="ADMIN",
            role_name="管理员",
            description="系统管理员角色",
            data_scope="ALL",
            parent_id=2,
            is_system=True,
            is_active=True,
            sort_order=10,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 12, 0, 0),
        )

        parent_role = Role(
            id=2,
            role_code="SUPER_ADMIN",
            role_name="超级管理员",
        )

        # Mock权限查询结果
        perm_result = MagicMock(spec=Result)
        perm_rows = [
            ("user:create",),
            ("user:edit",),
            ("user:delete",),
        ]
        perm_result.fetchall.return_value = perm_rows

        # Mock父角色查询
        parent_query = MagicMock()
        parent_filter = MagicMock()
        parent_query.filter.return_value = parent_filter
        parent_filter.first.return_value = parent_role

        self.mock_db.execute.return_value = perm_result
        self.mock_db.query.return_value = parent_query

        # 执行测试
        response = self.service._to_response(role)

        # 验证结果
        self.assertIsInstance(response, RoleResponse)
        self.assertEqual(response.id, 1)
        self.assertEqual(response.role_code, "ADMIN")
        self.assertEqual(response.role_name, "管理员")
        self.assertEqual(response.description, "系统管理员角色")
        self.assertEqual(response.data_scope, "ALL")
        self.assertEqual(response.parent_id, 2)
        self.assertEqual(response.parent_name, "超级管理员")
        self.assertTrue(response.is_system)
        self.assertTrue(response.is_active)
        self.assertEqual(response.sort_order, 10)
        self.assertEqual(len(response.permissions), 3)
        self.assertIn("user:create", response.permissions)
        self.assertIn("user:edit", response.permissions)
        self.assertIn("user:delete", response.permissions)
        self.assertEqual(response.permission_count, 3)

    def test_to_response_without_permissions(self):
        """测试转换为响应对象（无权限）"""
        role = Role(
            id=3,
            role_code="VIEWER",
            role_name="访客",
            description="只读权限",
            data_scope="OWN",
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=0,
            created_at=datetime(2024, 2, 1, 10, 0, 0),
            updated_at=None,
        )

        # Mock空权限查询结果
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []

        # Mock父角色查询（无父角色）
        parent_query = MagicMock()
        self.mock_db.execute.return_value = perm_result
        self.mock_db.query.return_value = parent_query

        # 执行测试
        response = self.service._to_response(role)

        # 验证结果
        self.assertEqual(response.id, 3)
        self.assertEqual(response.role_code, "VIEWER")
        self.assertEqual(response.role_name, "访客")
        self.assertIsNone(response.parent_id)
        self.assertIsNone(response.parent_name)
        self.assertFalse(response.is_system)
        self.assertTrue(response.is_active)
        self.assertEqual(len(response.permissions), 0)
        self.assertEqual(response.permission_count, 0)
        self.assertIsNone(response.updated_at)

    def test_to_response_without_parent(self):
        """测试转换为响应对象（无父角色）"""
        role = Role(
            id=5,
            role_code="OPERATOR",
            role_name="操作员",
            description="操作员角色",
            data_scope="DEPARTMENT",
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=5,
            created_at=datetime(2024, 3, 1, 10, 0, 0),
            updated_at=datetime(2024, 3, 10, 12, 0, 0),
        )

        # Mock权限查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = [("task:view",)]

        self.mock_db.execute.return_value = perm_result

        # 执行测试
        response = self.service._to_response(role)

        # 验证结果
        self.assertIsNone(response.parent_id)
        self.assertIsNone(response.parent_name)
        self.assertEqual(len(response.permissions), 1)
        self.assertEqual(response.permissions[0], "task:view")

    def test_to_response_with_parent_not_found(self):
        """测试转换为响应对象（父角色ID存在但查询不到）"""
        role = Role(
            id=6,
            role_code="TEMP",
            role_name="临时角色",
            description="临时角色",
            data_scope="OWN",
            parent_id=999,  # 不存在的父角色ID
            is_system=False,
            is_active=True,
            sort_order=0,
            created_at=datetime(2024, 4, 1, 10, 0, 0),
            updated_at=None,
        )

        # Mock权限查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []

        # Mock父角色查询（查不到）
        parent_query = MagicMock()
        parent_filter = MagicMock()
        parent_query.filter.return_value = parent_filter
        parent_filter.first.return_value = None

        self.mock_db.execute.return_value = perm_result
        self.mock_db.query.return_value = parent_query

        # 执行测试
        response = self.service._to_response(role)

        # 验证结果
        self.assertEqual(response.parent_id, 999)
        self.assertIsNone(response.parent_name)  # 父角色名称应为None

    def test_to_response_with_empty_permission_rows(self):
        """测试权限查询结果包含空行的情况"""
        role = Role(
            id=7,
            role_code="TEST",
            role_name="测试角色",
            description=None,
            data_scope="OWN",
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=0,
            created_at=datetime(2024, 5, 1, 10, 0, 0),
            updated_at=None,
        )

        # Mock权限查询结果包含空行和None
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = [
            ("valid:perm",),
            (None,),  # None值应被过滤
            (),  # 空行应被过滤
            ("",),  # 空字符串应被过滤
            ("another:perm",),
        ]

        self.mock_db.execute.return_value = perm_result

        # 执行测试
        response = self.service._to_response(role)

        # 验证结果 - 只应包含有效权限
        self.assertEqual(len(response.permissions), 2)
        self.assertIn("valid:perm", response.permissions)
        self.assertIn("another:perm", response.permissions)

    def test_to_response_with_default_values(self):
        """测试使用默认值的情况"""
        role = Role(
            id=8,
            role_code="DEFAULT",  # 提供有效值
            role_name="默认角色",  # 提供有效值
            description=None,
            data_scope=None,  # 应使用默认值"OWN"
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=0,  # 提供有效的整数值
            created_at=datetime(2024, 6, 1, 10, 0, 0),
            updated_at=None,
        )

        # Mock权限查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []

        self.mock_db.execute.return_value = perm_result

        # 执行测试
        response = self.service._to_response(role)

        # 验证结果
        self.assertEqual(response.role_code, "DEFAULT")
        self.assertEqual(response.role_name, "默认角色")
        self.assertEqual(response.data_scope, "OWN")
        self.assertFalse(response.is_system)
        self.assertTrue(response.is_active)
        self.assertEqual(response.sort_order, 0)
        self.assertIsNone(response.updated_at)


class TestRoleServiceListRoles(unittest.TestCase):
    """测试 list_roles() 方法"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock(spec=Session)
        self.service = RoleService(db=self.mock_db)

    @patch.object(RoleService, 'list')
    def test_list_roles_basic(self, mock_list):
        """测试基本列表功能"""
        # 准备测试数据
        role1 = Role(
            id=1,
            role_code="ADMIN",
            role_name="管理员",
            description="管理员",
            data_scope="ALL",
            parent_id=None,
            is_system=True,
            is_active=True,
            sort_order=10,
            created_at=datetime(2024, 1, 1),
            updated_at=None,
        )
        role2 = Role(
            id=2,
            role_code="USER",
            role_name="普通用户",
            description="普通用户",
            data_scope="OWN",
            parent_id=1,
            is_system=False,
            is_active=True,
            sort_order=20,
            created_at=datetime(2024, 1, 2),
            updated_at=None,
        )

        # Mock list方法返回
        mock_result = MagicMock()
        mock_result.items = [role1, role2]
        mock_result.total = 2
        mock_result.page = 1
        mock_result.page_size = 20
        mock_list.return_value = mock_result

        # Mock权限查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = [
            (1, "user:create"),
            (1, "user:edit"),
            (2, "task:view"),
        ]

        # Mock父角色查询
        parent_mock = MagicMock()
        parent_mock.id = 1
        parent_mock.role_name = "管理员"
        
        parent_query = MagicMock()
        parent_filter = MagicMock()
        parent_query.filter.return_value = parent_filter
        parent_filter.all.return_value = [parent_mock]

        self.mock_db.execute.return_value = perm_result
        self.mock_db.query.return_value = parent_query

        # 执行测试
        result = self.service.list_roles(page=1, page_size=20)

        # 验证结果
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 20)
        self.assertEqual(result["pages"], 1)
        self.assertEqual(len(result["items"]), 2)

        # 验证第一个角色
        item1 = result["items"][0]
        self.assertIsInstance(item1, RoleResponse)
        self.assertEqual(item1.id, 1)
        self.assertEqual(item1.role_code, "ADMIN")
        self.assertEqual(item1.role_name, "管理员")
        self.assertEqual(len(item1.permissions), 2)
        self.assertIn("user:create", item1.permissions)
        self.assertIn("user:edit", item1.permissions)
        self.assertIsNone(item1.parent_name)

        # 验证第二个角色
        item2 = result["items"][1]
        self.assertEqual(item2.id, 2)
        self.assertEqual(item2.role_code, "USER")
        self.assertEqual(len(item2.permissions), 1)
        self.assertEqual(item2.permissions[0], "task:view")
        self.assertEqual(item2.parent_name, "管理员")

    @patch.object(RoleService, 'list')
    def test_list_roles_with_keyword_search(self, mock_list):
        """测试关键词搜索"""
        role = Role(
            id=3,
            role_code="PM",
            role_name="项目经理",
            description="项目经理",
            data_scope="PROJECT",
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=15,
            created_at=datetime(2024, 1, 3),
            updated_at=None,
        )

        mock_result = MagicMock()
        mock_result.items = [role]
        mock_result.total = 1
        mock_result.page = 1
        mock_result.page_size = 20
        mock_list.return_value = mock_result

        # Mock权限和父角色查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []
        self.mock_db.execute.return_value = perm_result

        parent_query = MagicMock()
        parent_query.all.return_value = []
        self.mock_db.query.return_value = parent_query

        # 执行测试
        result = self.service.list_roles(page=1, page_size=20, keyword="项目")

        # 验证list方法被正确调用
        call_args = mock_list.call_args
        params = call_args[0][0]
        self.assertEqual(params.search, "项目")
        self.assertIn("role_code", params.search_fields)
        self.assertIn("role_name", params.search_fields)

    @patch.object(RoleService, 'list')
    def test_list_roles_with_is_active_filter(self, mock_list):
        """测试is_active过滤"""
        role = Role(
            id=4,
            role_code="INACTIVE",
            role_name="已停用",
            description="已停用角色",
            data_scope="OWN",
            parent_id=None,
            is_system=False,
            is_active=False,
            sort_order=0,
            created_at=datetime(2024, 1, 4),
            updated_at=None,
        )

        mock_result = MagicMock()
        mock_result.items = [role]
        mock_result.total = 1
        mock_result.page = 1
        mock_result.page_size = 20
        mock_list.return_value = mock_result

        # Mock权限和父角色查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []
        self.mock_db.execute.return_value = perm_result

        parent_query = MagicMock()
        parent_query.all.return_value = []
        self.mock_db.query.return_value = parent_query

        # 执行测试
        result = self.service.list_roles(page=1, page_size=20, is_active=False)

        # 验证list方法被正确调用
        call_args = mock_list.call_args
        params = call_args[0][0]
        self.assertEqual(params.filters.get("is_active"), False)

    @patch.object(RoleService, 'list')
    def test_list_roles_pagination(self, mock_list):
        """测试分页功能"""
        roles = [
            Role(
                id=i,
                role_code=f"ROLE_{i}",
                role_name=f"角色{i}",
                description=f"角色{i}",
                data_scope="OWN",
                parent_id=None,
                is_system=False,
                is_active=True,
                sort_order=i,
                created_at=datetime(2024, 1, i),
                updated_at=None,
            )
            for i in range(11, 21)  # 第2页，10条记录
        ]

        mock_result = MagicMock()
        mock_result.items = roles
        mock_result.total = 25  # 总共25条
        mock_result.page = 2
        mock_result.page_size = 10
        mock_list.return_value = mock_result

        # Mock权限和父角色查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []
        self.mock_db.execute.return_value = perm_result

        parent_query = MagicMock()
        parent_query.all.return_value = []
        self.mock_db.query.return_value = parent_query

        # 执行测试
        result = self.service.list_roles(page=2, page_size=10)

        # 验证分页结果
        self.assertEqual(result["total"], 25)
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["page_size"], 10)
        self.assertEqual(result["pages"], 3)  # (25 + 10 - 1) // 10 = 3
        self.assertEqual(len(result["items"]), 10)

    @patch.object(RoleService, 'list')
    def test_list_roles_empty_result(self, mock_list):
        """测试空结果"""
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20
        mock_list.return_value = mock_result

        # Mock权限和父角色查询（虽然不会用到）
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []
        self.mock_db.execute.return_value = perm_result

        parent_query = MagicMock()
        parent_query.all.return_value = []
        self.mock_db.query.return_value = parent_query

        # 执行测试
        result = self.service.list_roles(page=1, page_size=20)

        # 验证结果
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["pages"], 0)
        self.assertEqual(len(result["items"]), 0)

    @patch.object(RoleService, 'list')
    def test_list_roles_batch_permissions_loading(self, mock_list):
        """测试批量权限预加载（N+1查询优化）"""
        roles = [
            Role(
                id=i,
                role_code=f"ROLE_{i}",
                role_name=f"角色{i}",
                description=f"角色{i}",
                data_scope="OWN",
                parent_id=None,
                is_system=False,
                is_active=True,
                sort_order=i,
                created_at=datetime(2024, 1, i),
                updated_at=None,
            )
            for i in range(1, 6)
        ]

        mock_result = MagicMock()
        mock_result.items = roles
        mock_result.total = 5
        mock_result.page = 1
        mock_result.page_size = 20
        mock_list.return_value = mock_result

        # Mock批量权限查询（一次性返回所有角色的权限）
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = [
            (1, "perm1"),
            (1, "perm2"),
            (2, "perm3"),
            (3, "perm4"),
            (3, "perm5"),
            (3, "perm6"),
            # 角色4和5没有权限
        ]

        parent_query = MagicMock()
        parent_query.all.return_value = []
        
        self.mock_db.execute.return_value = perm_result
        self.mock_db.query.return_value = parent_query

        # 执行测试
        result = self.service.list_roles(page=1, page_size=20)

        # 验证权限被正确分配
        items = result["items"]
        self.assertEqual(len(items[0].permissions), 2)  # 角色1有2个权限
        self.assertEqual(len(items[1].permissions), 1)  # 角色2有1个权限
        self.assertEqual(len(items[2].permissions), 3)  # 角色3有3个权限
        self.assertEqual(len(items[3].permissions), 0)  # 角色4无权限
        self.assertEqual(len(items[4].permissions), 0)  # 角色5无权限

        # 验证db.execute只被调用一次（批量查询）
        self.assertEqual(self.mock_db.execute.call_count, 1)

    @patch.object(RoleService, 'list')
    def test_list_roles_batch_parent_loading(self, mock_list):
        """测试批量父角色预加载（N+1查询优化）"""
        roles = [
            Role(
                id=1,
                role_code="PARENT1",
                role_name="父角色1",
                description="父角色",
                data_scope="ALL",
                parent_id=None,
                is_system=True,
                is_active=True,
                sort_order=1,
                created_at=datetime(2024, 1, 1),
                updated_at=None,
            ),
            Role(
                id=2,
                role_code="CHILD1",
                role_name="子角色1",
                description="子角色",
                data_scope="DEPARTMENT",
                parent_id=1,  # 父角色ID=1
                is_system=False,
                is_active=True,
                sort_order=2,
                created_at=datetime(2024, 1, 2),
                updated_at=None,
            ),
            Role(
                id=3,
                role_code="CHILD2",
                role_name="子角色2",
                description="子角色",
                data_scope="PROJECT",
                parent_id=1,  # 父角色ID=1
                is_system=False,
                is_active=True,
                sort_order=3,
                created_at=datetime(2024, 1, 3),
                updated_at=None,
            ),
        ]

        mock_result = MagicMock()
        mock_result.items = roles
        mock_result.total = 3
        mock_result.page = 1
        mock_result.page_size = 20
        mock_list.return_value = mock_result

        # Mock权限查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []
        self.mock_db.execute.return_value = perm_result

        # Mock批量父角色查询
        parent_mock = MagicMock()
        parent_mock.id = 1
        parent_mock.role_name = "父角色1"
        
        parent_query = MagicMock()
        parent_filter = MagicMock()
        parent_query.filter.return_value = parent_filter
        parent_filter.all.return_value = [parent_mock]
        
        self.mock_db.query.return_value = parent_query

        # 执行测试
        result = self.service.list_roles(page=1, page_size=20)

        # 验证父角色名称被正确设置
        items = result["items"]
        self.assertIsNone(items[0].parent_name)  # 第一个角色无父角色
        self.assertEqual(items[1].parent_name, "父角色1")  # 第二个角色的父角色
        self.assertEqual(items[2].parent_name, "父角色1")  # 第三个角色的父角色

    @patch.object(RoleService, 'list')
    def test_list_roles_combined_filters(self, mock_list):
        """测试组合过滤条件"""
        role = Role(
            id=10,
            role_code="ACTIVE_PM",
            role_name="活跃项目经理",
            description="活跃的项目经理角色",
            data_scope="PROJECT",
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=10,
            created_at=datetime(2024, 1, 10),
            updated_at=None,
        )

        mock_result = MagicMock()
        mock_result.items = [role]
        mock_result.total = 1
        mock_result.page = 1
        mock_result.page_size = 20
        mock_list.return_value = mock_result

        # Mock权限和父角色查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = [(10, "project:manage")]
        self.mock_db.execute.return_value = perm_result

        parent_query = MagicMock()
        parent_query.all.return_value = []
        self.mock_db.query.return_value = parent_query

        # 执行测试（同时使用关键词和is_active过滤）
        result = self.service.list_roles(
            page=1,
            page_size=20,
            keyword="项目",
            is_active=True
        )

        # 验证list方法被正确调用
        call_args = mock_list.call_args
        params = call_args[0][0]
        self.assertEqual(params.search, "项目")
        self.assertEqual(params.filters.get("is_active"), True)
        
        # 验证结果
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0].role_code, "ACTIVE_PM")


class TestRoleServiceIntegration(unittest.TestCase):
    """测试服务的集成场景"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock(spec=Session)
        self.service = RoleService(db=self.mock_db)

    def test_service_initialization(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.model, Role)
        self.assertEqual(self.service.db, self.mock_db)
        self.assertEqual(self.service.response_schema, RoleResponse)
        self.assertEqual(self.service.resource_name, "角色")

    def test_to_response_with_special_characters(self):
        """测试特殊字符处理"""
        role = Role(
            id=100,
            role_code="SPECIAL@#$",
            role_name="特殊<>角色&",
            description="包含\"引号\"和'单引号'",
            data_scope="OWN",
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=0,
            created_at=datetime(2024, 1, 1),
            updated_at=None,
        )

        # Mock权限查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []
        self.mock_db.execute.return_value = perm_result

        # 执行测试
        response = self.service._to_response(role)

        # 验证特殊字符未被转义或修改
        self.assertEqual(response.role_code, "SPECIAL@#$")
        self.assertEqual(response.role_name, "特殊<>角色&")
        self.assertIn("\"引号\"", response.description)
        self.assertIn("'单引号'", response.description)

    def test_to_response_with_long_description(self):
        """测试长描述文本处理"""
        long_desc = "这是一个非常长的描述" * 100
        role = Role(
            id=101,
            role_code="LONG",
            role_name="长描述角色",
            description=long_desc,
            data_scope="OWN",
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=0,
            created_at=datetime(2024, 1, 1),
            updated_at=None,
        )

        # Mock权限查询
        perm_result = MagicMock(spec=Result)
        perm_result.fetchall.return_value = []
        self.mock_db.execute.return_value = perm_result

        # 执行测试
        response = self.service._to_response(role)

        # 验证长描述被正确处理
        self.assertEqual(response.description, long_desc)
        self.assertGreater(len(response.description), 500)


if __name__ == "__main__":
    unittest.main()

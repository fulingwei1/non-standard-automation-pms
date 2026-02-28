# -*- coding: utf-8 -*-
"""
用户工具函数单元测试

参考 test_condition_parser_rewrite.py 的mock策略：
- 只mock外部依赖（db.query, db.add等数据库操作）
- 让业务逻辑真正执行（不要mock业务方法）
- 覆盖主要方法和边界情况
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime

from fastapi import HTTPException

from app.api.v1.endpoints.users.utils import (
    get_role_names,
    get_role_ids,
    build_user_response,
    ensure_employee_unbound,
    prepare_employee_for_new_user,
    replace_user_roles,
    _invalidate_user_cache,
)
from app.schemas.auth import UserCreate


class TestGetRoleFunctions(unittest.TestCase):
    """测试角色获取函数"""

    def test_get_role_names_success(self):
        """测试成功获取角色名称"""
        # 构造mock用户和角色
        mock_role1 = MagicMock()
        mock_role1.role_name = "管理员"
        mock_role2 = MagicMock()
        mock_role2.role_name = "普通用户"

        mock_user_role1 = MagicMock()
        mock_user_role1.role = mock_role1
        mock_user_role2 = MagicMock()
        mock_user_role2.role = mock_role2

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = [mock_user_role1, mock_user_role2]

        result = get_role_names(mock_user)
        self.assertEqual(result, ["管理员", "普通用户"])

    def test_get_role_names_with_lazy_load(self):
        """测试延迟加载的角色"""
        mock_role = MagicMock()
        mock_role.role_name = "测试角色"
        mock_user_role = MagicMock()
        mock_user_role.role = mock_role

        # 模拟SQLAlchemy的lazy加载关系
        mock_roles = MagicMock()
        mock_roles.all.return_value = [mock_user_role]

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = mock_roles

        result = get_role_names(mock_user)
        self.assertEqual(result, ["测试角色"])

    def test_get_role_names_empty(self):
        """测试空角色列表"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = []

        result = get_role_names(mock_user)
        self.assertEqual(result, [])

    def test_get_role_names_with_none_role(self):
        """测试包含None角色的情况"""
        mock_user_role = MagicMock()
        mock_user_role.role = None

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = [mock_user_role]

        result = get_role_names(mock_user)
        self.assertEqual(result, [])

    def test_get_role_names_exception_handling(self):
        """测试异常处理"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = MagicMock(side_effect=Exception("Database error"))

        result = get_role_names(mock_user)
        self.assertEqual(result, [])

    def test_get_role_ids_success(self):
        """测试成功获取角色ID"""
        mock_user_role1 = MagicMock()
        mock_user_role1.role_id = 1
        mock_user_role2 = MagicMock()
        mock_user_role2.role_id = 2

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = [mock_user_role1, mock_user_role2]

        result = get_role_ids(mock_user)
        self.assertEqual(result, [1, 2])

    def test_get_role_ids_with_lazy_load(self):
        """测试延迟加载的角色ID"""
        mock_user_role = MagicMock()
        mock_user_role.role_id = 5

        mock_roles = MagicMock()
        mock_roles.all.return_value = [mock_user_role]

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = mock_roles

        result = get_role_ids(mock_user)
        self.assertEqual(result, [5])

    def test_get_role_ids_empty(self):
        """测试空角色ID列表"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = []

        result = get_role_ids(mock_user)
        self.assertEqual(result, [])

    def test_get_role_ids_with_none(self):
        """测试包含None的role_id"""
        mock_user_role = MagicMock()
        mock_user_role.role_id = None

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = [mock_user_role]

        result = get_role_ids(mock_user)
        self.assertEqual(result, [])

    def test_get_role_ids_exception_handling(self):
        """测试异常处理"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.roles = MagicMock(side_effect=Exception("Database error"))

        result = get_role_ids(mock_user)
        self.assertEqual(result, [])


class TestBuildUserResponse(unittest.TestCase):
    """测试构建用户响应"""

    def test_build_user_response_complete(self):
        """测试完整用户数据响应"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.employee_id = 100
        mock_user.email = "test@example.com"
        mock_user.phone = "13800138000"
        mock_user.real_name = "测试用户"
        mock_user.employee_no = "EMP001"
        mock_user.department = "技术部"
        mock_user.position = "工程师"
        mock_user.avatar = "https://example.com/avatar.jpg"
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_user.last_login_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_user.created_at = datetime(2023, 1, 1, 0, 0, 0)
        mock_user.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        # Mock角色
        mock_user_role = MagicMock()
        mock_user_role.role_id = 1
        mock_user_role.role = MagicMock()
        mock_user_role.role.role_name = "管理员"
        mock_user.roles = [mock_user_role]

        response = build_user_response(mock_user)

        self.assertEqual(response.id, 1)
        self.assertEqual(response.username, "testuser")
        self.assertEqual(response.employee_id, 100)
        self.assertEqual(response.email, "test@example.com")
        self.assertEqual(response.phone, "13800138000")
        self.assertEqual(response.real_name, "测试用户")
        self.assertEqual(response.employee_no, "EMP001")
        self.assertEqual(response.department, "技术部")
        self.assertEqual(response.position, "工程师")
        self.assertEqual(response.avatar, "https://example.com/avatar.jpg")
        self.assertTrue(response.is_active)
        self.assertFalse(response.is_superuser)
        self.assertEqual(response.last_login_at, datetime(2024, 1, 1, 12, 0, 0))
        self.assertEqual(response.roles, ["管理员"])
        self.assertEqual(response.role_ids, [1])

    def test_build_user_response_minimal(self):
        """测试最小用户数据响应"""
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.username = "minuser"
        mock_user.email = None
        mock_user.phone = None
        mock_user.real_name = None
        mock_user.employee_no = None
        mock_user.department = None
        mock_user.position = None
        mock_user.avatar = None
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_user.last_login_at = None
        mock_user.created_at = datetime(2023, 1, 1, 0, 0, 0)
        mock_user.updated_at = datetime(2023, 1, 1, 0, 0, 0)
        mock_user.roles = []
        
        # 模拟没有employee_id属性
        delattr(mock_user, 'employee_id')

        response = build_user_response(mock_user)

        self.assertEqual(response.id, 2)
        self.assertEqual(response.username, "minuser")
        self.assertIsNone(response.employee_id)
        self.assertIsNone(response.email)
        self.assertEqual(response.roles, [])
        self.assertEqual(response.role_ids, [])


class TestEnsureEmployeeUnbound(unittest.TestCase):
    """测试员工绑定检查"""

    def test_ensure_employee_unbound_no_existing(self):
        """测试员工未绑定的情况"""
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        # 不应该抛出异常
        ensure_employee_unbound(mock_db, employee_id=1)

        mock_db.query.assert_called_once()

    def test_ensure_employee_unbound_same_user(self):
        """测试同一用户绑定员工"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.employee_id = 100

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_user

        # 不应该抛出异常（同一用户）
        ensure_employee_unbound(mock_db, employee_id=100, current_user_id=1)

    def test_ensure_employee_unbound_different_user_raises(self):
        """测试员工已被其他用户绑定"""
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.employee_id = 100

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_user

        # 应该抛出HTTPException
        with self.assertRaises(HTTPException) as context:
            ensure_employee_unbound(mock_db, employee_id=100, current_user_id=1)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "该员工已绑定其他账号")


class TestPrepareEmployeeForNewUser(unittest.TestCase):
    """测试准备员工记录"""

    def test_prepare_employee_by_id(self):
        """测试通过员工ID绑定"""
        mock_employee = MagicMock()
        mock_employee.id = 100

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_employee

        # Mock ensure_employee_unbound
        with patch('app.api.v1.endpoints.users.utils.ensure_employee_unbound'):
            user_in = UserCreate(
                username="test",
                password="pass123",
                employee_id=100
            )
            result = prepare_employee_for_new_user(mock_db, user_in)

            self.assertEqual(result, mock_employee)

    def test_prepare_employee_by_id_not_found(self):
        """测试员工ID不存在"""
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        user_in = UserCreate(
            username="test",
            password="pass123",
            employee_id=999
        )

        with self.assertRaises(HTTPException) as context:
            prepare_employee_for_new_user(mock_db, user_in)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "员工不存在")

    def test_prepare_employee_by_no(self):
        """测试通过员工编号绑定"""
        mock_employee = MagicMock()
        mock_employee.id = 100
        mock_employee.employee_code = "EMP001"

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_employee

        with patch('app.api.v1.endpoints.users.utils.ensure_employee_unbound'):
            user_in = UserCreate(
                username="test",
                password="pass123",
                employee_no="EMP001"
            )
            result = prepare_employee_for_new_user(mock_db, user_in)

            self.assertEqual(result, mock_employee)

    @patch('app.api.v1.endpoints.users.utils.generate_employee_code')
    def test_prepare_employee_create_new(self, mock_generate_code):
        """测试创建新员工"""
        mock_generate_code.return_value = "EMP999"

        mock_db = MagicMock()
        # 第一次查询（by employee_id）返回None
        # 第二次查询（by employee_no）也返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None

        user_in = UserCreate(
            username="newuser",
            password="pass123",
            real_name="新用户",
            department="技术部",
            position="工程师",
            phone="13800138000"
        )

        result = prepare_employee_for_new_user(mock_db, user_in)

        # 验证创建了新员工
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

        # 验证员工对象的属性
        created_employee = mock_db.add.call_args[0][0]
        self.assertEqual(created_employee.employee_code, "EMP999")
        self.assertEqual(created_employee.name, "新用户")
        self.assertEqual(created_employee.department, "技术部")
        self.assertEqual(created_employee.role, "工程师")
        self.assertEqual(created_employee.phone, "13800138000")

    @patch('app.api.v1.endpoints.users.utils.generate_employee_code')
    def test_prepare_employee_create_with_employee_no(self, mock_generate_code):
        """测试用指定编号创建新员工"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        user_in = UserCreate(
            username="newuser",
            password="pass123",
            employee_no="CUSTOM001",
            real_name="新用户"
        )

        result = prepare_employee_for_new_user(mock_db, user_in)

        # 应该使用提供的employee_no，不调用generate_employee_code
        mock_generate_code.assert_not_called()

        created_employee = mock_db.add.call_args[0][0]
        self.assertEqual(created_employee.employee_code, "CUSTOM001")


class TestReplaceUserRoles(unittest.TestCase):
    """测试替换用户角色"""

    @patch('app.api.v1.endpoints.users.utils._invalidate_user_cache')
    def test_replace_user_roles_none(self, mock_invalidate):
        """测试role_ids为None时不做任何操作"""
        mock_db = MagicMock()

        replace_user_roles(mock_db, user_id=1, role_ids=None)

        # 不应该查询或删除
        mock_db.query.assert_not_called()
        mock_invalidate.assert_not_called()

    @patch('app.api.v1.endpoints.users.utils._invalidate_user_cache')
    def test_replace_user_roles_empty_list(self, mock_invalidate):
        """测试清空用户角色"""
        # Mock旧角色
        mock_old_role1 = MagicMock()
        mock_old_role1.role_id = 1
        mock_old_role2 = MagicMock()
        mock_old_role2.role_id = 2

        mock_db = MagicMock()
        mock_user_role_query = mock_db.query.return_value
        mock_user_role_filter = mock_user_role_query.filter.return_value
        mock_user_role_filter.all.return_value = [mock_old_role1, mock_old_role2]

        replace_user_roles(mock_db, user_id=1, role_ids=[])

        # 验证删除了旧角色
        mock_user_role_filter.delete.assert_called_once()
        # 验证缓存失效
        mock_invalidate.assert_called_once_with(1, [1, 2], [])

    @patch('app.api.v1.endpoints.users.utils._invalidate_user_cache')
    def test_replace_user_roles_success(self, mock_invalidate):
        """测试成功替换角色"""
        # Mock旧角色
        mock_old_role = MagicMock()
        mock_old_role.role_id = 1

        # Mock新角色
        mock_role1 = MagicMock()
        mock_role1.id = 2
        mock_role2 = MagicMock()
        mock_role2.id = 3

        mock_db = MagicMock()
        
        # 设置查询链
        def query_side_effect(model):
            if model.__name__ == 'UserRole':
                mock_query = MagicMock()
                mock_filter = MagicMock()
                mock_filter.all.return_value = [mock_old_role]
                mock_filter.delete.return_value = None
                mock_query.filter.return_value = mock_filter
                return mock_query
            elif model.__name__ == 'Role':
                mock_query = MagicMock()
                mock_filter = MagicMock()
                mock_filter.all.return_value = [mock_role1, mock_role2]
                mock_query.filter.return_value = mock_filter
                return mock_query

        mock_db.query.side_effect = query_side_effect

        replace_user_roles(mock_db, user_id=1, role_ids=[2, 3])

        # 验证添加了新角色（2次调用）
        self.assertEqual(mock_db.add.call_count, 2)
        # 验证缓存失效
        mock_invalidate.assert_called_once_with(1, [1], [2, 3])

    @patch('app.api.v1.endpoints.users.utils._invalidate_user_cache')
    def test_replace_user_roles_duplicate_ids(self, mock_invalidate):
        """测试去重重复的角色ID"""
        mock_role1 = MagicMock()
        mock_role1.id = 2
        mock_role2 = MagicMock()
        mock_role2.id = 3

        mock_db = MagicMock()
        
        def query_side_effect(model):
            if model.__name__ == 'UserRole':
                mock_query = MagicMock()
                mock_filter = MagicMock()
                mock_filter.all.return_value = []
                mock_filter.delete.return_value = None
                mock_query.filter.return_value = mock_filter
                return mock_query
            elif model.__name__ == 'Role':
                mock_query = MagicMock()
                mock_filter = MagicMock()
                mock_filter.all.return_value = [mock_role1, mock_role2]
                mock_query.filter.return_value = mock_filter
                return mock_query

        mock_db.query.side_effect = query_side_effect

        # 传入重复的ID
        replace_user_roles(mock_db, user_id=1, role_ids=[2, 3, 2, 3])

        # 应该只添加2次（去重后）
        self.assertEqual(mock_db.add.call_count, 2)

    @patch('app.api.v1.endpoints.users.utils._invalidate_user_cache')
    def test_replace_user_roles_role_not_exist(self, mock_invalidate):
        """测试部分角色不存在"""
        mock_role = MagicMock()
        mock_role.id = 2

        mock_db = MagicMock()
        
        def query_side_effect(model):
            if model.__name__ == 'UserRole':
                mock_query = MagicMock()
                mock_filter = MagicMock()
                mock_filter.all.return_value = []
                mock_filter.delete.return_value = None
                mock_query.filter.return_value = mock_filter
                return mock_query
            elif model.__name__ == 'Role':
                mock_query = MagicMock()
                mock_filter = MagicMock()
                # 只返回1个角色，但请求了2个
                mock_filter.all.return_value = [mock_role]
                mock_query.filter.return_value = mock_filter
                return mock_query

        mock_db.query.side_effect = query_side_effect

        with self.assertRaises(HTTPException) as context:
            replace_user_roles(mock_db, user_id=1, role_ids=[2, 999])

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "部分角色不存在")


class TestInvalidateUserCache(unittest.TestCase):
    """测试缓存失效"""

    @patch('app.services.permission_cache_service.get_permission_cache_service')
    def test_invalidate_user_cache_success(self, mock_get_service):
        """测试成功使缓存失效"""
        mock_cache_service = MagicMock()
        mock_get_service.return_value = mock_cache_service

        _invalidate_user_cache(user_id=1, old_role_ids=[1, 2], new_role_ids=[3, 4])

        mock_cache_service.invalidate_user_role_change.assert_called_once_with(1, [1, 2], [3, 4])

    @patch('app.services.permission_cache_service.get_permission_cache_service')
    def test_invalidate_user_cache_exception(self, mock_get_service):
        """测试缓存失效异常不影响主流程"""
        mock_get_service.side_effect = Exception("Cache service error")

        # 不应该抛出异常
        _invalidate_user_cache(user_id=1, old_role_ids=[1], new_role_ids=[2])


if __name__ == "__main__":
    unittest.main()

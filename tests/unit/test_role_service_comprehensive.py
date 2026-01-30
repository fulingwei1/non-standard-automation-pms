# -*- coding: utf-8 -*-
"""
RoleService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- _to_response: 转换响应对象
- list_roles: 获取角色列表
"""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest


class TestRoleServiceInit:
    """测试 RoleService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()

        service = RoleService(mock_db)

        assert service.db == mock_db
        assert service.resource_name == "角色"

    def test_sets_correct_model(self):
        """测试设置正确的模型"""
        from app.services.role_service import RoleService
        from app.models.user import Role

        mock_db = MagicMock()

        service = RoleService(mock_db)

        assert service.model == Role


class TestToResponse:
    """测试 _to_response 方法"""

    def test_converts_role_to_response(self):
        """测试转换角色对象为响应"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()

        # 模拟权限查询结果
        mock_perm_result = MagicMock()
        mock_perm_result.fetchall.return_value = [("project:read",), ("project:write",)]
        mock_db.execute.return_value = mock_perm_result
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = RoleService(mock_db)

        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.role_code = "ADMIN"
        mock_role.role_name = "管理员"
        mock_role.description = "系统管理员角色"
        mock_role.data_scope = "ALL"
        mock_role.parent_id = None
        mock_role.is_system = True
        mock_role.is_active = True
        mock_role.sort_order = 1
        mock_role.created_at = datetime(2024, 1, 1)
        mock_role.updated_at = datetime(2024, 1, 1)

        result = service._to_response(mock_role)

        assert result.id == 1
        assert result.role_code == "ADMIN"
        assert result.role_name == "管理员"
        assert result.data_scope == "ALL"
        assert result.is_system is True
        assert result.is_active is True
        assert result.permission_count == 2
        assert "project:read" in result.permissions

    def test_handles_parent_role(self):
        """测试处理父角色"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()

        # 模拟权限查询结果
        mock_perm_result = MagicMock()
        mock_perm_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_perm_result

        # 模拟父角色
        mock_parent = MagicMock()
        mock_parent.role_name = "父角色"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_parent

        service = RoleService(mock_db)

        mock_role = MagicMock()
        mock_role.id = 2
        mock_role.role_code = "USER"
        mock_role.role_name = "普通用户"
        mock_role.description = "普通用户角色"
        mock_role.data_scope = "OWN"
        mock_role.parent_id = 1
        mock_role.is_system = False
        mock_role.is_active = True
        mock_role.sort_order = 2
        mock_role.created_at = datetime(2024, 1, 1)
        mock_role.updated_at = datetime(2024, 1, 1)

        result = service._to_response(mock_role)

        assert result.parent_id == 1
        assert result.parent_name == "父角色"

    def test_handles_none_values(self):
        """测试处理空值"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()

        # 模拟权限查询结果
        mock_perm_result = MagicMock()
        mock_perm_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_perm_result
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = RoleService(mock_db)

        mock_role = MagicMock()
        mock_role.id = 3
        mock_role.role_code = None
        mock_role.role_name = None
        mock_role.description = None
        mock_role.data_scope = None
        mock_role.parent_id = None
        mock_role.is_system = None
        mock_role.is_active = None
        mock_role.sort_order = None
        mock_role.created_at = datetime(2024, 1, 1)
        mock_role.updated_at = datetime(2024, 1, 1)

        # 模拟 getattr 返回默认值
        delattr(mock_role, 'sort_order')

        result = service._to_response(mock_role)

        assert result.role_code == ""
        assert result.role_name == ""
        assert result.data_scope == "OWN"
        assert result.is_system is False
        assert result.is_active is True


class TestListRoles:
    """测试 list_roles 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()
        service = RoleService(mock_db)

        mock_result = MagicMock()
        mock_result.items = [MagicMock(), MagicMock()]
        mock_result.total = 2
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_roles(page=1, page_size=20)

            assert result['items'] == mock_result.items
            assert result['total'] == 2
            assert result['page'] == 1
            assert result['page_size'] == 20

    def test_filters_by_is_active(self):
        """测试按激活状态过滤"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()
        service = RoleService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_roles(is_active=True)

            mock_list.assert_called_once()
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('is_active') is True

    def test_filters_by_is_active_false(self):
        """测试按非激活状态过滤"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()
        service = RoleService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_roles(is_active=False)

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('is_active') is False

    def test_no_filter_when_is_active_none(self):
        """测试 is_active 为 None 时不过滤"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()
        service = RoleService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_roles(is_active=None)

            call_args = mock_list.call_args[0][0]
            assert 'is_active' not in call_args.filters

    def test_searches_by_keyword(self):
        """测试关键字搜索"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()
        service = RoleService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_roles(keyword="管理员")

            call_args = mock_list.call_args[0][0]
            assert call_args.search == "管理员"
            assert "role_code" in call_args.search_fields
            assert "role_name" in call_args.search_fields

    def test_calculates_pages(self):
        """测试计算总页数"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()
        service = RoleService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 55
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_roles()

            # (55 + 20 - 1) // 20 = 3
            assert result['pages'] == 3

    def test_calculates_pages_exact_division(self):
        """测试精确整除时的页数计算"""
        from app.services.role_service import RoleService

        mock_db = MagicMock()
        service = RoleService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 40
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_roles()

            # (40 + 20 - 1) // 20 = 2
            assert result['pages'] == 2

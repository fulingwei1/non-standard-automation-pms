# -*- coding: utf-8 -*-
"""
PermissionCRUDService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- _to_response: 转换响应对象
- list_permissions: 获取权限列表
"""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest


class TestPermissionCRUDServiceInit:
    """测试 PermissionCRUDService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()

        service = PermissionCRUDService(mock_db)

        assert service.db == mock_db
        assert service.resource_name == "权限"

    def test_sets_correct_model(self):
        """测试设置正确的模型"""
        from app.services.permission_crud_service import PermissionCRUDService
        from app.models.user import ApiPermission

        mock_db = MagicMock()

        service = PermissionCRUDService(mock_db)

        assert service.model == ApiPermission


class TestToResponse:
    """测试 _to_response 方法"""

    def test_converts_permission_to_response(self):
        """测试转换权限为响应对象"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()
        service = PermissionCRUDService(mock_db)

        mock_perm = MagicMock()
        mock_perm.id = 1
        mock_perm.perm_code = "project:read"
        mock_perm.perm_name = "项目读取"
        mock_perm.module = "project"
        mock_perm.action = "read"
        mock_perm.description = "读取项目信息"
        mock_perm.is_active = True
        mock_perm.created_at = datetime(2024, 1, 1)
        mock_perm.updated_at = datetime(2024, 1, 1)

        result = service._to_response(mock_perm)

        assert result.id == 1
        assert result.permission_code == "project:read"
        assert result.permission_name == "项目读取"
        assert result.module == "project"
        assert result.action == "read"
        assert result.description == "读取项目信息"
        assert result.is_active is True
        assert result.resource is None

    def test_handles_none_is_active(self):
        """测试处理 is_active 为 None"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()
        service = PermissionCRUDService(mock_db)

        mock_perm = MagicMock()
        mock_perm.id = 2
        mock_perm.perm_code = "project:write"
        mock_perm.perm_name = "项目写入"
        mock_perm.module = "project"
        mock_perm.action = "write"
        mock_perm.description = None
        mock_perm.is_active = None
        mock_perm.created_at = datetime(2024, 1, 1)
        mock_perm.updated_at = datetime(2024, 1, 1)

        result = service._to_response(mock_perm)

        assert result.is_active is True


class TestListPermissions:
    """测试 list_permissions 方法"""

    def test_returns_all_active_permissions(self):
        """测试返回所有激活权限"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()
        service = PermissionCRUDService(mock_db)

        mock_perm1 = MagicMock()
        mock_perm1.id = 1
        mock_perm1.perm_code = "project:read"
        mock_perm1.perm_name = "项目读取"
        mock_perm1.module = "project"
        mock_perm1.action = "read"
        mock_perm1.description = None
        mock_perm1.is_active = True
        mock_perm1.created_at = datetime(2024, 1, 1)
        mock_perm1.updated_at = datetime(2024, 1, 1)

        mock_perm2 = MagicMock()
        mock_perm2.id = 2
        mock_perm2.perm_code = "project:write"
        mock_perm2.perm_name = "项目写入"
        mock_perm2.module = "project"
        mock_perm2.action = "write"
        mock_perm2.description = None
        mock_perm2.is_active = True
        mock_perm2.created_at = datetime(2024, 1, 1)
        mock_perm2.updated_at = datetime(2024, 1, 1)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_perm1, mock_perm2]
        mock_db.query.return_value = mock_query

        result = service.list_permissions()

        assert len(result) == 2
        assert result[0].permission_code == "project:read"
        assert result[1].permission_code == "project:write"

    def test_filters_by_module(self):
        """测试按模块过滤"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()
        service = PermissionCRUDService(mock_db)

        mock_query = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter2 = MagicMock()
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.list_permissions(module="project")

        mock_query.filter.assert_called_once()

    def test_filters_by_is_active(self):
        """测试按激活状态过滤"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()
        service = PermissionCRUDService(mock_db)

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.list_permissions(is_active=True)

        mock_filter.order_by.assert_called_once()

    def test_returns_empty_list(self):
        """测试返回空列表"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()
        service = PermissionCRUDService(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.list_permissions()

        assert result == []

    def test_orders_by_module_and_perm_code(self):
        """测试按模块和权限码排序"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()
        service = PermissionCRUDService(mock_db)

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.list_permissions()

        mock_filter.order_by.assert_called_once()

    def test_includes_inactive_permissions_when_disabled(self):
        """测试 is_active=False 时包含非激活权限"""
        from app.services.permission_crud_service import PermissionCRUDService

        mock_db = MagicMock()
        service = PermissionCRUDService(mock_db)

        mock_perm = MagicMock()
        mock_perm.id = 1
        mock_perm.perm_code = "old:perm"
        mock_perm.perm_name = "旧权限"
        mock_perm.module = "old"
        mock_perm.action = "perm"
        mock_perm.description = None
        mock_perm.is_active = False
        mock_perm.created_at = datetime(2024, 1, 1)
        mock_perm.updated_at = datetime(2024, 1, 1)

        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = [mock_perm]
        mock_db.query.return_value = mock_query

        result = service.list_permissions(is_active=False)

        # 当 is_active=False 时，不添加 is_active 过滤条件
        assert len(result) == 1

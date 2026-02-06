# -*- coding: utf-8 -*-
"""
Tests for role_service
角色服务测试
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.models.user import Role


@pytest.mark.unit
class TestRoleService:
    """角色服务测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """创建 RoleService 实例"""
        from app.services.role_service import RoleService
        return RoleService(mock_db)

    def test_init(self, mock_db):
        """测试服务初始化"""
        from app.services.role_service import RoleService
        service = RoleService(mock_db)
        assert service.db == mock_db
        assert service.model == Role
        assert service.resource_name == "角色"

    def test_to_response_basic(self, service, mock_db):
        """测试基本响应转换"""
        mock_role = Mock(
            id=1,
            role_code="ADMIN",
            role_name="管理员",
            description="系统管理员",
            data_scope="ALL",
            parent_id=None,
            is_system=True,
            is_active=True,
            sort_order=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Mock permission query
        mock_perm_result = Mock()
        mock_perm_result.fetchall.return_value = [("user:read",), ("user:write",)]
        mock_db.execute.return_value = mock_perm_result

        result = service._to_response(mock_role)

        assert result.id == 1
        assert result.role_code == "ADMIN"
        assert result.role_name == "管理员"
        assert result.is_system is True
        assert "user:read" in result.permissions
        assert "user:write" in result.permissions
        assert result.permission_count == 2

    def test_to_response_with_parent(self, service, mock_db):
        """测试带父角色的响应转换"""
        mock_parent = Mock(id=1, role_name="父角色")
        mock_role = Mock(
            id=2,
            role_code="CHILD",
            role_name="子角色",
            description="子角色描述",
            data_scope="DEPT",
            parent_id=1,
            is_system=False,
            is_active=True,
            sort_order=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Mock permission query
        mock_perm_result = Mock()
        mock_perm_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_perm_result

        # Mock parent query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_parent

        result = service._to_response(mock_role)

        assert result.parent_id == 1
        assert result.parent_name == "父角色"

    def test_to_response_no_permissions(self, service, mock_db):
        """测试无权限的响应转换"""
        mock_role = Mock(
            id=1,
            role_code="BASIC",
            role_name="基础角色",
            description=None,
            data_scope="OWN",
            parent_id=None,
            is_system=False,
            is_active=True,
            sort_order=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        mock_perm_result = Mock()
        mock_perm_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_perm_result

        result = service._to_response(mock_role)

        assert result.permissions == []
        assert result.permission_count == 0

    def test_list_roles_basic(self, service, mock_db):
        """测试基本角色列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 0
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_roles()

            assert result["total"] == 0
            assert result["page"] == 1
            assert result["page_size"] == 20
            mock_list.assert_called_once()

    def test_list_roles_with_keyword(self, service, mock_db):
        """测试带关键词的角色列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 5
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_roles(keyword="admin")

            assert result["total"] == 5
            call_args = mock_list.call_args[0][0]
            assert call_args.search == "admin"
            assert "role_code" in call_args.search_fields
            assert "role_name" in call_args.search_fields

    def test_list_roles_with_is_active_filter(self, service, mock_db):
        """测试带激活状态过滤的角色列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 3
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_roles(is_active=True)

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get("is_active") is True

    def test_list_roles_pagination(self, service, mock_db):
        """测试角色列表分页"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 45
            mock_result.page = 2
            mock_result.page_size = 10
            mock_list.return_value = mock_result

            result = service.list_roles(page=2, page_size=10)

            assert result["page"] == 2
            assert result["page_size"] == 10
            assert result["total"] == 45
            assert result["pages"] == 5  # (45 + 10 - 1) // 10 = 5

    def test_list_roles_pages_calculation(self, service, mock_db):
        """测试页数计算"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 21
            mock_result.page = 1
            mock_result.page_size = 10
            mock_list.return_value = mock_result

            result = service.list_roles(page=1, page_size=10)

            # (21 + 10 - 1) // 10 = 3
            assert result["pages"] == 3

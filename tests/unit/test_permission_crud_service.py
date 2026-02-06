# -*- coding: utf-8 -*-
"""
Tests for permission_crud_service
Covers: app/services/permission_crud_service.py
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.models.user import ApiPermission
from app.schemas.auth import PermissionResponse


class TestPermissionCRUDServiceInit:
    """Test suite for service initialization."""

    def test_init_service(self):
        from app.services.permission_crud_service import PermissionCRUDService

        mock_session = Mock(spec=Session)
        service = PermissionCRUDService(mock_session)

        assert service.db == mock_session
        assert service.model == ApiPermission
        assert service.resource_name == "权限"


class TestToResponse:
    """Test suite for _to_response method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_to_response_complete_data(self, db_session):
        from app.services.permission_crud_service import PermissionCRUDService

        service = PermissionCRUDService(db_session)

        mock_permission = Mock(spec=ApiPermission)
        mock_permission.id = 1
        mock_permission.perm_code = "project:read"
        mock_permission.perm_name = "查看项目"
        mock_permission.module = "project"
        mock_permission.action = "read"
        mock_permission.description = "允许查看项目信息"
        mock_permission.is_active = True
        mock_permission.created_at = datetime(2025, 1, 1, 10, 0, 0)
        mock_permission.updated_at = datetime(2025, 1, 15, 14, 30, 0)

        result = service._to_response(mock_permission)

        assert isinstance(result, PermissionResponse)
        assert result.id == 1
        assert result.permission_code == "project:read"
        assert result.permission_name == "查看项目"
        assert result.module == "project"
        assert result.resource is None
        assert result.action == "read"
        assert result.description == "允许查看项目信息"
        assert result.is_active is True
        assert result.created_at == datetime(2025, 1, 1, 10, 0, 0)
        assert result.updated_at == datetime(2025, 1, 15, 14, 30, 0)

    def test_to_response_is_active_none(self, db_session):
        from app.services.permission_crud_service import PermissionCRUDService

        service = PermissionCRUDService(db_session)

        mock_permission = Mock(spec=ApiPermission)
        mock_permission.id = 2
        mock_permission.perm_code = "user:manage"
        mock_permission.perm_name = "管理用户"
        mock_permission.module = "user"
        mock_permission.action = "manage"
        mock_permission.description = None
        mock_permission.is_active = None  # None should default to True
        mock_permission.created_at = None
        mock_permission.updated_at = None

        result = service._to_response(mock_permission)

        assert result.is_active is True

    def test_to_response_is_active_false(self, db_session):
        from app.services.permission_crud_service import PermissionCRUDService

        service = PermissionCRUDService(db_session)

        mock_permission = Mock(spec=ApiPermission)
        mock_permission.id = 3
        mock_permission.perm_code = "old:permission"
        mock_permission.perm_name = "旧权限"
        mock_permission.module = "legacy"
        mock_permission.action = "view"
        mock_permission.description = "已禁用"
        mock_permission.is_active = False
        mock_permission.created_at = None
        mock_permission.updated_at = None

        result = service._to_response(mock_permission)

        assert result.is_active is False


class TestListPermissions:
    """Test suite for list_permissions method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_list_all_active_permissions(self, db_session):
        from app.services.permission_crud_service import PermissionCRUDService

        service = PermissionCRUDService(db_session)

        class MockPermission1:
            id = 1
            perm_code = "project:read"
            perm_name = "查看项目"
            module = "project"
            action = "read"
            description = "查看项目"
            is_active = True
            created_at = None
            updated_at = None

        class MockPermission2:
            id = 2
            perm_code = "project:write"
            perm_name = "编辑项目"
            module = "project"
            action = "write"
            description = "编辑项目"
            is_active = True
            created_at = None
            updated_at = None

        mock_permissions = [MockPermission1(), MockPermission2()]

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=mock_permissions)
        db_session.query = Mock(return_value=mock_query)

        result = service.list_permissions()

        assert len(result) == 2
        assert all(isinstance(r, PermissionResponse) for r in result)
        assert result[0].permission_code == "project:read"
        assert result[1].permission_code == "project:write"

    def test_list_permissions_by_module(self, db_session):
        from app.services.permission_crud_service import PermissionCRUDService

        service = PermissionCRUDService(db_session)

        class MockPermission:
            id = 1
            perm_code = "user:read"
            perm_name = "查看用户"
            module = "user"
            action = "read"
            description = None
            is_active = True
            created_at = None
            updated_at = None

        mock_permissions = [MockPermission()]

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=mock_permissions)
        db_session.query = Mock(return_value=mock_query)

        result = service.list_permissions(module="user")

        assert len(result) == 1
        assert result[0].module == "user"
        # Verify filter was called twice (module + is_active)
        assert mock_query.filter.call_count == 2

    def test_list_permissions_include_inactive(self, db_session):
        from app.services.permission_crud_service import PermissionCRUDService

        service = PermissionCRUDService(db_session)

        class MockPermission:
            id = 1
            perm_code = "legacy:view"
            perm_name = "旧权限"
            module = "legacy"
            action = "view"
            description = None
            is_active = False
            created_at = None
            updated_at = None

        mock_permissions = [MockPermission()]

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=mock_permissions)
        db_session.query = Mock(return_value=mock_query)

        result = service.list_permissions(is_active=False)

        assert len(result) == 1
        # Verify filter was NOT called for is_active when is_active=False
        assert mock_query.filter.call_count == 0

    def test_list_permissions_empty_result(self, db_session):
        from app.services.permission_crud_service import PermissionCRUDService

        service = PermissionCRUDService(db_session)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        db_session.query = Mock(return_value=mock_query)

        result = service.list_permissions(module="nonexistent")

        assert result == []

    def test_list_permissions_with_module_and_active(self, db_session):
        from app.services.permission_crud_service import PermissionCRUDService

        service = PermissionCRUDService(db_session)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        db_session.query = Mock(return_value=mock_query)

        service.list_permissions(module="project", is_active=True)

        # Both filters should be applied
        assert mock_query.filter.call_count == 2

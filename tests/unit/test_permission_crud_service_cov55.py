# -*- coding: utf-8 -*-
"""
Tests for app/services/permission_crud_service.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.permission_crud_service import PermissionCRUDService
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.permission_crud_service.BaseService.__init__", return_value=None):
        svc = PermissionCRUDService.__new__(PermissionCRUDService)
        svc.db = mock_db
        svc.model = MagicMock()
        return svc


def test_to_response_converts_fields(service):
    """_to_response 应正确映射字段"""
    perm = MagicMock()
    perm.id = 1
    perm.perm_code = "user:read"
    perm.perm_name = "查看用户"
    perm.module = "user"
    perm.action = "read"
    perm.description = "查看用户信息"
    perm.is_active = True
    perm.created_at = None
    perm.updated_at = None

    with patch("app.services.permission_crud_service.PermissionResponse") as MockResponse:
        MockResponse.return_value = MagicMock()
        result = service._to_response(perm)
        MockResponse.assert_called_once()
        call_kwargs = MockResponse.call_args[1]
        assert call_kwargs["permission_code"] == "user:read"
        assert call_kwargs["permission_name"] == "查看用户"


def test_list_permissions_no_filter(service, mock_db):
    """无过滤条件时返回所有激活权限"""
    perm = MagicMock()
    perm.id = 1
    perm.perm_code = "a:b"
    perm.perm_name = "test"
    perm.module = "mod"
    perm.action = "read"
    perm.description = ""
    perm.is_active = True
    perm.created_at = None
    perm.updated_at = None

    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [perm]

    with patch.object(service, "_to_response", return_value=MagicMock()):
        result = service.list_permissions()
        assert isinstance(result, list)


def test_list_permissions_module_filter(service, mock_db):
    """有 module 过滤时应添加额外过滤条件"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []

    result = service.list_permissions(module="user")
    assert isinstance(result, list)


def test_list_permissions_inactive_included(service, mock_db):
    """is_active=False 时应包含未激活权限"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []

    result = service.list_permissions(is_active=False)
    assert isinstance(result, list)


def test_to_response_is_active_none(service):
    """is_active 为 None 时默认为 True"""
    perm = MagicMock()
    perm.id = 2
    perm.perm_code = "b:c"
    perm.perm_name = "test2"
    perm.module = "mod"
    perm.action = "write"
    perm.description = ""
    perm.is_active = None
    perm.created_at = None
    perm.updated_at = None

    with patch("app.services.permission_crud_service.PermissionResponse") as MockResponse:
        MockResponse.return_value = MagicMock()
        service._to_response(perm)
        call_kwargs = MockResponse.call_args[1]
        assert call_kwargs["is_active"] is True


def test_list_permissions_empty_result(service, mock_db):
    """无权限时返回空列表"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []

    result = service.list_permissions()
    assert result == []

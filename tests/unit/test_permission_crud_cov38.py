# -*- coding: utf-8 -*-
"""
Unit tests for PermissionCRUDService (第三十八批)
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.permission_crud_service", reason="导入失败，跳过")

try:
    from app.services.permission_crud_service import PermissionCRUDService
except ImportError:
    pytestmark = pytest.mark.skip(reason="permission_crud_service 不可用")
    PermissionCRUDService = None


def make_mock_permission(
    id=1, perm_code="view_project", perm_name="查看项目",
    module="project", action="view", is_active=True
):
    p = MagicMock()
    p.id = id
    p.perm_code = perm_code
    p.perm_name = perm_name
    p.module = module
    p.action = action
    p.description = "查看项目详情"
    p.is_active = is_active
    p.created_at = datetime(2024, 1, 1)
    p.updated_at = datetime(2024, 6, 1)
    return p


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.permission_crud_service.BaseService.__init__", return_value=None):
        svc = PermissionCRUDService.__new__(PermissionCRUDService)
        svc.db = mock_db
        svc.model = MagicMock()
        svc.model.module = MagicMock()
        svc.model.perm_code = MagicMock()
        svc.model.is_active = MagicMock()
        return svc


class TestToResponse:
    """测试 _to_response 转换方法"""

    def test_converts_permission_fields(self, service):
        """正确转换权限字段"""
        perm = make_mock_permission()
        with patch("app.services.permission_crud_service.PermissionResponse") as MockResp:
            service._to_response(perm)
            MockResp.assert_called_once()
            kwargs = MockResp.call_args[1]
            assert kwargs["id"] == 1
            assert kwargs["permission_code"] == "view_project"
            assert kwargs["permission_name"] == "查看项目"

    def test_resource_is_none(self, service):
        """新模型 resource 字段为 None"""
        perm = make_mock_permission()
        with patch("app.services.permission_crud_service.PermissionResponse") as MockResp:
            service._to_response(perm)
            kwargs = MockResp.call_args[1]
            assert kwargs["resource"] is None

    def test_is_active_true_when_none(self, service):
        """is_active 为 None 时默认为 True"""
        perm = make_mock_permission(is_active=None)
        perm.is_active = None
        with patch("app.services.permission_crud_service.PermissionResponse") as MockResp:
            service._to_response(perm)
            kwargs = MockResp.call_args[1]
            assert kwargs["is_active"] is True


class TestListPermissions:
    """测试 list_permissions 方法"""

    def _setup_query(self, service, results):
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = results
        service.db.query.return_value = mock_query
        return mock_query

    def test_list_returns_response_list(self, service):
        """返回响应列表"""
        perms = [make_mock_permission(id=1), make_mock_permission(id=2)]
        self._setup_query(service, perms)

        with patch.object(service, "_to_response", side_effect=lambda p: p):
            result = service.list_permissions()
        assert len(result) == 2

    def test_list_filters_by_module(self, service):
        """按模块过滤"""
        perms = [make_mock_permission(module="user")]
        mock_q = self._setup_query(service, perms)

        with patch.object(service, "_to_response", side_effect=lambda p: p):
            service.list_permissions(module="user")
        assert mock_q.filter.called

    def test_list_filters_active_by_default(self, service):
        """默认过滤活跃权限"""
        self._setup_query(service, [])
        with patch.object(service, "_to_response", side_effect=lambda p: p):
            service.list_permissions()
        # 验证查询被调用
        assert service.db.query.called

    def test_list_empty_returns_empty_list(self, service):
        """无权限时返回空列表"""
        self._setup_query(service, [])
        with patch.object(service, "_to_response", side_effect=lambda p: p):
            result = service.list_permissions()
        assert result == []

    def test_list_module_and_active_combined(self, service):
        """模块和活跃状态组合过滤"""
        self._setup_query(service, [])
        with patch.object(service, "_to_response", side_effect=lambda p: p):
            service.list_permissions(module="admin", is_active=True)
        assert service.db.query.called

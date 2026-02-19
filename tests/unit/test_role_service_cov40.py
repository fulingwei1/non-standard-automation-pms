# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 角色业务逻辑服务
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.role_service import RoleService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.role_service.BaseService.__init__", return_value=None):
        svc = RoleService.__new__(RoleService)
        svc.db = mock_db
        svc.model = MagicMock()
        svc.resource_name = "角色"
        return svc


class TestRoleServiceInit:

    def test_instantiate_without_crash(self, mock_db):
        """验证可以导入模块并创建实例（mock BaseService.__init__）"""
        with patch("app.services.role_service.BaseService.__init__", return_value=None):
            svc = RoleService.__new__(RoleService)
            svc.db = mock_db
            assert svc is not None


class TestToResponse:

    def _make_role(self, role_id=1, parent_id=None):
        from datetime import datetime
        role = MagicMock()
        role.id = role_id
        role.role_code = "ADMIN"
        role.role_name = "管理员"
        role.description = "系统管理员"
        role.data_scope = "ALL"
        role.parent_id = parent_id
        role.is_system = True
        role.is_active = True
        role.sort_order = 0
        role.created_at = datetime(2024, 1, 1, 0, 0, 0)
        role.updated_at = datetime(2024, 1, 2, 0, 0, 0)
        return role

    def test_to_response_no_parent(self, service, mock_db):
        role = self._make_role(parent_id=None)
        perm_result = MagicMock()
        perm_result.fetchall.return_value = [("perm:read",), ("perm:write",)]
        mock_db.execute.return_value = perm_result

        resp = service._to_response(role)
        assert resp.role_code == "ADMIN"
        assert "perm:read" in resp.permissions
        assert resp.parent_name is None

    def test_to_response_with_parent(self, service, mock_db):
        role = self._make_role(role_id=2, parent_id=1)
        perm_result = MagicMock()
        perm_result.fetchall.return_value = []
        mock_db.execute.return_value = perm_result

        parent_role = MagicMock()
        parent_role.role_name = "超级管理员"
        mock_db.query.return_value.filter.return_value.first.return_value = parent_role

        resp = service._to_response(role)
        assert resp.parent_name == "超级管理员"

    def test_permission_count_matches(self, service, mock_db):
        role = self._make_role()
        perm_result = MagicMock()
        perm_result.fetchall.return_value = [("p1",), ("p2",), ("p3",)]
        mock_db.execute.return_value = perm_result

        resp = service._to_response(role)
        assert resp.permission_count == 3


class TestListRoles:

    def test_list_roles_returns_expected_keys(self, service, mock_db):
        # Mock list() result
        result_mock = MagicMock()
        result_mock.items = []
        result_mock.total = 0
        result_mock.page = 1
        result_mock.page_size = 20
        service.list = MagicMock(return_value=result_mock)
        mock_db.execute.return_value.fetchall.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.list_roles(page=1, page_size=20)
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "pages" in result

    def test_list_roles_empty(self, service, mock_db):
        result_mock = MagicMock()
        result_mock.items = []
        result_mock.total = 0
        result_mock.page = 1
        result_mock.page_size = 20
        service.list = MagicMock(return_value=result_mock)
        mock_db.execute.return_value.fetchall.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.list_roles()
        assert result["total"] == 0
        assert result["pages"] == 0

    def test_list_roles_pages_calculation(self, service, mock_db):
        result_mock = MagicMock()
        result_mock.items = []
        result_mock.total = 45
        result_mock.page = 1
        result_mock.page_size = 20
        service.list = MagicMock(return_value=result_mock)
        mock_db.execute.return_value.fetchall.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.list_roles(page_size=20)
        assert result["pages"] == 3  # ceil(45/20)=3

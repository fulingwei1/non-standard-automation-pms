# -*- coding: utf-8 -*-
"""权限服务与工时审批分支测试。"""

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.permissions import timesheet as timesheet_module
from app.core.permissions.timesheet import (
    apply_timesheet_access_filter,
    check_timesheet_approval_permission,
    get_user_manageable_dimensions,
    has_timesheet_approval_access,
    is_timesheet_admin,
    require_timesheet_approval_access,
)
from app.models.user import Role, User
from app.services.permission_management.permission_service import PermissionService


_UNSET = object()


def _query(*, first=_UNSET, all_=_UNSET):
    query = MagicMock()
    query.filter.return_value = query
    query.join.return_value = query
    query.order_by.return_value = query
    if first is not _UNSET:
        query.first.return_value = first
    if all_ is not _UNSET:
        query.all.return_value = all_
    return query


class TestPermissionServiceBranches:
    def test_get_user_permissions_uses_users_tenant_when_tenant_id_missing(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(tenant_id=9)

        with patch("app.core.permission_engine.load_permissions", return_value={"project:read"}) as mock_load:
            permissions = PermissionService.get_user_permissions(db, user_id=3)

        assert permissions == ["project:read"]
        mock_load.assert_called_once_with(3, db, 9)

    def test_get_user_effective_roles_includes_position_roles(self):
        user = SimpleNamespace(id=7, tenant_id=8)
        direct_role = Role(id=1, role_code="DIRECT", role_name="Direct", is_active=True, tenant_id=8)
        position_role = Role(id=2, role_code="POSITION", role_name="Position", is_active=True, tenant_id=8)
        assignment = SimpleNamespace(position_id=11)
        user_role = SimpleNamespace(role_id=1)
        position_link = SimpleNamespace(role_id=2)
        db = MagicMock()
        db.query.side_effect = [
            _query(first=user),
            _query(all_=[user_role]),
            _query(first=direct_role),
            _query(all_=[assignment]),
            _query(all_=[position_link]),
            _query(first=position_role),
        ]

        roles = PermissionService.get_user_effective_roles(db, user_id=7)

        assert [role.role_code for role in roles] == ["DIRECT", "POSITION"]

    def test_get_user_effective_roles_falls_back_to_sql_query(self):
        user = SimpleNamespace(id=7, tenant_id=8)
        broken_query = _query()
        broken_query.filter.side_effect = RuntimeError("broken orm query")
        db = MagicMock()
        db.query.side_effect = [_query(first=user), broken_query]
        db.execute.return_value = [
            SimpleNamespace(id=5, role_code="FALLBACK", role_name="Fallback Role")
        ]

        roles = PermissionService.get_user_effective_roles(db, user_id=7)

        assert len(roles) == 1
        assert roles[0].role_code == "FALLBACK"

    def test_get_user_effective_roles_returns_empty_when_fallback_also_fails(self):
        user = SimpleNamespace(id=7, tenant_id=None)
        broken_query = _query()
        broken_query.filter.side_effect = RuntimeError("broken orm query")
        db = MagicMock()
        db.query.side_effect = [_query(first=user), broken_query]
        db.execute.side_effect = RuntimeError("fallback failed")

        assert PermissionService.get_user_effective_roles(db, user_id=7) == []

    def test_check_permission_short_circuits_for_superuser_loaded_from_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
            tenant_id=3, is_superuser=True
        )

        with patch.object(PermissionService, "get_user_permissions") as mock_get_permissions:
            assert PermissionService.check_permission(db, 5, "admin:all") is True

        mock_get_permissions.assert_not_called()

    def test_get_user_menus_returns_empty_without_roles(self):
        with patch.object(PermissionService, "get_user_effective_roles", return_value=[]):
            assert PermissionService.get_user_menus(MagicMock(), user_id=1) == []

    def test_get_user_menus_returns_tree_for_role_menus(self):
        root_menu = SimpleNamespace(
            id=10,
            menu_code="dashboard",
            menu_name="Dashboard",
            menu_path="/dashboard",
            menu_icon="home",
            menu_type="MENU",
            sort_order=1,
        )
        child_menu = SimpleNamespace(
            id=11,
            menu_code="dashboard:detail",
            menu_name="Dashboard Detail",
            menu_path="/dashboard/detail",
            menu_icon="doc",
            menu_type="MENU",
            sort_order=2,
        )
        db = MagicMock()
        db.query.side_effect = [
            _query(all_=[SimpleNamespace(menu_id=10), SimpleNamespace(menu_id=11)]),
            _query(all_=[root_menu]),
            _query(all_=[child_menu]),
            _query(all_=[]),
        ]

        with patch.object(PermissionService, "get_user_effective_roles", return_value=[SimpleNamespace(id=1)]):
            menus = PermissionService.get_user_menus(db, user_id=3)

        assert menus == [
            {
                "id": 10,
                "code": "dashboard",
                "name": "Dashboard",
                "path": "/dashboard",
                "icon": "home",
                "type": "MENU",
                "sort": 1,
                "children": [
                    {
                        "id": 11,
                        "code": "dashboard:detail",
                        "name": "Dashboard Detail",
                        "path": "/dashboard/detail",
                        "icon": "doc",
                        "type": "MENU",
                        "sort": 2,
                    }
                ],
            }
        ]

    def test_get_user_menus_superuser_returns_all_root_menus(self):
        menu = MagicMock()
        menu.to_dict.return_value = {"id": 1, "code": "all"}
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [menu]
        superuser = SimpleNamespace(is_superuser=True)

        assert PermissionService.get_user_menus(db, user_id=1, user=superuser) == [
            {"id": 1, "code": "all"}
        ]

    def test_get_user_data_scopes_prefers_broader_scope(self):
        db = MagicMock()
        db.query.side_effect = [
            _query(
                all_=[
                    SimpleNamespace(resource_type="timesheet", scope_rule_id=1),
                    SimpleNamespace(resource_type="timesheet", scope_rule_id=2),
                ]
            ),
            _query(first=SimpleNamespace(scope_type="OWN")),
            _query(first=SimpleNamespace(scope_type="DEPARTMENT")),
        ]

        with patch.object(
            PermissionService,
            "get_user_effective_roles",
            return_value=[SimpleNamespace(id=1), SimpleNamespace(id=2)],
        ):
            scopes = PermissionService.get_user_data_scopes(db, user_id=5)

        assert scopes == {"timesheet": "DEPARTMENT"}

    def test_get_user_data_scopes_returns_empty_on_exception(self):
        with patch.object(
            PermissionService,
            "get_user_effective_roles",
            side_effect=RuntimeError("boom"),
        ):
            assert PermissionService.get_user_data_scopes(MagicMock(), user_id=5) == {}


class TestTimesheetPermissionBranches:
    def test_is_timesheet_admin_accepts_role_wrappers(self):
        role = SimpleNamespace(role_code="timesheet_admin", role_name="工时管理员")
        user_role = SimpleNamespace(role=role)
        user = SimpleNamespace(is_superuser=False, roles=[user_role])

        assert is_timesheet_admin(user) is True

    def test_get_user_manageable_dimensions_collects_all_dimension_ids(self):
        db = MagicMock()
        db.query.side_effect = [
            _query(all_=[SimpleNamespace(id=1)]),
            _query(all_=[SimpleNamespace(id=2)]),
            _query(all_=[SimpleNamespace(id=3)]),
            _query(all_=[SimpleNamespace(id=4)]),
        ]
        user = SimpleNamespace(id=9, employee_id=99, is_superuser=False, roles=[])

        dims = get_user_manageable_dimensions(db, user)

        assert dims == {
            "is_admin": False,
            "project_ids": {1},
            "rd_project_ids": {2},
            "department_ids": {3},
            "subordinate_user_ids": {4},
        }

    def test_apply_timesheet_access_filter_uses_all_manageable_dimensions(self):
        query = MagicMock()
        query.filter.return_value = query
        current_user = SimpleNamespace(id=7, is_superuser=False, roles=[])
        dims = {
            "is_admin": False,
            "project_ids": {1},
            "rd_project_ids": {2},
            "department_ids": {3},
            "subordinate_user_ids": {4},
        }

        with patch.object(timesheet_module, "get_user_manageable_dimensions", return_value=dims):
            filtered = apply_timesheet_access_filter(query, MagicMock(), current_user)

        assert filtered is query
        query.filter.assert_called_once()

    @pytest.mark.parametrize(
        ("timesheet", "dims"),
        [
            (SimpleNamespace(user_id=2, project_id=None, rd_project_id=5, department_id=None), {"project_ids": set(), "rd_project_ids": {5}, "department_ids": set(), "subordinate_user_ids": set()}),
            (SimpleNamespace(user_id=2, project_id=None, rd_project_id=None, department_id=6), {"project_ids": set(), "rd_project_ids": set(), "department_ids": {6}, "subordinate_user_ids": set()}),
            (SimpleNamespace(user_id=8, project_id=None, rd_project_id=None, department_id=None), {"project_ids": set(), "rd_project_ids": set(), "department_ids": set(), "subordinate_user_ids": {8}}),
        ],
    )
    def test_check_timesheet_approval_permission_allows_manager_paths(self, timesheet, dims):
        current_user = SimpleNamespace(id=1, is_superuser=False, roles=[])

        with patch.object(timesheet_module, "get_user_manageable_dimensions", return_value=dims):
            assert check_timesheet_approval_permission(MagicMock(), timesheet, current_user) is True

    def test_check_timesheet_approval_permission_denies_when_no_dimension_matches(self):
        current_user = SimpleNamespace(id=1, is_superuser=False, roles=[])
        timesheet = SimpleNamespace(user_id=2, project_id=None, rd_project_id=None, department_id=None)
        dims = {
            "project_ids": set(),
            "rd_project_ids": set(),
            "department_ids": set(),
            "subordinate_user_ids": set(),
        }

        with patch.object(timesheet_module, "get_user_manageable_dimensions", return_value=dims):
            assert check_timesheet_approval_permission(MagicMock(), timesheet, current_user) is False

    def test_has_timesheet_approval_access_via_subordinate_and_department(self):
        current_user = SimpleNamespace(id=1, is_superuser=False, roles=[])
        dims = {
            "project_ids": set(),
            "rd_project_ids": set(),
            "department_ids": {9},
            "subordinate_user_ids": {3},
        }
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(department_id=9)

        with patch.object(timesheet_module, "get_user_manageable_dimensions", return_value=dims):
            assert has_timesheet_approval_access(current_user, db, target_user_id=3) is True
            assert has_timesheet_approval_access(current_user, db, target_user_id=4) is True
            assert has_timesheet_approval_access(current_user, db, target_department_id=9) is True

    def test_require_timesheet_approval_access_raises_http_403(self):
        checker = require_timesheet_approval_access()

        with patch.object(timesheet_module, "has_timesheet_approval_access", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(checker(current_user=SimpleNamespace(id=1), db=MagicMock()))

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "您没有工时审批权限"

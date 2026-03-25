# -*- coding: utf-8 -*-
"""
工程师绩效数据范围核心模块单元测试

覆盖:
- resolve_engperf_scope: 超管 / RoleDataScope / 降级 Role.data_scope / fail-closed
- can_access_engineer_data: ALL / OWN / TEAM / DEPARTMENT / fail-closed
- apply_engperf_scope_to_query: ALL / OWN / TEAM / DEPARTMENT / fail-closed
"""
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.permission import ScopeType
from app.services.engineer_performance.engperf_scope import (
    ENGPERF_RESOURCE_TYPE,
    EngPerfScopeContext,
    apply_engperf_scope_to_query,
    can_access_engineer_data,
    resolve_engperf_scope,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id=1, is_superuser=False, roles=None, department_id=10):
    user = MagicMock()
    user.id = user_id
    user.is_superuser = is_superuser
    user.department_id = department_id
    user.roles = roles or []
    return user


def _make_role(data_scope="OWN", is_active=True, role_code="engineer"):
    role = MagicMock()
    role.data_scope = data_scope
    role.is_active = is_active
    role.role_code = role_code
    return role


def _make_user_role(role):
    ur = MagicMock()
    ur.role = role
    return ur


# ---------------------------------------------------------------------------
# resolve_engperf_scope
# ---------------------------------------------------------------------------

class TestResolveEngperfScope:

    def test_superuser_gets_all(self):
        db = MagicMock()
        user = _make_user(is_superuser=True)
        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "ALL"
        assert scope.accessible_dept_ids is None

    @patch("app.services.engineer_performance.engperf_scope.PermissionService")
    def test_role_data_scope_engineer_performance(self, mock_perm_svc):
        """RoleDataScope 配置了 engineer_performance → 使用精细 scope"""
        db = MagicMock()
        user = _make_user(roles=[])
        mock_perm_svc.get_user_data_scopes.return_value = {
            "engineer_performance": "ALL"
        }
        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "ALL"
        assert scope.accessible_dept_ids is None

    @patch("app.services.engineer_performance.engperf_scope.DataScopeServiceEnhanced")
    @patch("app.services.engineer_performance.engperf_scope.PermissionService")
    def test_department_scope_with_org_units(self, mock_perm_svc, mock_ds_svc):
        """DEPARTMENT scope 返回可访问部门 ID"""
        db = MagicMock()
        user = _make_user(roles=[])
        mock_perm_svc.get_user_data_scopes.return_value = {
            "engineer_performance": "DEPARTMENT"
        }
        mock_ds_svc.get_accessible_org_units.return_value = [3, 5, 7]

        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "DEPARTMENT"
        assert scope.accessible_dept_ids == [3, 5, 7]

    @patch("app.services.engineer_performance.engperf_scope.DataScopeServiceEnhanced")
    @patch("app.services.engineer_performance.engperf_scope.PermissionService")
    def test_department_scope_no_org_units_falls_back_to_own(
        self, mock_perm_svc, mock_ds_svc
    ):
        """DEPARTMENT scope 但用户无组织关联 → 降级 OWN"""
        db = MagicMock()
        user = _make_user(roles=[])
        mock_perm_svc.get_user_data_scopes.return_value = {
            "engineer_performance": "DEPARTMENT"
        }
        mock_ds_svc.get_accessible_org_units.return_value = []

        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "OWN"
        assert scope.accessible_dept_ids == []

    @patch("app.services.engineer_performance.engperf_scope._get_dept_ids_for_users")
    @patch("app.services.engineer_performance.engperf_scope.UserScopeService")
    @patch("app.services.engineer_performance.engperf_scope.PermissionService")
    def test_team_scope_with_subordinates(
        self, mock_perm_svc, mock_user_scope_svc, mock_get_depts
    ):
        """TEAM scope → 自己 + 直属下级"""
        db = MagicMock()
        user = _make_user(user_id=10, roles=[])
        mock_perm_svc.get_user_data_scopes.return_value = {
            "engineer_performance": "TEAM"
        }
        mock_user_scope_svc.get_subordinate_ids.return_value = {20, 30}
        mock_get_depts.return_value = [5, 8]

        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "TEAM"
        assert set(scope.accessible_user_ids) == {10, 20, 30}
        assert scope.accessible_dept_ids == [5, 8]

    @patch("app.services.engineer_performance.engperf_scope.UserScopeService")
    @patch("app.services.engineer_performance.engperf_scope.PermissionService")
    def test_team_scope_no_subordinates_falls_back_to_own(
        self, mock_perm_svc, mock_user_scope_svc
    ):
        """TEAM scope 但无下属 → 降级 OWN"""
        db = MagicMock()
        user = _make_user(user_id=10, roles=[])
        mock_perm_svc.get_user_data_scopes.return_value = {
            "engineer_performance": "TEAM"
        }
        mock_user_scope_svc.get_subordinate_ids.return_value = set()

        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "OWN"

    @patch("app.services.engineer_performance.engperf_scope.PermissionService")
    def test_fallback_to_role_data_scope(self, mock_perm_svc):
        """RoleDataScope 没有 engineer_performance → 降级到 Role.data_scope"""
        db = MagicMock()
        role = _make_role(data_scope="ALL")
        user = _make_user(roles=[_make_user_role(role)])
        mock_perm_svc.get_user_data_scopes.return_value = {}

        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "ALL"

    @patch("app.services.engineer_performance.engperf_scope.PermissionService")
    def test_no_role_no_scope_defaults_to_own(self, mock_perm_svc):
        """无角色、无 RoleDataScope → OWN"""
        db = MagicMock()
        user = _make_user(roles=[])
        mock_perm_svc.get_user_data_scopes.return_value = {}

        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "OWN"

    @patch("app.services.engineer_performance.engperf_scope.PermissionService")
    def test_exception_returns_own(self, mock_perm_svc):
        """异常 → fail-closed 返回 OWN"""
        db = MagicMock()
        user = _make_user()
        mock_perm_svc.get_user_data_scopes.side_effect = RuntimeError("db crashed")

        scope = resolve_engperf_scope(db, user)
        assert scope.scope_type == "OWN"
        assert scope.accessible_dept_ids == []


# ---------------------------------------------------------------------------
# can_access_engineer_data
# ---------------------------------------------------------------------------

class TestCanAccessEngineerData:

    def test_all_scope_allows_everything(self):
        scope = EngPerfScopeContext(scope_type="ALL", user_id=1)
        assert can_access_engineer_data(scope, target_user_id=999, target_dept_id=99)

    def test_own_scope_allows_self(self):
        scope = EngPerfScopeContext(scope_type="OWN", user_id=5)
        assert can_access_engineer_data(scope, target_user_id=5)

    def test_own_scope_denies_other(self):
        scope = EngPerfScopeContext(scope_type="OWN", user_id=5)
        assert not can_access_engineer_data(scope, target_user_id=6)

    def test_team_scope_allows_subordinate(self):
        scope = EngPerfScopeContext(
            scope_type="TEAM", user_id=10,
            accessible_user_ids=[10, 20, 30],
        )
        assert can_access_engineer_data(scope, target_user_id=20)

    def test_team_scope_denies_non_subordinate(self):
        scope = EngPerfScopeContext(
            scope_type="TEAM", user_id=10,
            accessible_user_ids=[10, 20, 30],
        )
        assert not can_access_engineer_data(scope, target_user_id=99)

    def test_department_scope_allows_same_dept(self):
        scope = EngPerfScopeContext(
            scope_type="DEPARTMENT", user_id=10,
            accessible_dept_ids=[3, 5, 7],
        )
        assert can_access_engineer_data(scope, target_user_id=99, target_dept_id=5)

    def test_department_scope_denies_other_dept(self):
        scope = EngPerfScopeContext(
            scope_type="DEPARTMENT", user_id=10,
            accessible_dept_ids=[3, 5, 7],
        )
        assert not can_access_engineer_data(scope, target_user_id=99, target_dept_id=100)

    def test_department_scope_null_target_dept_denied(self):
        """target_dept_id=None → 无法匹配 → 拒绝"""
        scope = EngPerfScopeContext(
            scope_type="DEPARTMENT", user_id=10,
            accessible_dept_ids=[3, 5],
        )
        assert not can_access_engineer_data(scope, target_user_id=99, target_dept_id=None)

    def test_empty_dept_ids_denied(self):
        """accessible_dept_ids=[] 且非 ALL/OWN → 拒绝"""
        scope = EngPerfScopeContext(
            scope_type="DEPARTMENT", user_id=10,
            accessible_dept_ids=[],
        )
        assert not can_access_engineer_data(scope, target_user_id=99, target_dept_id=5)


# ---------------------------------------------------------------------------
# apply_engperf_scope_to_query
# ---------------------------------------------------------------------------

class TestApplyEngperfScopeToQuery:

    def test_all_scope_returns_query_unchanged(self):
        query = MagicMock()
        scope = EngPerfScopeContext(scope_type="ALL", user_id=1)
        result = apply_engperf_scope_to_query(query, scope)
        assert result is query
        query.filter.assert_not_called()

    def test_own_scope_filters_by_user_id(self):
        query = MagicMock()
        scope = EngPerfScopeContext(scope_type="OWN", user_id=5)

        col = MagicMock()
        apply_engperf_scope_to_query(query, scope, user_id_column=col)
        query.filter.assert_called_once()

    def test_team_scope_filters_by_user_id_list(self):
        query = MagicMock()
        scope = EngPerfScopeContext(
            scope_type="TEAM", user_id=10,
            accessible_user_ids=[10, 20, 30],
        )

        col = MagicMock()
        apply_engperf_scope_to_query(query, scope, user_id_column=col)
        col.in_.assert_called_once_with([10, 20, 30])

    def test_department_scope_filters_by_dept_ids(self):
        query = MagicMock()
        scope = EngPerfScopeContext(
            scope_type="DEPARTMENT", user_id=10,
            accessible_dept_ids=[3, 5, 7],
        )

        dept_col = MagicMock()
        apply_engperf_scope_to_query(query, scope, dept_id_column=dept_col)
        dept_col.in_.assert_called_once_with([3, 5, 7])

    def test_empty_dept_ids_falls_back_to_user_id(self):
        query = MagicMock()
        scope = EngPerfScopeContext(
            scope_type="DEPARTMENT", user_id=10,
            accessible_dept_ids=[],
        )

        user_col = MagicMock()
        apply_engperf_scope_to_query(query, scope, user_id_column=user_col)
        query.filter.assert_called_once()

    def test_unknown_scope_returns_empty(self):
        """未知 scope → filter(False) → 空结果"""
        query = MagicMock()
        scope = EngPerfScopeContext(
            scope_type="UNKNOWN", user_id=10,
        )
        apply_engperf_scope_to_query(query, scope)
        query.filter.assert_called_once_with(False)


# ---------------------------------------------------------------------------
# EngPerfScopeContext properties
# ---------------------------------------------------------------------------

class TestEngPerfScopeContextProperties:

    def test_is_all(self):
        ctx = EngPerfScopeContext(scope_type="ALL", user_id=1)
        assert ctx.is_all
        assert not ctx.is_own

    def test_is_own(self):
        ctx = EngPerfScopeContext(scope_type="OWN", user_id=1)
        assert ctx.is_own
        assert not ctx.is_all

# -*- coding: utf-8 -*-
"""
数据权限服务增强版单元测试 (I3组)
直接实例化/调用，mock db，确保覆盖率
"""
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

import pytest

from app.models.enums import DataScopeEnum
from app.models.permission import ScopeType
from app.services.data_scope_service_enhanced import (
    DataScopeServiceEnhanced,
    SCOPE_TYPE_MAPPING,
)


# ─────────────────────────────────────────────────────────────────────────────
# 枚举映射
# ─────────────────────────────────────────────────────────────────────────────
class TestScopeTypeMapping:
    def test_all_mappings_exist(self):
        for st_val in [
            ScopeType.ALL.value,
            ScopeType.BUSINESS_UNIT.value,
            ScopeType.DEPARTMENT.value,
            ScopeType.TEAM.value,
            ScopeType.PROJECT.value,
            ScopeType.OWN.value,
        ]:
            assert st_val in SCOPE_TYPE_MAPPING

    def test_normalize_all(self):
        assert DataScopeServiceEnhanced.normalize_scope_type(ScopeType.ALL.value) == DataScopeEnum.ALL.value

    def test_normalize_business_unit(self):
        assert DataScopeServiceEnhanced.normalize_scope_type(ScopeType.BUSINESS_UNIT.value) == DataScopeEnum.DEPT.value

    def test_normalize_department(self):
        assert DataScopeServiceEnhanced.normalize_scope_type(ScopeType.DEPARTMENT.value) == DataScopeEnum.DEPT.value

    def test_normalize_team(self):
        assert DataScopeServiceEnhanced.normalize_scope_type(ScopeType.TEAM.value) == DataScopeEnum.DEPT.value

    def test_normalize_project(self):
        assert DataScopeServiceEnhanced.normalize_scope_type(ScopeType.PROJECT.value) == DataScopeEnum.PROJECT.value

    def test_normalize_own(self):
        assert DataScopeServiceEnhanced.normalize_scope_type(ScopeType.OWN.value) == DataScopeEnum.OWN.value

    def test_normalize_unknown_passthrough(self):
        assert DataScopeServiceEnhanced.normalize_scope_type("UNKNOWN_SCOPE") == "UNKNOWN_SCOPE"


# ─────────────────────────────────────────────────────────────────────────────
# get_user_org_units
# ─────────────────────────────────────────────────────────────────────────────
class TestGetUserOrgUnits:
    def _make_db(self, assignments):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = assignments
        return db

    def test_empty_returns_empty_list(self):
        db = self._make_db([])
        result = DataScopeServiceEnhanced.get_user_org_units(db, user_id=1)
        assert result == []

    def test_single_assignment(self):
        a = MagicMock(); a.org_unit_id = 10
        db = self._make_db([a])
        result = DataScopeServiceEnhanced.get_user_org_units(db, user_id=1)
        assert result == [10]

    def test_multiple_assignments(self):
        a1 = MagicMock(); a1.org_unit_id = 10
        a2 = MagicMock(); a2.org_unit_id = 20
        db = self._make_db([a1, a2])
        result = DataScopeServiceEnhanced.get_user_org_units(db, user_id=5)
        assert set(result) == {10, 20}

    def test_deduplication(self):
        a1 = MagicMock(); a1.org_unit_id = 10
        a2 = MagicMock(); a2.org_unit_id = 10
        db = self._make_db([a1, a2])
        result = DataScopeServiceEnhanced.get_user_org_units(db, user_id=1)
        assert result == [10]

    def test_exception_returns_empty_list(self):
        db = MagicMock()
        db.query.side_effect = Exception("DB error")
        result = DataScopeServiceEnhanced.get_user_org_units(db, user_id=1)
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# get_accessible_org_units
# ─────────────────────────────────────────────────────────────────────────────
class TestGetAccessibleOrgUnits:
    def test_all_scope_returns_all_active_units(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)
        ]
        result = DataScopeServiceEnhanced.get_accessible_org_units(db, 1, ScopeType.ALL.value)
        assert set(result) == {1, 2, 3}

    def test_user_has_no_orgs_returns_empty(self):
        db = MagicMock()
        with patch.object(DataScopeServiceEnhanced, "get_user_org_units", return_value=[]):
            result = DataScopeServiceEnhanced.get_accessible_org_units(db, 1, ScopeType.TEAM.value)
        assert result == []

    def test_team_scope_returns_own_org(self):
        db = MagicMock()
        org = MagicMock(); org.id = 5; org.unit_type = "TEAM"
        db.query.return_value.filter.return_value.first.return_value = org
        with patch.object(DataScopeServiceEnhanced, "get_user_org_units", return_value=[5]):
            result = DataScopeServiceEnhanced.get_accessible_org_units(db, 1, ScopeType.TEAM.value)
        assert 5 in result

    def test_department_scope_with_dept_ancestor(self):
        db = MagicMock()
        org = MagicMock(); org.id = 5; org.unit_type = "DEPARTMENT"
        dept_ancestor = MagicMock(); dept_ancestor.id = 3
        db.query.return_value.filter.return_value.first.return_value = org

        with patch.object(DataScopeServiceEnhanced, "get_user_org_units", return_value=[5]), \
             patch.object(DataScopeServiceEnhanced, "_find_ancestor_by_type", return_value=dept_ancestor), \
             patch.object(DataScopeServiceEnhanced, "_get_subtree_ids_optimized", return_value={3, 4, 5}):
            result = DataScopeServiceEnhanced.get_accessible_org_units(db, 1, ScopeType.DEPARTMENT.value)
        assert 3 in result

    def test_department_scope_no_dept_ancestor_falls_back_to_org(self):
        db = MagicMock()
        org = MagicMock(); org.id = 5; org.unit_type = "TEAM"
        db.query.return_value.filter.return_value.first.return_value = org
        with patch.object(DataScopeServiceEnhanced, "get_user_org_units", return_value=[5]), \
             patch.object(DataScopeServiceEnhanced, "_find_ancestor_by_type", return_value=None):
            result = DataScopeServiceEnhanced.get_accessible_org_units(db, 1, ScopeType.DEPARTMENT.value)
        assert 5 in result

    def test_business_unit_scope_with_bu_ancestor(self):
        db = MagicMock()
        org = MagicMock(); org.id = 5
        bu_ancestor = MagicMock(); bu_ancestor.id = 1
        db.query.return_value.filter.return_value.first.return_value = org
        with patch.object(DataScopeServiceEnhanced, "get_user_org_units", return_value=[5]), \
             patch.object(DataScopeServiceEnhanced, "_find_ancestor_by_type", return_value=bu_ancestor), \
             patch.object(DataScopeServiceEnhanced, "_get_subtree_ids_optimized", return_value={1, 2, 3}):
            result = DataScopeServiceEnhanced.get_accessible_org_units(db, 1, ScopeType.BUSINESS_UNIT.value)
        assert 1 in result

    def test_org_unit_not_found_skipped(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with patch.object(DataScopeServiceEnhanced, "get_user_org_units", return_value=[99]):
            result = DataScopeServiceEnhanced.get_accessible_org_units(db, 1, ScopeType.TEAM.value)
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# _find_ancestor_by_type
# ─────────────────────────────────────────────────────────────────────────────
class TestFindAncestorByType:
    def test_current_is_target_type(self):
        db = MagicMock()
        org = MagicMock(); org.unit_type = "DEPARTMENT"; org.parent_id = None
        result = DataScopeServiceEnhanced._find_ancestor_by_type(db, org, "DEPARTMENT")
        assert result is org

    def test_finds_ancestor_in_chain(self):
        db = MagicMock()
        child = MagicMock(); child.unit_type = "TEAM"; child.parent_id = 10
        parent = MagicMock(); parent.unit_type = "DEPARTMENT"; parent.parent_id = None
        db.query.return_value.filter.return_value.first.return_value = parent
        result = DataScopeServiceEnhanced._find_ancestor_by_type(db, child, "DEPARTMENT")
        assert result is parent

    def test_returns_none_when_not_found(self):
        db = MagicMock()
        org = MagicMock(); org.unit_type = "TEAM"; org.parent_id = None
        result = DataScopeServiceEnhanced._find_ancestor_by_type(db, org, "BUSINESS_UNIT")
        assert result is None

    def test_none_org_unit_returns_none(self):
        db = MagicMock()
        result = DataScopeServiceEnhanced._find_ancestor_by_type(db, None, "DEPARTMENT")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# _get_subtree_ids_optimized
# ─────────────────────────────────────────────────────────────────────────────
class TestGetSubtreeIds:
    def test_optimized_with_path(self):
        db = MagicMock()
        org = MagicMock(); org.id = 1; org.path = "/1/"
        db.query.return_value.filter.return_value.first.return_value = org
        db.query.return_value.filter.return_value.all.return_value = [MagicMock(id=2), MagicMock(id=3)]
        result = DataScopeServiceEnhanced._get_subtree_ids_optimized(db, 1)
        assert 1 in result

    def test_optimized_no_path_falls_back_to_recursive(self):
        db = MagicMock()
        org = MagicMock(); org.id = 1; org.path = None
        db.query.return_value.filter.return_value.first.return_value = org
        with patch.object(DataScopeServiceEnhanced, "_get_subtree_ids_recursive", return_value={1, 2}) as mock_rec:
            result = DataScopeServiceEnhanced._get_subtree_ids_optimized(db, 1)
        mock_rec.assert_called_once_with(db, 1)
        assert 1 in result

    def test_optimized_org_not_found_returns_only_id(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = DataScopeServiceEnhanced._get_subtree_ids_optimized(db, 99)
        assert result == {99}

    def test_optimized_exception_returns_id(self):
        db = MagicMock()
        db.query.side_effect = Exception("DB error")
        result = DataScopeServiceEnhanced._get_subtree_ids_optimized(db, 1)
        assert 1 in result

    def test_recursive_no_children(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = DataScopeServiceEnhanced._get_subtree_ids_recursive(db, 1)
        assert result == {1}

    def test_recursive_with_children(self):
        db = MagicMock()
        child = MagicMock(); child.id = 2
        # First call returns child, second call (for child) returns empty
        db.query.return_value.filter.return_value.all.side_effect = [[child], []]
        result = DataScopeServiceEnhanced._get_subtree_ids_recursive(db, 1)
        assert 1 in result
        assert 2 in result


# ─────────────────────────────────────────────────────────────────────────────
# apply_data_scope
# ─────────────────────────────────────────────────────────────────────────────
class TestApplyDataScope:
    def _make_user(self, is_superuser=False, user_id=1):
        user = MagicMock(); user.id = user_id; user.is_superuser = is_superuser
        return user

    def test_superuser_skips_filter(self):
        db = MagicMock()
        user = self._make_user(is_superuser=True)
        query = MagicMock()
        result = DataScopeServiceEnhanced.apply_data_scope(query, db, user, "project")
        assert result is query
        query.filter.assert_not_called()

    def test_all_scope_returns_unchanged_query(self):
        db = MagicMock()
        user = self._make_user()
        query = MagicMock()
        query.column_descriptions = [{"entity": MagicMock()}]
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.ALL.value}
            result = DataScopeServiceEnhanced.apply_data_scope(query, db, user, "project")
        assert result is query

    def test_own_scope_with_owner_field(self):
        db = MagicMock()
        user = self._make_user(user_id=5)
        model_cls = MagicMock()
        model_cls.created_by = MagicMock()
        query = MagicMock()
        query.column_descriptions = [{"entity": model_cls}]
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.OWN.value}
            with patch("app.services.data_scope_service_enhanced.or_"):
                result = DataScopeServiceEnhanced.apply_data_scope(query, db, user, "project")
        # Should have called query.filter
        assert result is not None

    def test_dept_scope_no_accessible_orgs_returns_false_filter(self):
        db = MagicMock()
        user = self._make_user()
        model_cls = MagicMock()
        query = MagicMock()
        query.column_descriptions = [{"entity": model_cls}]
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps, \
             patch.object(DataScopeServiceEnhanced, "get_accessible_org_units", return_value=[]):
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.DEPARTMENT.value}
            result = DataScopeServiceEnhanced.apply_data_scope(query, db, user, "project")
        query.filter.assert_called()

    def test_exception_returns_empty_result(self):
        db = MagicMock()
        user = self._make_user()
        query = MagicMock()
        query.column_descriptions = [{"entity": MagicMock()}]
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.side_effect = Exception("DB error")
            result = DataScopeServiceEnhanced.apply_data_scope(query, db, user, "project")
        query.filter.assert_called()


# ─────────────────────────────────────────────────────────────────────────────
# can_access_data
# ─────────────────────────────────────────────────────────────────────────────
class TestCanAccessData:
    def test_superuser_always_true(self):
        db = MagicMock()
        user = MagicMock(); user.is_superuser = True
        data = MagicMock()
        assert DataScopeServiceEnhanced.can_access_data(db, user, "project", data) is True

    def test_all_scope_returns_true(self):
        db = MagicMock()
        user = MagicMock(); user.is_superuser = False; user.id = 1
        data = MagicMock()
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.ALL.value}
            result = DataScopeServiceEnhanced.can_access_data(db, user, "project", data)
        assert result is True

    def test_own_scope_owner_match(self):
        db = MagicMock()
        user = MagicMock(); user.is_superuser = False; user.id = 5
        data = MagicMock(spec=[])
        data.created_by = 5
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.OWN.value}
            result = DataScopeServiceEnhanced.can_access_data(db, user, "project", data, owner_field="created_by")
        assert result is True

    def test_own_scope_no_match(self):
        db = MagicMock()
        user = MagicMock(); user.is_superuser = False; user.id = 5
        data = MagicMock(spec=[])
        data.created_by = 99
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.OWN.value}
            result = DataScopeServiceEnhanced.can_access_data(db, user, "project", data, owner_field="created_by")
        assert result is False

    def test_dept_scope_accessible(self):
        db = MagicMock()
        user = MagicMock(); user.is_superuser = False; user.id = 1
        data = MagicMock(); data.org_unit_id = 10
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps, \
             patch.object(DataScopeServiceEnhanced, "get_accessible_org_units", return_value=[10, 20]):
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.DEPARTMENT.value}
            result = DataScopeServiceEnhanced.can_access_data(db, user, "project", data)
        assert result is True

    def test_dept_scope_no_org_field_allows_access(self):
        db = MagicMock()
        user = MagicMock(); user.is_superuser = False; user.id = 1
        data = object()  # no org_unit_id attribute
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps, \
             patch.object(DataScopeServiceEnhanced, "get_accessible_org_units", return_value=[10]):
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.DEPARTMENT.value}
            result = DataScopeServiceEnhanced.can_access_data(db, user, "project", data)
        assert result is True

    def test_exception_returns_false(self):
        db = MagicMock()
        user = MagicMock(); user.is_superuser = False; user.id = 1
        data = MagicMock()
        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.side_effect = Exception("Error")
            result = DataScopeServiceEnhanced.can_access_data(db, user, "project", data)
        assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# Backward compat alias
# ─────────────────────────────────────────────────────────────────────────────
class TestBackwardCompat:
    def test_data_scope_service_alias(self):
        from app.services.data_scope_service_enhanced import DataScopeService
        assert DataScopeService is DataScopeServiceEnhanced

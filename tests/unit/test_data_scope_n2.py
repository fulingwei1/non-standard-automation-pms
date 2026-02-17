# -*- coding: utf-8 -*-
"""
数据权限服务增强版 N2 深度覆盖测试
覆盖: apply_data_scope 的 BUSINESS_UNIT/PROJECT scope,
      can_access_data 的 DEPARTMENT/PROJECT scope,
      _get_subtree_ids_recursive 的多层递归,
      _find_ancestor_by_type 的深度限制
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models.permission import ScopeType
from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced


def make_user(user_id=1, is_superuser=False):
    u = MagicMock()
    u.id = user_id
    u.is_superuser = is_superuser
    return u


# ======================= apply_data_scope BUSINESS_UNIT scope =======================

class TestApplyDataScopeBUScope:
    def test_bu_scope_with_accessible_orgs(self):
        db = MagicMock()
        user = make_user()
        model_cls = MagicMock()
        model_cls.org_unit_id = MagicMock()
        query = MagicMock()
        query.column_descriptions = [{"entity": model_cls}]
        query.filter.return_value = query

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps, \
             patch.object(DataScopeServiceEnhanced, "get_accessible_org_units", return_value=[1, 2, 3]):
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.BUSINESS_UNIT.value}
            result = DataScopeServiceEnhanced.apply_data_scope(
                query, db, user, "project"
            )
        query.filter.assert_called()

    def test_bu_scope_uses_department_id_fallback(self):
        """模型没有 org_unit_id 但有 department_id 时使用 department_id"""
        db = MagicMock()
        user = make_user()
        model_cls = MagicMock(spec=["department_id"])
        model_cls.department_id = MagicMock()
        query = MagicMock()
        query.column_descriptions = [{"entity": model_cls}]
        query.filter.return_value = query

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps, \
             patch.object(DataScopeServiceEnhanced, "get_accessible_org_units", return_value=[1, 2]):
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.BUSINESS_UNIT.value}
            result = DataScopeServiceEnhanced.apply_data_scope(
                query, db, user, "project"
            )
        query.filter.assert_called()


# ======================= apply_data_scope PROJECT scope =======================

class TestApplyDataScopeProjectScope:
    def test_project_scope_with_owner_field(self):
        db = MagicMock()
        user = make_user(user_id=7)
        model_cls = MagicMock()
        model_cls.created_by = MagicMock()
        query = MagicMock()
        query.column_descriptions = [{"entity": model_cls}]
        query.filter.return_value = query

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps, \
             patch("app.services.data_scope_service_enhanced.or_"):
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.PROJECT.value}
            result = DataScopeServiceEnhanced.apply_data_scope(
                query, db, user, "project"
            )
        assert result is not None

    def test_project_scope_with_pm_field(self):
        """提供 pm_field 时也加入过滤"""
        db = MagicMock()
        user = make_user(user_id=3)
        model_cls = MagicMock()
        model_cls.created_by = MagicMock()
        model_cls.pm_id = MagicMock()
        query = MagicMock()
        query.column_descriptions = [{"entity": model_cls}]
        query.filter.return_value = query

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps, \
             patch("app.services.data_scope_service_enhanced.or_"):
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.PROJECT.value}
            result = DataScopeServiceEnhanced.apply_data_scope(
                query, db, user, "project", pm_field="pm_id"
            )
        assert result is not None

    def test_project_scope_no_owner_field_returns_false_filter(self):
        """模型无任何可用字段时返回空结果"""
        db = MagicMock()
        user = make_user()
        model_cls = MagicMock(spec=[])  # no attributes
        query = MagicMock()
        query.column_descriptions = [{"entity": model_cls}]
        query.filter.return_value = query

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.PROJECT.value}
            result = DataScopeServiceEnhanced.apply_data_scope(
                query, db, user, "project"
            )
        query.filter.assert_called()


# ======================= can_access_data PROJECT scope =======================

class TestCanAccessDataProjectScope:
    def test_project_scope_owner_match(self):
        db = MagicMock()
        user = make_user(user_id=5)
        data = MagicMock()
        data.created_by = 5

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.PROJECT.value}
            result = DataScopeServiceEnhanced.can_access_data(
                db, user, "project", data, owner_field="created_by"
            )
        assert result is True

    def test_project_scope_pm_match(self):
        """pm_field 匹配时也允许访问"""
        db = MagicMock()
        user = make_user(user_id=8)
        # data has pm_id=8
        data = MagicMock()
        data.created_by = 99
        data.owner_id = 99
        data.pm_id = 8

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.PROJECT.value}
            # OWN scope checks owner_id and pm_id
            result = DataScopeServiceEnhanced.can_access_data(
                db, user, "project", data, owner_field="created_by"
            )
        # user.id=8 is in [created_by=99, owner_id=99, pm_id=8] → True
        assert result is True

    def test_project_scope_no_match_returns_false(self):
        db = MagicMock()
        user = make_user(user_id=1)
        data = MagicMock()
        data.created_by = 99
        data.owner_id = 99
        data.pm_id = 99

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps:
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.OWN.value}
            result = DataScopeServiceEnhanced.can_access_data(
                db, user, "project", data, owner_field="created_by"
            )
        assert result is False


# ======================= can_access_data DEPARTMENT scope inaccessible =======================

class TestCanAccessDataDeptScopeInaccessible:
    def test_dept_scope_not_accessible(self):
        """数据org_unit_id不在可访问列表中，拒绝访问"""
        db = MagicMock()
        user = make_user(user_id=1)
        data = MagicMock()
        data.org_unit_id = 999

        with patch("app.services.data_scope_service_enhanced.PermissionService") as mock_ps, \
             patch.object(DataScopeServiceEnhanced, "get_accessible_org_units", return_value=[1, 2, 3]):
            mock_ps.get_user_data_scopes.return_value = {"project": ScopeType.DEPARTMENT.value}
            result = DataScopeServiceEnhanced.can_access_data(
                db, user, "project", data
            )
        assert result is False


# ======================= _find_ancestor_by_type 深度限制 =======================

class TestFindAncestorDepthLimit:
    def test_depth_limit_prevents_infinite_loop(self):
        """循环引用的组织树不会导致无限循环"""
        db = MagicMock()

        # Create a mock org that always has a parent_id pointing to itself via DB
        org = MagicMock()
        org.unit_type = "TEAM"
        org.parent_id = 1

        # DB always returns an org with wrong type and parent_id=1
        next_org = MagicMock()
        next_org.unit_type = "TEAM"
        next_org.parent_id = 1
        db.query.return_value.filter.return_value.first.return_value = next_org

        # Should complete without hanging
        result = DataScopeServiceEnhanced._find_ancestor_by_type(db, org, "BUSINESS_UNIT")
        assert result is None  # Not found, depth limit hit


# ======================= _get_subtree_ids_recursive 多层 =======================

class TestSubtreeRecursiveMultiLevel:
    def test_three_level_hierarchy(self):
        db = MagicMock()

        # Level structure: 1 → 2 → 3 → (no children)
        child2 = MagicMock(); child2.id = 2
        child3 = MagicMock(); child3.id = 3

        call_count = [0]
        def all_side():
            call_count[0] += 1
            if call_count[0] == 1:
                return [child2]
            elif call_count[0] == 2:
                return [child3]
            return []

        db.query.return_value.filter.return_value.all.side_effect = lambda: all_side()
        result = DataScopeServiceEnhanced._get_subtree_ids_recursive(db, 1)
        assert 1 in result
        assert 2 in result
        assert 3 in result


# ======================= normalize_scope_type 通过值 =======================

class TestNormalizeScopeTypeEdgeCases:
    def test_empty_string_passthrough(self):
        result = DataScopeServiceEnhanced.normalize_scope_type("")
        assert result == ""

    def test_case_sensitive(self):
        """大小写敏感，未匹配的直接透传"""
        result = DataScopeServiceEnhanced.normalize_scope_type("all")
        assert result == "all"  # lowercase not in mapping

    def test_all_value_mapped(self):
        from app.models.enums import DataScopeEnum
        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.ALL.value)
        assert result == DataScopeEnum.ALL.value

# -*- coding: utf-8 -*-
"""第二十三批：data_scope/generic_filter 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.data_scope.generic_filter")

from app.services.data_scope.generic_filter import GenericFilterService
from app.services.data_scope.config import DataScopeConfig


def _mock_user(is_superuser=False, data_scope="OWN", user_id=1, department="研发部"):
    user = MagicMock()
    user.id = user_id
    user.is_superuser = is_superuser
    user.department = department
    return user


def _mock_db():
    return MagicMock()


class TestFilterByScopeSuperuser:
    def test_superuser_gets_all(self):
        db = _mock_db()
        query = MagicMock()
        model = MagicMock()
        user = _mock_user(is_superuser=True)
        result = GenericFilterService.filter_by_scope(db, query, model, user)
        assert result is query


class TestFilterByScopeOWN:
    def test_own_scope_no_owner_field_returns_false_filter(self):
        db = _mock_db()
        query = MagicMock()
        filtered = MagicMock()
        query.filter.return_value = filtered
        model = MagicMock()
        # No owner_field → filter(False)
        config = DataScopeConfig(owner_field=None)
        with patch("app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope", return_value="OWN"):
            result = GenericFilterService.filter_by_scope(db, query, model, user=_mock_user(), config=config)
        query.filter.assert_called_once()

    def test_own_scope_calls_filter(self):
        """OWN 权限调用了 query.filter"""
        db = _mock_db()
        query = MagicMock()
        query.filter.return_value = MagicMock()
        config = DataScopeConfig(owner_field=None)
        with patch("app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope", return_value="OWN"):
            result = GenericFilterService.filter_by_scope(db, query, MagicMock(), _mock_user(), config)
        assert query.filter.called


class TestFilterByScopeALL:
    def test_all_scope_returns_original_query(self):
        db = _mock_db()
        query = MagicMock()
        model = MagicMock()
        user = _mock_user(is_superuser=False)
        config = DataScopeConfig()
        with patch("app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope", return_value="ALL"):
            result = GenericFilterService.filter_by_scope(db, query, model, user, config)
        assert result is query


class TestFilterByScopeSubordinate:
    def test_subordinate_scope_no_owner_field(self):
        """SUBORDINATE 权限 + 无 owner_field → filter(False)"""
        db = _mock_db()
        query = MagicMock()
        query.filter.return_value = MagicMock()
        config = DataScopeConfig(owner_field=None)
        user = _mock_user(is_superuser=False)
        with patch("app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope", return_value="SUBORDINATE"):
            with patch("app.services.data_scope.generic_filter.UserScopeService.get_subordinate_ids", return_value={2, 3}):
                result = GenericFilterService.filter_by_scope(db, query, MagicMock(), user, config)
        assert query.filter.called


class TestCheckCustomerAccess:
    def test_superuser_always_has_access(self):
        db = _mock_db()
        user = _mock_user(is_superuser=True)
        result = GenericFilterService.check_customer_access(db, user, 99)
        assert result is True

    def test_all_scope_has_access(self):
        db = _mock_db()
        user = _mock_user(is_superuser=False)
        with patch("app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope", return_value="ALL"):
            result = GenericFilterService.check_customer_access(db, user, 99)
        assert result is True

    def test_else_scope_no_projects_no_access(self):
        """非ALL/CUSTOMER权限且没有项目时无访问权限（需要 patch DataScopeEnum）"""
        db = _mock_db()
        user = _mock_user(is_superuser=False)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        # 补丁 DataScopeEnum，添加 CUSTOMER 属性
        from app.models.enums import DataScopeEnum
        with patch.object(DataScopeEnum, "CUSTOMER", create=True, new=MagicMock(value="CUSTOMER_PORTAL")):
            with patch("app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope", return_value="SUBORDINATE"):
                with patch("app.services.data_scope.generic_filter.UserScopeService.get_user_project_ids", return_value=set()):
                    result = GenericFilterService.check_customer_access(db, user, 99)
        assert result is False

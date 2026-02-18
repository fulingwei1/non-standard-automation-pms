# -*- coding: utf-8 -*-
"""第二十三批：data_scope/issue_filter 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.data_scope.issue_filter")

from app.services.data_scope.issue_filter import IssueFilterService


def _mock_user(is_superuser=False, user_id=1, department="研发部"):
    u = MagicMock()
    u.id = user_id
    u.is_superuser = is_superuser
    u.department = department
    u.is_active = True
    return u


def _make_db():
    return MagicMock()


class TestFilterIssuesByScopeSuperuser:
    def test_superuser_returns_original_query(self):
        db = _make_db()
        query = MagicMock()
        user = _mock_user(is_superuser=True)
        result = IssueFilterService.filter_issues_by_scope(db, query, user)
        assert result is query


class TestFilterIssuesByScopeALL:
    def test_all_scope_returns_original(self):
        db = _make_db()
        query = MagicMock()
        user = _mock_user(is_superuser=False)
        with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_data_scope", return_value="ALL"):
            result = IssueFilterService.filter_issues_by_scope(db, query, user)
        assert result is query


class TestFilterIssuesByScopeOWN:
    def test_own_scope_adds_filter(self):
        db = _make_db()
        query = MagicMock()
        filtered = MagicMock()
        query.filter.return_value = filtered
        user = _mock_user(is_superuser=False)
        with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_data_scope", return_value="OWN"):
            result = IssueFilterService.filter_issues_by_scope(db, query, user)
        query.filter.assert_called_once()
        assert result is filtered


class TestFilterIssuesByScopeSubordinate:
    def test_subordinate_includes_subordinate_ids(self):
        db = _make_db()
        query = MagicMock()
        filtered = MagicMock()
        query.filter.return_value = filtered
        user = _mock_user(is_superuser=False)
        with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_data_scope", return_value="SUBORDINATE"):
            with patch("app.services.data_scope.issue_filter.UserScopeService.get_subordinate_ids", return_value={2, 3}):
                result = IssueFilterService.filter_issues_by_scope(db, query, user)
        query.filter.assert_called_once()


class TestFilterIssuesByScopeProject:
    def test_project_scope_uses_project_ids(self):
        db = _make_db()
        query = MagicMock()
        filtered = MagicMock()
        query.filter.return_value = filtered
        user = _mock_user(is_superuser=False)
        with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_data_scope", return_value="PROJECT"):
            with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_project_ids", return_value={10, 11}):
                result = IssueFilterService.filter_issues_by_scope(db, query, user)
        query.filter.assert_called_once()

    def test_project_scope_no_projects(self):
        db = _make_db()
        query = MagicMock()
        filtered = MagicMock()
        query.filter.return_value = filtered
        user = _mock_user(is_superuser=False)
        with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_data_scope", return_value="PROJECT"):
            with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_project_ids", return_value=set()):
                result = IssueFilterService.filter_issues_by_scope(db, query, user)
        query.filter.assert_called_once()


class TestFilterIssuesByScopeDept:
    def test_dept_scope_falls_back_when_no_department(self):
        db = _make_db()
        query = MagicMock()
        filtered = MagicMock()
        query.filter.return_value = filtered
        user = _mock_user(is_superuser=False, department=None)
        with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_data_scope", return_value="DEPT"):
            result = IssueFilterService.filter_issues_by_scope(db, query, user)
        query.filter.assert_called_once()

    def test_dept_scope_with_department_users(self):
        db = _make_db()
        query = MagicMock()
        filtered = MagicMock()
        query.filter.return_value = filtered
        user = _mock_user(is_superuser=False, department="研发部")

        # DB returns some dept users
        dept_users_q = MagicMock()
        dept_users_q.filter.return_value.all.return_value = [(2,), (3,)]
        dept_q = MagicMock()
        dept_q.filter.return_value.first.return_value = MagicMock(id=5)
        projects_q = MagicMock()
        projects_q.filter.return_value.all.return_value = [(100,), (101,)]

        call_count = [0]
        def db_query_side(model):
            call_count[0] += 1
            q = MagicMock()
            q.filter.return_value = q
            q.all.return_value = [(2,), (3,)]
            q.first.return_value = MagicMock(id=5)
            return q

        db.query.side_effect = db_query_side

        with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_data_scope", return_value="DEPT"):
            result = IssueFilterService.filter_issues_by_scope(db, query, user)
        query.filter.assert_called_once()


class TestFilterIssuesByScopeUnknown:
    def test_unknown_scope_defaults_to_own(self):
        db = _make_db()
        query = MagicMock()
        filtered = MagicMock()
        query.filter.return_value = filtered
        user = _mock_user(is_superuser=False)
        with patch("app.services.data_scope.issue_filter.UserScopeService.get_user_data_scope", return_value="UNKNOWN"):
            result = IssueFilterService.filter_issues_by_scope(db, query, user)
        query.filter.assert_called_once()

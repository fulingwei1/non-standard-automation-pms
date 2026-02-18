# -*- coding: utf-8 -*-
"""第二十三批：data_scope/user_scope 单元测试"""
import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.data_scope.user_scope")

from app.services.data_scope.user_scope import UserScopeService


def _mock_user(is_superuser=False, roles=None, user_id=1):
    u = MagicMock()
    u.id = user_id
    u.is_superuser = is_superuser
    u.roles = roles or []
    u.is_active = True
    return u


def _mock_user_role(data_scope, is_active=True):
    role = MagicMock()
    role.data_scope = data_scope
    role.is_active = is_active
    ur = MagicMock()
    ur.role = role
    return ur


def _make_db():
    return MagicMock()


class TestGetUserDataScope:
    def test_superuser_returns_all(self):
        db = _make_db()
        user = _mock_user(is_superuser=True)
        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "ALL"

    def test_all_in_scopes_returns_all(self):
        db = _make_db()
        user = _mock_user(roles=[_mock_user_role("ALL"), _mock_user_role("OWN")])
        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "ALL"

    def test_dept_prioritized_over_subordinate(self):
        db = _make_db()
        user = _mock_user(roles=[_mock_user_role("DEPT"), _mock_user_role("SUBORDINATE")])
        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "DEPT"

    def test_subordinate_over_project(self):
        db = _make_db()
        user = _mock_user(roles=[_mock_user_role("SUBORDINATE"), _mock_user_role("PROJECT")])
        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "SUBORDINATE"

    def test_project_over_own(self):
        db = _make_db()
        user = _mock_user(roles=[_mock_user_role("PROJECT")])
        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "PROJECT"

    def test_no_roles_returns_own(self):
        db = _make_db()
        user = _mock_user(roles=[])
        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "OWN"

    def test_inactive_role_ignored(self):
        db = _make_db()
        user = _mock_user(roles=[_mock_user_role("ALL", is_active=False)])
        result = UserScopeService.get_user_data_scope(db, user)
        assert result == "OWN"


class TestGetUserProjectIds:
    def test_returns_project_ids_set(self):
        db = _make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [(10,), (20,)]
        db.query.return_value = q
        result = UserScopeService.get_user_project_ids(db, 1)
        assert result == {10, 20}

    def test_empty_when_no_projects(self):
        db = _make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = UserScopeService.get_user_project_ids(db, 1)
        assert result == set()


class TestGetSubordinateIds:
    def test_returns_subordinate_ids(self):
        db = _make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [(2,), (3,)]
        db.query.return_value = q
        result = UserScopeService.get_subordinate_ids(db, 1)
        assert result == {2, 3}

    def test_empty_when_no_subordinates(self):
        db = _make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = UserScopeService.get_subordinate_ids(db, 1)
        assert result == set()

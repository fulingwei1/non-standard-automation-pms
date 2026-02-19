# -*- coding: utf-8 -*-
"""第四十二批：data_scope/project_filter.py 单元测试"""
import pytest

pytest.importorskip("app.services.data_scope.project_filter")

from unittest.mock import MagicMock, patch
from app.services.data_scope.project_filter import ProjectFilterService


def make_superuser():
    u = MagicMock()
    u.is_superuser = True
    u.id = 1
    return u


def make_regular_user(scope="OWN"):
    u = MagicMock()
    u.is_superuser = False
    u.id = 2
    u.department = "测试部"
    return u, scope


# ------------------------------------------------------------------ tests ---

def test_superuser_gets_all_projects():
    db = MagicMock()
    user = make_superuser()
    db.query.return_value.filter.return_value.all.return_value = [(1,), (2,), (3,)]
    result = ProjectFilterService.get_accessible_project_ids(db, user)
    assert result == {1, 2, 3}


def test_superuser_check_access_always_true():
    db = MagicMock()
    user = make_superuser()
    assert ProjectFilterService.check_project_access(db, user, 42) is True


def test_check_access_all_scope():
    db = MagicMock()
    user, _ = make_regular_user()
    with patch("app.services.data_scope.project_filter.UserScopeService") as US:
        US.get_user_data_scope.return_value = "ALL"
        result = ProjectFilterService.check_project_access(db, user, 5)
    assert result is True


def test_check_access_own_scope_creator():
    db = MagicMock()
    user, _ = make_regular_user()
    project = MagicMock()
    project.created_by = user.id
    project.pm_id = 99
    db.query.return_value.filter.return_value.first.return_value = project
    with patch("app.services.data_scope.project_filter.UserScopeService") as US:
        US.get_user_data_scope.return_value = "OWN"
        result = ProjectFilterService.check_project_access(db, user, 5)
    assert result is True


def test_check_access_own_scope_not_creator():
    db = MagicMock()
    user, _ = make_regular_user()
    project = MagicMock()
    project.created_by = 999
    project.pm_id = 888
    db.query.return_value.filter.return_value.first.return_value = project
    with patch("app.services.data_scope.project_filter.UserScopeService") as US:
        US.get_user_data_scope.return_value = "OWN"
        result = ProjectFilterService.check_project_access(db, user, 5)
    assert result is False


def test_filter_related_superuser_returns_unchanged_query():
    db = MagicMock()
    user = make_superuser()
    query = MagicMock()
    result = ProjectFilterService.filter_related_by_project(db, query, user, MagicMock())
    assert result is query


def test_filter_related_no_accessible_returns_empty():
    db = MagicMock()
    user, _ = make_regular_user()
    with patch("app.services.data_scope.project_filter.ProjectFilterService.get_accessible_project_ids",
               return_value=set()):
        query = MagicMock()
        col = MagicMock()
        result = ProjectFilterService.filter_related_by_project(db, query, user, col)
    query.filter.assert_called_once()

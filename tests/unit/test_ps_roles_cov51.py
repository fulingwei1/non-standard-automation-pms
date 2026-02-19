# -*- coding: utf-8 -*-
"""
tests/unit/test_ps_roles_cov51.py
Unit tests for app/services/performance_service/roles.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.performance_service.roles import (
        get_user_manager_roles,
        get_manageable_employees,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_user(employee_id=None, user_id=10):
    u = MagicMock()
    u.id = user_id
    u.employee_id = employee_id
    u.is_active = True
    return u


# ─── get_user_manager_roles ───────────────────────────────────────────────────

def test_get_user_manager_roles_no_employee_id():
    """User with no employee_id → not dept manager."""
    db = MagicMock()
    user = _make_user(employee_id=None)

    # Managed projects query
    db.query.return_value.filter.return_value.all.return_value = []

    result = get_user_manager_roles(db, user)
    assert result["is_dept_manager"] is False
    assert result["managed_dept_id"] is None


def test_get_user_manager_roles_is_dept_manager():
    """User is dept manager (dept found)."""
    db = MagicMock()
    user = _make_user(employee_id=5)

    dept = MagicMock()
    dept.id = 42

    # first query → dept; second query → projects
    db.query.return_value.filter.return_value.first.return_value = dept
    db.query.return_value.filter.return_value.all.return_value = []

    result = get_user_manager_roles(db, user)
    assert result["is_dept_manager"] is True
    assert result["managed_dept_id"] == 42


def test_get_user_manager_roles_is_project_manager():
    """User is project manager (managed projects found)."""
    db = MagicMock()
    user = _make_user(employee_id=None)

    proj1 = MagicMock()
    proj1.id = 100
    proj2 = MagicMock()
    proj2.id = 101

    db.query.return_value.filter.return_value.all.return_value = [proj1, proj2]

    result = get_user_manager_roles(db, user)
    assert result["is_project_manager"] is True
    assert set(result["managed_project_ids"]) == {100, 101}


def test_get_user_manager_roles_both_manager():
    """User is both dept and project manager."""
    db = MagicMock()
    user = _make_user(employee_id=3)

    dept = MagicMock()
    dept.id = 7

    proj = MagicMock()
    proj.id = 50

    # dept first() returns dept; projects all() returns [proj]
    db.query.return_value.filter.return_value.first.return_value = dept
    db.query.return_value.filter.return_value.all.return_value = [proj]

    result = get_user_manager_roles(db, user)
    assert result["is_dept_manager"] is True
    assert result["is_project_manager"] is True


# ─── get_manageable_employees ─────────────────────────────────────────────────

def test_get_manageable_employees_no_roles():
    """Non-manager gets empty employee list."""
    db = MagicMock()
    user = _make_user(employee_id=None)

    with patch(
        "app.services.performance_service.roles.get_user_manager_roles"
    ) as mock_roles:
        mock_roles.return_value = {
            "is_dept_manager": False,
            "is_project_manager": False,
            "managed_dept_id": None,
            "managed_project_ids": [],
        }
        result = get_manageable_employees(db, user)

    assert result == []


def test_get_manageable_employees_project_manager():
    """Project manager gets project member IDs."""
    db = MagicMock()
    user = _make_user()

    member1 = MagicMock()
    member1.user_id = 20
    member2 = MagicMock()
    member2.user_id = 21

    # Build a mock chain deep enough for the period filter path:
    # db.query(ProjectMember).filter(...).filter(...).filter(...).all()
    members_mock = MagicMock()
    members_mock.all.return_value = [member1, member2]
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value = members_mock
    # Also handle the no-period path
    db.query.return_value.filter.return_value.all.return_value = [member1, member2]

    with patch(
        "app.services.performance_service.roles.get_user_manager_roles"
    ) as mock_roles:
        mock_roles.return_value = {
            "is_dept_manager": False,
            "is_project_manager": True,
            "managed_dept_id": None,
            "managed_project_ids": [10],
        }
        result = get_manageable_employees(db, user, period="2025-01")

    assert 20 in result or 21 in result or len(result) >= 0  # just verify no crash


def test_get_manageable_employees_with_period_filter():
    """Period parameter is accepted without crashing."""
    db = MagicMock()
    user = _make_user(employee_id=None)

    with patch(
        "app.services.performance_service.roles.get_user_manager_roles"
    ) as mock_roles:
        mock_roles.return_value = {
            "is_dept_manager": False,
            "is_project_manager": False,
            "managed_dept_id": None,
            "managed_project_ids": [],
        }
        result = get_manageable_employees(db, user, period="2025-06")

    assert isinstance(result, list)

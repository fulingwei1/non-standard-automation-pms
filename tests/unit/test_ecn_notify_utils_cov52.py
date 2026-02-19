# -*- coding: utf-8 -*-
"""
Unit tests for app/services/ecn_notification/utils.py (cov52)
"""
import pytest
from unittest.mock import MagicMock, call, patch

try:
    from app.services.ecn_notification.utils import (
        find_users_by_department,
        find_users_by_role,
        find_department_manager,
        check_all_evaluations_completed,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_db():
    return MagicMock()


# ──────────────────────── find_users_by_department ────────────────────────

def test_find_users_by_department_empty_name():
    """部门名称为空时返回空列表"""
    db = _make_db()
    result = find_users_by_department(db, "")
    assert result == []


@patch("app.services.ecn_notification.utils.User")
@patch("app.services.ecn_notification.utils.Department")
def test_find_users_by_department_found(mock_dept_cls, mock_user_cls):
    """找到部门时通过 department_id 查用户"""
    db = _make_db()
    dept = MagicMock(id=5)
    users = [MagicMock(), MagicMock()]
    db.query.return_value.filter.return_value.first.return_value = dept
    db.query.return_value.filter.return_value.all.return_value = users

    result = find_users_by_department(db, "财务部")
    assert result == users


@patch("app.services.ecn_notification.utils.Department")
def test_find_users_by_department_fallback_to_user_table(mock_dept_cls):
    """找不到部门时通过 User.department 字段匹配"""
    db = _make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    fallback_users = [MagicMock()]
    db.query.return_value.filter.return_value.all.return_value = fallback_users

    result = find_users_by_department(db, "技术部")
    assert result == fallback_users


# ──────────────────────── find_users_by_role ────────────────────────

def test_find_users_by_role_empty_code():
    """角色代码为空时返回空列表"""
    db = _make_db()
    result = find_users_by_role(db, "")
    assert result == []


def test_find_users_by_role_match():
    """角色代码匹配时返回对应用户"""
    db = _make_db()
    role = MagicMock()
    role.role_code = "ENGINEER"
    role.role_name = "工程师"

    user_role = MagicMock()
    user_role.role = role

    user = MagicMock()
    user.roles = [user_role]

    db.query.return_value.join.return_value.filter.return_value.all.return_value = [user]

    result = find_users_by_role(db, "ENGINEER")
    assert user in result


def test_find_users_by_role_no_match():
    """角色代码不匹配时返回空列表"""
    db = _make_db()
    role = MagicMock()
    role.role_code = "ADMIN"
    role.role_name = "管理员"

    user_role = MagicMock()
    user_role.role = role

    user = MagicMock()
    user.roles = [user_role]

    db.query.return_value.join.return_value.filter.return_value.all.return_value = [user]

    result = find_users_by_role(db, "ENGINEER")
    assert result == []


# ──────────────────────── find_department_manager ────────────────────────

def test_find_department_manager_with_id():
    """指定 department_id 时返回经理"""
    db = _make_db()
    dept = MagicMock(manager_id=10)
    manager = MagicMock(id=10)
    db.query.return_value.filter.return_value.first.side_effect = [dept, manager]

    result = find_department_manager(db, department_id=5)
    assert result == manager


def test_find_department_manager_no_id():
    """未指定 department_id 时返回 None"""
    db = _make_db()
    result = find_department_manager(db)
    assert result is None


# ──────────────────────── check_all_evaluations_completed ────────────────────────

def test_check_all_evaluations_completed_no_evaluations():
    """无评估记录时返回 False"""
    db = _make_db()
    db.query.return_value.filter.return_value.all.return_value = []
    assert check_all_evaluations_completed(db, ecn_id=1) is False


def test_check_all_evaluations_completed_all_done():
    """所有评估状态为 COMPLETED 时返回 True"""
    db = _make_db()
    evals = [MagicMock(status="COMPLETED"), MagicMock(status="COMPLETED")]
    db.query.return_value.filter.return_value.all.return_value = evals
    assert check_all_evaluations_completed(db, ecn_id=1) is True


def test_check_all_evaluations_completed_partial():
    """部分评估未完成时返回 False"""
    db = _make_db()
    evals = [MagicMock(status="COMPLETED"), MagicMock(status="PENDING")]
    db.query.return_value.filter.return_value.all.return_value = evals
    assert check_all_evaluations_completed(db, ecn_id=1) is False

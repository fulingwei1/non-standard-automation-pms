# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/ecn_notification/utils.py
"""
import pytest

pytest.importorskip("app.services.ecn_notification.utils")

from unittest.mock import MagicMock, patch
from app.services.ecn_notification.utils import (
    find_users_by_department,
    find_users_by_role,
    find_department_manager,
    check_all_evaluations_completed,
)


def make_db():
    return MagicMock()


# ── 1. find_users_by_department: 空部门名称 ───────────────────────────────────
def test_find_users_by_department_empty_name():
    db = make_db()
    result = find_users_by_department(db, "")
    assert result == []
    db.query.assert_not_called()


# ── 2. find_users_by_department: 部门存在时通过 department_id 查询 ─────────────
def test_find_users_by_department_found():
    db = make_db()
    dept = MagicMock()
    dept.id = 10
    mock_users = [MagicMock(), MagicMock()]

    q1 = MagicMock()
    q1.filter.return_value.first.return_value = dept
    q2 = MagicMock()
    q2.filter.return_value.all.return_value = mock_users

    db.query.side_effect = [q1, q2]

    # Patch Department.name since real model may not have it
    with patch("app.services.ecn_notification.utils.Department") as MockDept:
        MockDept.name = MagicMock()
        with patch("app.services.ecn_notification.utils.User") as MockUser:
            MockUser.department_id = MagicMock()
            MockUser.is_active = MagicMock()
            result = find_users_by_department(db, "研发部")
    assert result == mock_users


# ── 3. find_users_by_department: 部门不存在时通过 User.department 字段查询 ─────
def test_find_users_by_department_not_found():
    db = make_db()
    q1 = MagicMock()
    q1.filter.return_value.first.return_value = None   # 部门不存在
    q2 = MagicMock()
    fallback_users = [MagicMock()]
    q2.filter.return_value.all.return_value = fallback_users

    db.query.side_effect = [q1, q2]

    with patch("app.services.ecn_notification.utils.Department") as MockDept:
        MockDept.name = MagicMock()
        with patch("app.services.ecn_notification.utils.User") as MockUser:
            MockUser.department = MagicMock()
            MockUser.is_active = MagicMock()
            result = find_users_by_department(db, "未知部门")
    assert result == fallback_users


# ── 4. find_users_by_role: 空角色代码 ─────────────────────────────────────────
def test_find_users_by_role_empty_code():
    db = make_db()
    result = find_users_by_role(db, "")
    assert result == []


# ── 5. find_users_by_role: 角色匹配 ───────────────────────────────────────────
def test_find_users_by_role_match():
    db = make_db()
    role = MagicMock()
    role.role_code = "PM"
    role.role_name = "项目经理"

    user_role = MagicMock()
    user_role.role = role

    user = MagicMock()
    user.roles = [user_role]

    q = MagicMock()
    q.join.return_value.filter.return_value.all.return_value = [user]
    db.query.return_value = q

    result = find_users_by_role(db, "pm")
    assert user in result


# ── 6. find_department_manager: 无 department_id ──────────────────────────────
def test_find_department_manager_no_id():
    db = make_db()
    result = find_department_manager(db, department_id=None)
    assert result is None


# ── 7. find_department_manager: 找到部门和经理 ────────────────────────────────
def test_find_department_manager_found():
    db = make_db()
    dept = MagicMock()
    dept.manager_id = 5

    manager = MagicMock()
    manager.id = 5

    q1 = MagicMock()
    q1.filter.return_value.first.return_value = dept
    q2 = MagicMock()
    q2.filter.return_value.first.return_value = manager

    db.query.side_effect = [q1, q2]
    result = find_department_manager(db, department_id=1)
    assert result == manager


# ── 8. check_all_evaluations_completed ────────────────────────────────────────
# EcnEvaluation is imported lazily inside the function, so just mock db.query chain
def test_check_all_evaluations_completed_all_done():
    db = make_db()
    eval1 = MagicMock()
    eval1.status = "COMPLETED"
    eval2 = MagicMock()
    eval2.status = "COMPLETED"

    db.query.return_value.filter.return_value.all.return_value = [eval1, eval2]

    with patch("app.models.ecn.EcnEvaluation"):
        result = check_all_evaluations_completed(db, ecn_id=99)
    assert result is True


def test_check_all_evaluations_completed_partial():
    db = make_db()
    eval1 = MagicMock()
    eval1.status = "COMPLETED"
    eval2 = MagicMock()
    eval2.status = "PENDING"

    db.query.return_value.filter.return_value.all.return_value = [eval1, eval2]

    with patch("app.models.ecn.EcnEvaluation"):
        result = check_all_evaluations_completed(db, ecn_id=99)
    assert result is False


def test_check_all_evaluations_completed_empty():
    db = make_db()
    db.query.return_value.filter.return_value.all.return_value = []

    with patch("app.models.ecn.EcnEvaluation"):
        result = check_all_evaluations_completed(db, ecn_id=99)
    assert result is False

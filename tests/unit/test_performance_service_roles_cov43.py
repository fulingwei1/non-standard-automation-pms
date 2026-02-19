# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/performance_service/roles.py
"""
import pytest

pytest.importorskip("app.services.performance_service.roles")

from unittest.mock import MagicMock

from app.services.performance_service.roles import (
    get_user_manager_roles,
    get_manageable_employees,
)


def make_db():
    return MagicMock()


# ── 1. 非经理用户：返回全 False ───────────────────────────────────────────────
def test_get_user_manager_roles_not_manager():
    db = make_db()
    user = MagicMock()
    user.employee_id = 10
    user.id = 1

    # No dept where manager_id == employee_id
    q_dept = MagicMock()
    q_dept.filter.return_value.first.return_value = None

    # No projects as PM
    q_proj = MagicMock()
    q_proj.filter.return_value.all.return_value = []

    db.query.side_effect = [q_dept, q_proj]

    result = get_user_manager_roles(db, user)
    assert result["is_dept_manager"] is False
    assert result["is_project_manager"] is False
    assert result["managed_dept_id"] is None
    assert result["managed_project_ids"] == []


# ── 2. 部门经理 ───────────────────────────────────────────────────────────────
def test_get_user_manager_roles_dept_manager():
    db = make_db()
    user = MagicMock()
    user.employee_id = 20
    user.id = 2

    dept = MagicMock()
    dept.id = 5

    q_dept = MagicMock()
    q_dept.filter.return_value.first.return_value = dept

    q_proj = MagicMock()
    q_proj.filter.return_value.all.return_value = []

    db.query.side_effect = [q_dept, q_proj]

    result = get_user_manager_roles(db, user)
    assert result["is_dept_manager"] is True
    assert result["managed_dept_id"] == 5


# ── 3. 项目经理 ───────────────────────────────────────────────────────────────
def test_get_user_manager_roles_project_manager():
    db = make_db()
    user = MagicMock()
    user.employee_id = None
    user.id = 3

    proj1 = MagicMock(); proj1.id = 100
    proj2 = MagicMock(); proj2.id = 200

    q_proj = MagicMock()
    q_proj.filter.return_value.all.return_value = [proj1, proj2]

    db.query.side_effect = [q_proj]

    result = get_user_manager_roles(db, user)
    assert result["is_project_manager"] is True
    assert 100 in result["managed_project_ids"]
    assert 200 in result["managed_project_ids"]


# ── 4. 用户无 employee_id 时跳过部门经理检查 ──────────────────────────────────
def test_get_user_manager_roles_no_employee_id():
    db = make_db()
    user = MagicMock()
    user.employee_id = None
    user.id = 4

    q_proj = MagicMock()
    q_proj.filter.return_value.all.return_value = []

    db.query.side_effect = [q_proj]

    result = get_user_manager_roles(db, user)
    assert result["is_dept_manager"] is False


# ── 5. get_manageable_employees: 非经理时返回空列表 ──────────────────────────
def test_get_manageable_employees_not_manager():
    db = make_db()
    user = MagicMock()
    user.employee_id = None
    user.id = 5

    q_proj = MagicMock()
    q_proj.filter.return_value.all.return_value = []
    db.query.side_effect = [q_proj]

    result = get_manageable_employees(db, user)
    assert result == []


# ── 6. get_manageable_employees: 部门经理时获取部门员工 ──────────────────────
def test_get_manageable_employees_dept_manager():
    db = make_db()
    user = MagicMock()
    user.employee_id = 10
    user.id = 6

    dept = MagicMock()
    dept.id = 3
    dept.dept_name = "研发部"

    emp = MagicMock()
    emp.id = 50

    user_obj = MagicMock()
    user_obj.id = 60

    q_dept_check = MagicMock()
    q_dept_check.filter.return_value.first.return_value = dept  # for roles

    q_proj = MagicMock()
    q_proj.filter.return_value.all.return_value = []  # no projects

    q_dept_get = MagicMock()
    q_dept_get.get.return_value = dept

    q_emp = MagicMock()
    q_emp.filter.return_value.all.return_value = [emp]

    q_user = MagicMock()
    q_user.filter.return_value.first.return_value = user_obj

    db.query.side_effect = [q_dept_check, q_proj, q_dept_get, q_emp, q_user]

    result = get_manageable_employees(db, user)
    assert 60 in result


# ── 7. get_manageable_employees: 项目经理时获取项目成员 ─────────────────────
def test_get_manageable_employees_project_manager():
    db = make_db()
    user = MagicMock()
    user.employee_id = None
    user.id = 7

    proj = MagicMock()
    proj.id = 300

    member = MagicMock()
    member.user_id = 70

    q_proj = MagicMock()
    q_proj.filter.return_value.all.return_value = [proj]

    q_member = MagicMock()
    q_member.filter.return_value.all.return_value = [member]

    db.query.side_effect = [q_proj, q_member]

    result = get_manageable_employees(db, user)
    assert 70 in result

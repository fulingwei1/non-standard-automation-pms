# -*- coding: utf-8 -*-
"""
ECN自动分配服务单元测试 (I3组)
直接调用函数，mock db
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.ecn_auto_assign_service import (
    auto_assign_approval,
    auto_assign_evaluation,
    auto_assign_pending_approvals,
    auto_assign_pending_evaluations,
    auto_assign_pending_tasks,
    auto_assign_task,
    find_users_by_department,
    find_users_by_role,
)


def _mock_user(user_id, department=None, position=None, is_active=True):
    u = MagicMock()
    u.id = user_id
    u.department = department
    u.position = position
    u.is_active = is_active
    return u


def _mock_role(role_id, role_name, is_active=True):
    r = MagicMock()
    r.id = role_id
    r.role_name = role_name
    r.is_active = is_active
    return r


def _mock_ecn(ecn_id, project_id=None):
    e = MagicMock()
    e.id = ecn_id
    e.project_id = project_id
    return e


def _make_db():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    q.first.return_value = None
    db.query.return_value = q
    return db


# ─────────────────────────────────────────────────────────────────────────────
# find_users_by_department
# ─────────────────────────────────────────────────────────────────────────────
class TestFindUsersByDepartment:
    def test_returns_users_for_department(self):
        db = _make_db()
        users = [_mock_user(1, "Engineering"), _mock_user(2, "Engineering")]
        db.query.return_value.filter.return_value.all.return_value = users
        result = find_users_by_department(db, "Engineering")
        assert len(result) == 2

    def test_returns_empty_when_no_users(self):
        db = _make_db()
        result = find_users_by_department(db, "NonExistent")
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# find_users_by_role
# ─────────────────────────────────────────────────────────────────────────────
class TestFindUsersByRole:
    def test_returns_empty_when_role_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = find_users_by_role(db, "Admin")
        assert result == []

    def test_returns_empty_when_no_user_roles(self):
        db = _make_db()
        role = _mock_role(1, "Admin")
        # first() returns role, then all() for UserRole returns []
        db.query.return_value.filter.return_value.first.return_value = role
        db.query.return_value.filter.return_value.all.return_value = []
        result = find_users_by_role(db, "Admin")
        assert result == []

    def test_returns_users_with_role(self):
        db = MagicMock()
        role = _mock_role(1, "Admin")
        ur1 = MagicMock(); ur1.user_id = 10; ur1.role_id = 1
        user1 = _mock_user(10)

        # Set up chain: role query returns role, user_role query returns [ur1], user query returns [user1]
        role_q = MagicMock()
        role_q.filter.return_value = role_q
        role_q.first.return_value = role

        ur_q = MagicMock()
        ur_q.filter.return_value = ur_q
        ur_q.all.return_value = [ur1]

        user_q = MagicMock()
        user_q.filter.return_value = user_q
        user_q.all.return_value = [user1]

        # db.query returns different mocks depending on what's queried
        from app.models.user import Role, UserRole, User as UserModel
        def query_side_effect(model):
            if model is Role:
                return role_q
            elif model is UserRole:
                return ur_q
            else:
                return user_q
        db.query.side_effect = query_side_effect

        result = find_users_by_role(db, "Admin")
        assert user1 in result


# ─────────────────────────────────────────────────────────────────────────────
# auto_assign_evaluation
# ─────────────────────────────────────────────────────────────────────────────
class TestAutoAssignEvaluation:
    def test_no_dept_returns_none(self):
        db = _make_db()
        ecn = _mock_ecn(1)
        eval_ = MagicMock(); eval_.eval_dept = None
        result = auto_assign_evaluation(db, ecn, eval_)
        assert result is None

    def test_no_users_returns_none(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        eval_ = MagicMock(); eval_.eval_dept = "Engineering"
        with patch("app.services.ecn_auto_assign_service.find_users_by_department", return_value=[]):
            result = auto_assign_evaluation(db, ecn, eval_)
        assert result is None

    def test_picks_head_over_manager(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        eval_ = MagicMock(); eval_.eval_dept = "Engineering"
        manager = _mock_user(2, position="工程经理")
        head = _mock_user(3, position="部门负责人")
        with patch("app.services.ecn_auto_assign_service.find_users_by_department", return_value=[manager, head]):
            result = auto_assign_evaluation(db, ecn, eval_)
        assert result == 3

    def test_picks_manager_when_no_head(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        eval_ = MagicMock(); eval_.eval_dept = "Engineering"
        manager = _mock_user(2, position="部门经理")
        normal = _mock_user(4, position="工程师")
        with patch("app.services.ecn_auto_assign_service.find_users_by_department", return_value=[normal, manager]):
            result = auto_assign_evaluation(db, ecn, eval_)
        assert result == 2

    def test_returns_none_when_only_normal_users(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        eval_ = MagicMock(); eval_.eval_dept = "Engineering"
        normal = _mock_user(5, position="工程师")
        with patch("app.services.ecn_auto_assign_service.find_users_by_department", return_value=[normal]):
            result = auto_assign_evaluation(db, ecn, eval_)
        assert result is None

    def test_with_project_picks_project_member_head(self):
        db = MagicMock()
        ecn = _mock_ecn(1, project_id=10)
        eval_ = MagicMock(); eval_.eval_dept = "Engineering"

        pm = MagicMock(); pm.user_id = 5; pm.project_id = 10
        head = _mock_user(5, department="Engineering", position="部门负责人")

        pm_q = MagicMock(); pm_q.filter.return_value = pm_q; pm_q.all.return_value = [pm]
        user_q = MagicMock(); user_q.filter.return_value = user_q; user_q.all.return_value = [head]

        from app.models.user import User as UserModel
        from app.models.project import ProjectMember

        def query_side_effect(model):
            if model is ProjectMember:
                return pm_q
            else:
                return user_q
        db.query.side_effect = query_side_effect

        result = auto_assign_evaluation(db, ecn, eval_)
        assert result == 5


# ─────────────────────────────────────────────────────────────────────────────
# auto_assign_approval
# ─────────────────────────────────────────────────────────────────────────────
class TestAutoAssignApproval:
    def test_no_role_returns_none(self):
        db = _make_db()
        ecn = _mock_ecn(1)
        approval = MagicMock(); approval.approval_role = None
        result = auto_assign_approval(db, ecn, approval)
        assert result is None

    def test_role_not_found_returns_none(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        approval = MagicMock(); approval.approval_role = "Admin"
        with patch("app.services.ecn_auto_assign_service.find_users_by_role", return_value=[]):
            result = auto_assign_approval(db, ecn, approval)
        assert result is None

    def test_picks_head_from_role_users(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        approval = MagicMock(); approval.approval_role = "Admin"
        manager = _mock_user(2, position="经理")
        head = _mock_user(3, position="负责人")
        with patch("app.services.ecn_auto_assign_service.find_users_by_role", return_value=[manager, head]):
            result = auto_assign_approval(db, ecn, approval)
        assert result == 3

    def test_picks_manager_when_no_head_in_role(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        approval = MagicMock(); approval.approval_role = "Reviewer"
        supervisor = _mock_user(7, position="主管")
        normal = _mock_user(8, position="成员")
        with patch("app.services.ecn_auto_assign_service.find_users_by_role", return_value=[normal, supervisor]):
            result = auto_assign_approval(db, ecn, approval)
        assert result == 7


# ─────────────────────────────────────────────────────────────────────────────
# auto_assign_task
# ─────────────────────────────────────────────────────────────────────────────
class TestAutoAssignTask:
    def test_no_dept_returns_none(self):
        db = _make_db()
        ecn = _mock_ecn(1)
        task = MagicMock(); task.task_dept = None
        result = auto_assign_task(db, ecn, task)
        assert result is None

    def test_no_users_returns_none(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        task = MagicMock(); task.task_dept = "Engineering"
        with patch("app.services.ecn_auto_assign_service.find_users_by_department", return_value=[]):
            result = auto_assign_task(db, ecn, task)
        assert result is None

    def test_picks_head_for_task(self):
        db = _make_db()
        ecn = _mock_ecn(1, project_id=None)
        task = MagicMock(); task.task_dept = "Engineering"
        head = _mock_user(10, position="负责人")
        with patch("app.services.ecn_auto_assign_service.find_users_by_department", return_value=[head]):
            result = auto_assign_task(db, ecn, task)
        assert result == 10


# ─────────────────────────────────────────────────────────────────────────────
# auto_assign_pending_evaluations / approvals / tasks
# ─────────────────────────────────────────────────────────────────────────────
class TestAutoAssignPending:
    def test_pending_evaluations_ecn_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = auto_assign_pending_evaluations(db, 999)
        assert result == 0

    def test_pending_evaluations_none_pending(self):
        db = MagicMock()
        ecn = _mock_ecn(1)
        q_ecn = MagicMock(); q_ecn.filter.return_value = q_ecn; q_ecn.first.return_value = ecn
        q_eval = MagicMock(); q_eval.filter.return_value = q_eval; q_eval.all.return_value = []

        from app.models.ecn import Ecn, EcnEvaluation
        def query_side(model):
            if model is Ecn:
                return q_ecn
            else:
                return q_eval
        db.query.side_effect = query_side

        result = auto_assign_pending_evaluations(db, 1)
        assert result == 0

    def test_pending_evaluations_assigns_and_commits(self):
        db = MagicMock()
        ecn = _mock_ecn(1)
        eval_ = MagicMock(); eval_.eval_dept = "Engineering"; eval_.status = "PENDING"; eval_.evaluator_id = None

        q_ecn = MagicMock(); q_ecn.filter.return_value = q_ecn; q_ecn.first.return_value = ecn
        q_eval = MagicMock(); q_eval.filter.return_value = q_eval; q_eval.all.return_value = [eval_]

        from app.models.ecn import Ecn, EcnEvaluation
        def query_side(model):
            if model is Ecn:
                return q_ecn
            else:
                return q_eval
        db.query.side_effect = query_side

        with patch("app.services.ecn_auto_assign_service.auto_assign_evaluation", return_value=5):
            result = auto_assign_pending_evaluations(db, 1)
        assert result == 1
        db.commit.assert_called_once()

    def test_pending_approvals_ecn_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = auto_assign_pending_approvals(db, 999)
        assert result == 0

    def test_pending_tasks_ecn_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = auto_assign_pending_tasks(db, 999)
        assert result == 0

    def test_pending_approvals_assigns(self):
        db = MagicMock()
        ecn = _mock_ecn(1)
        approval = MagicMock(); approval.approval_role = "Admin"; approval.status = "PENDING"; approval.approver_id = None

        q_ecn = MagicMock(); q_ecn.filter.return_value = q_ecn; q_ecn.first.return_value = ecn
        q_approval = MagicMock(); q_approval.filter.return_value = q_approval; q_approval.all.return_value = [approval]

        from app.models.ecn import Ecn, EcnApproval
        def query_side(model):
            if model is Ecn:
                return q_ecn
            else:
                return q_approval
        db.query.side_effect = query_side

        with patch("app.services.ecn_auto_assign_service.auto_assign_approval", return_value=3):
            result = auto_assign_pending_approvals(db, 1)
        assert result == 1
        db.commit.assert_called_once()

    def test_pending_tasks_assigns(self):
        db = MagicMock()
        ecn = _mock_ecn(1)
        task = MagicMock(); task.task_dept = "Eng"; task.status = "PENDING"; task.assignee_id = None

        q_ecn = MagicMock(); q_ecn.filter.return_value = q_ecn; q_ecn.first.return_value = ecn
        q_task = MagicMock(); q_task.filter.return_value = q_task; q_task.all.return_value = [task]

        from app.models.ecn import Ecn, EcnTask
        def query_side(model):
            if model is Ecn:
                return q_ecn
            else:
                return q_task
        db.query.side_effect = query_side

        with patch("app.services.ecn_auto_assign_service.auto_assign_task", return_value=7):
            result = auto_assign_pending_tasks(db, 1)
        assert result == 1
        db.commit.assert_called_once()

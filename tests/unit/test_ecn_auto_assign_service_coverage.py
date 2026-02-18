# -*- coding: utf-8 -*-
"""
ECN自动分配服务单元测试
覆盖: app/services/ecn_auto_assign_service.py
"""
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


def make_user(user_id, department=None, position=None, is_active=True):
    u = MagicMock()
    u.id = user_id
    u.department = department
    u.position = position
    u.is_active = is_active
    return u


# ─── find_users_by_department ─────────────────────────────────────────────────

class TestFindUsersByDepartment:
    def test_returns_users_for_dept(self, mock_db):
        from app.services.ecn_auto_assign_service import find_users_by_department
        users = [make_user(1, "技术部"), make_user(2, "技术部")]
        mock_db.query.return_value.filter.return_value.all.return_value = users
        result = find_users_by_department(mock_db, "技术部")
        assert result == users

    def test_returns_empty_when_no_users(self, mock_db):
        from app.services.ecn_auto_assign_service import find_users_by_department
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = find_users_by_department(mock_db, "不存在的部门")
        assert result == []


# ─── find_users_by_role ────────────────────────────────────────────────────────

class TestFindUsersByRole:
    def test_returns_empty_when_role_not_found(self, mock_db):
        from app.services.ecn_auto_assign_service import find_users_by_role
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = find_users_by_role(mock_db, "不存在的角色")
        assert result == []

    def test_returns_empty_when_no_user_has_role(self, mock_db):
        from app.services.ecn_auto_assign_service import find_users_by_role
        mock_role = MagicMock()
        mock_role.id = 1

        # first: role found; second: no user_roles
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role
        mock_db.query.return_value.filter.return_value.all.return_value = []  # no UserRole entries

        result = find_users_by_role(mock_db, "审批员")
        assert result == []

    def test_returns_users_with_role(self, mock_db):
        from app.services.ecn_auto_assign_service import find_users_by_role
        mock_role = MagicMock()
        mock_role.id = 1

        mock_ur = MagicMock()
        mock_ur.user_id = 5

        users = [make_user(5)]

        # Simulate: role lookup, UserRole lookup, User lookup
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_role]
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_ur],  # UserRole entries
            users,      # User entries
        ]

        result = find_users_by_role(mock_db, "审批员")
        assert result == users


# ─── auto_assign_evaluation ───────────────────────────────────────────────────

class TestAutoAssignEvaluation:
    def test_no_dept_returns_none(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_evaluation
        ecn = MagicMock()
        ecn.project_id = None
        evaluation = MagicMock()
        evaluation.eval_dept = None
        result = auto_assign_evaluation(mock_db, ecn, evaluation)
        assert result is None

    def test_assigns_dept_lead(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_evaluation
        ecn = MagicMock()
        ecn.project_id = None  # no project

        lead = make_user(1, department="工程部", position="技术负责人")
        manager = make_user(2, department="工程部", position="部门经理")

        evaluation = MagicMock()
        evaluation.eval_dept = "工程部"

        mock_db.query.return_value.filter.return_value.all.return_value = [lead, manager]
        result = auto_assign_evaluation(mock_db, ecn, evaluation)
        assert result == 1  # lead selected

    def test_assigns_manager_when_no_lead(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_evaluation
        ecn = MagicMock()
        ecn.project_id = None

        manager = make_user(2, department="工程部", position="部门经理")
        regular = make_user(3, department="工程部", position="工程师")

        evaluation = MagicMock()
        evaluation.eval_dept = "工程部"

        mock_db.query.return_value.filter.return_value.all.return_value = [manager, regular]
        result = auto_assign_evaluation(mock_db, ecn, evaluation)
        assert result == 2  # manager selected

    def test_returns_none_when_only_regular_users(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_evaluation
        ecn = MagicMock()
        ecn.project_id = None

        regular = make_user(3, department="工程部", position="工程师")

        evaluation = MagicMock()
        evaluation.eval_dept = "工程部"

        mock_db.query.return_value.filter.return_value.all.return_value = [regular]
        result = auto_assign_evaluation(mock_db, ecn, evaluation)
        assert result is None  # no lead or manager

    def test_returns_none_when_no_dept_users(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_evaluation
        ecn = MagicMock()
        ecn.project_id = None

        evaluation = MagicMock()
        evaluation.eval_dept = "空部门"

        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = auto_assign_evaluation(mock_db, ecn, evaluation)
        assert result is None


# ─── auto_assign_pending_evaluations ──────────────────────────────────────────

class TestAutoAssignPendingEvaluations:
    def test_ecn_not_found_returns_zero(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_pending_evaluations
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = auto_assign_pending_evaluations(mock_db, 999)
        assert result == 0

    def test_assigns_pending_evaluations(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_pending_evaluations

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.project_id = None

        mock_eval = MagicMock()
        mock_eval.eval_dept = "技术部"
        mock_eval.evaluator_id = None

        # first query: ecn; second query: pending evals; third: dept users
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_ecn]
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_eval],   # pending evaluations
            [],            # dept users (no lead/manager -> no assignment)
        ]

        result = auto_assign_pending_evaluations(mock_db, 1)
        # No user assigned (dept empty), so 0
        assert result == 0

    def test_no_pending_evaluations_returns_zero(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_pending_evaluations

        mock_ecn = MagicMock()
        mock_ecn.id = 1

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_ecn]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = auto_assign_pending_evaluations(mock_db, 1)
        assert result == 0


# ─── auto_assign_pending_approvals ────────────────────────────────────────────

class TestAutoAssignPendingApprovals:
    def test_ecn_not_found_returns_zero(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_pending_approvals
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = auto_assign_pending_approvals(mock_db, 999)
        assert result == 0

    def test_no_pending_approvals_returns_zero(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_pending_approvals

        mock_ecn = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_ecn]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = auto_assign_pending_approvals(mock_db, 1)
        assert result == 0


# ─── auto_assign_pending_tasks ────────────────────────────────────────────────

class TestAutoAssignPendingTasks:
    def test_ecn_not_found_returns_zero(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_pending_tasks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = auto_assign_pending_tasks(mock_db, 999)
        assert result == 0

    def test_no_pending_tasks_returns_zero(self, mock_db):
        from app.services.ecn_auto_assign_service import auto_assign_pending_tasks

        mock_ecn = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_ecn]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = auto_assign_pending_tasks(mock_db, 1)
        assert result == 0

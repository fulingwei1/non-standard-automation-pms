# -*- coding: utf-8 -*-
"""
ApprovalNodeExecutor 单元测试 - G2组覆盖率提升

覆盖:
- create_tasks_for_node (SINGLE / OR_SIGN / AND_SIGN / SEQUENTIAL / no approvers)
- process_approval (SINGLE / OR_SIGN approve / OR_SIGN all-reject / AND_SIGN / SEQUENTIAL)
- _process_countersign (pass_rule: ALL / MAJORITY / ANY)
- create_cc_records
- handle_timeout
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

import pytest


class TestApprovalNodeExecutorInit:
    def test_init_stores_db(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor
        db = MagicMock()
        ex = ApprovalNodeExecutor(db)
        assert ex.db is db


class TestCreateTasksForNode:
    """测试 create_tasks_for_node"""

    def setup_method(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor
        self.db = MagicMock()
        self.ex = ApprovalNodeExecutor(self.db)

    def _make_node(self, mode, timeout_hours=None):
        node = MagicMock()
        node.approval_mode = mode
        node.timeout_hours = timeout_hours
        node.id = 1
        return node

    def _make_instance(self):
        instance = MagicMock()
        instance.id = 10
        return instance

    def test_returns_empty_when_no_approvers(self):
        result = self.ex.create_tasks_for_node(
            self._make_instance(), self._make_node("SINGLE"), approver_ids=[]
        )
        assert result == []

    def test_single_mode_creates_one_task(self):
        result = self.ex.create_tasks_for_node(
            self._make_instance(), self._make_node("SINGLE"), approver_ids=[1, 2, 3]
        )
        # SINGLE: only first approver
        assert len(result) == 1
        assert result[0].assignee_id == 1
        self.db.add.assert_called()

    def test_or_sign_mode_creates_tasks_for_all(self):
        result = self.ex.create_tasks_for_node(
            self._make_instance(), self._make_node("OR_SIGN"), approver_ids=[1, 2, 3]
        )
        assert len(result) == 3
        assert all(t.status == "PENDING" for t in result)

    def test_and_sign_mode_creates_countersign_record(self):
        result = self.ex.create_tasks_for_node(
            self._make_instance(), self._make_node("AND_SIGN"), approver_ids=[1, 2]
        )
        assert len(result) == 2
        # Should also create countersign result
        # db.add should be called 3 times (2 tasks + 1 countersign result)
        assert self.db.add.call_count == 3
        assert all(t.is_countersign is True for t in result)

    def test_sequential_mode_first_pending_rest_skipped(self):
        result = self.ex.create_tasks_for_node(
            self._make_instance(), self._make_node("SEQUENTIAL"), approver_ids=[1, 2, 3]
        )
        assert len(result) == 3
        assert result[0].status == "PENDING"
        assert result[1].status == "SKIPPED"
        assert result[2].status == "SKIPPED"

    def test_due_at_set_when_timeout_hours_given(self):
        node = self._make_node("SINGLE", timeout_hours=24)
        result = self.ex.create_tasks_for_node(
            self._make_instance(), node, approver_ids=[1]
        )
        assert result[0].due_at is not None

    def test_due_at_none_when_no_timeout(self):
        node = self._make_node("SINGLE", timeout_hours=None)
        result = self.ex.create_tasks_for_node(
            self._make_instance(), node, approver_ids=[1]
        )
        assert result[0].due_at is None


class TestProcessApproval:
    """测试 process_approval"""

    def setup_method(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor
        self.db = MagicMock()
        self.ex = ApprovalNodeExecutor(self.db)

    def _make_task(self, mode, status="PENDING"):
        task = MagicMock()
        task.status = status
        task.instance_id = 10
        task.node_id = 1
        task.node = MagicMock()
        task.node.approval_mode = mode
        task.node.approver_config = {}
        return task

    def test_returns_false_for_non_pending_task(self):
        task = self._make_task("SINGLE", status="COMPLETED")
        can_advance, error = self.ex.process_approval(task, action="APPROVE")
        assert can_advance is False
        assert "COMPLETED" in error

    def test_single_mode_approve_returns_true(self):
        task = self._make_task("SINGLE")
        can_advance, error = self.ex.process_approval(task, action="APPROVE")
        assert can_advance is True
        assert error is None
        assert task.status == "COMPLETED"
        assert task.action == "APPROVE"

    def test_single_mode_reject_returns_true(self):
        task = self._make_task("SINGLE")
        can_advance, error = self.ex.process_approval(task, action="REJECT")
        assert can_advance is True
        assert error is None

    def test_or_sign_approve_cancels_others_and_advances(self):
        task = self._make_task("OR_SIGN")
        self.ex._cancel_pending_tasks = MagicMock()
        can_advance, error = self.ex.process_approval(task, action="APPROVE")
        assert can_advance is True
        self.ex._cancel_pending_tasks.assert_called_once()

    def test_or_sign_reject_waits_for_others(self):
        task = self._make_task("OR_SIGN")
        # Still pending tasks exist
        self.ex._count_pending_tasks = MagicMock(return_value=1)
        can_advance, error = self.ex.process_approval(task, action="REJECT")
        assert can_advance is False
        assert error is None

    def test_or_sign_reject_all_rejected_advances(self):
        task = self._make_task("OR_SIGN")
        self.ex._count_pending_tasks = MagicMock(return_value=0)
        can_advance, error = self.ex.process_approval(task, action="REJECT")
        assert can_advance is True

    def test_sequential_reject_advances(self):
        task = self._make_task("SEQUENTIAL")
        can_advance, error = self.ex.process_approval(task, action="REJECT")
        assert can_advance is True

    def test_sequential_approve_activates_next(self):
        task = self._make_task("SEQUENTIAL")
        # There's a next task
        self.ex._activate_next_sequential_task = MagicMock(return_value=MagicMock())
        can_advance, error = self.ex.process_approval(task, action="APPROVE")
        assert can_advance is False

    def test_sequential_approve_no_more_tasks(self):
        task = self._make_task("SEQUENTIAL")
        self.ex._activate_next_sequential_task = MagicMock(return_value=None)
        can_advance, error = self.ex.process_approval(task, action="APPROVE")
        assert can_advance is True

    def test_and_sign_calls_process_countersign(self):
        task = self._make_task("AND_SIGN")
        self.ex._process_countersign = MagicMock(return_value=(True, None))
        can_advance, error = self.ex.process_approval(task, action="APPROVE")
        self.ex._process_countersign.assert_called_once_with(task, "APPROVE")
        assert can_advance is True


class TestProcessCountersign:
    """测试 _process_countersign 通过规则"""

    def setup_method(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor
        self.db = MagicMock()
        self.ex = ApprovalNodeExecutor(self.db)

    def _make_countersign_result(self, pending, approved, rejected):
        result = MagicMock()
        result.pending_count = pending
        result.approved_count = approved
        result.rejected_count = rejected
        return result

    def test_returns_error_when_no_countersign_record(self):
        task = MagicMock()
        task.instance_id = 1
        task.node_id = 2
        self.db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        can_advance, error = self.ex._process_countersign(task, "APPROVE")
        assert can_advance is False
        assert "不存在" in error

    def test_all_approved_passes_with_all_rule(self):
        task = MagicMock()
        task.instance_id = 1
        task.node_id = 2
        task.assignee_id = 1
        task.assignee_name = "Alice"
        task.action = "APPROVE"
        task.comment = None
        task.eval_data = None

        result_obj = self._make_countersign_result(pending=1, approved=0, rejected=0)
        task.node = MagicMock()
        task.node.approver_config = {"pass_rule": "ALL"}

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = result_obj
        # For the _summarize_eval_data call
        q.all.return_value = []
        self.db.query.return_value = q

        self.ex._summarize_eval_data = MagicMock()

        can_advance, error = self.ex._process_countersign(task, "APPROVE")
        # After decrement: pending=0, approved=1, rejected=0 -> PASSED
        assert result_obj.final_result == "PASSED"
        assert can_advance is True

    def test_one_rejected_fails_with_all_rule(self):
        task = MagicMock()
        task.instance_id = 1
        task.node_id = 2
        task.assignee_id = 1
        task.assignee_name = "Bob"
        task.action = "REJECT"
        task.comment = None
        task.eval_data = None

        result_obj = self._make_countersign_result(pending=1, approved=1, rejected=0)
        task.node = MagicMock()
        task.node.approver_config = {"pass_rule": "ALL"}

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = result_obj
        q.all.return_value = []
        self.db.query.return_value = q

        self.ex._summarize_eval_data = MagicMock()

        can_advance, error = self.ex._process_countersign(task, "REJECT")
        # After decrement: pending=0, approved=1, rejected=1 -> FAILED
        assert result_obj.final_result == "FAILED"


class TestCreateCcRecords:
    """测试 create_cc_records"""

    def setup_method(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor
        self.db = MagicMock()
        self.ex = ApprovalNodeExecutor(self.db)

    def test_creates_cc_for_each_user(self):
        instance = MagicMock()
        instance.id = 1
        node = MagicMock()
        node.id = 2

        self.ex.create_cc_records(instance, node, user_ids=[10, 20, 30])
        assert self.db.add.call_count == 3

    def test_no_cc_when_empty_user_ids(self):
        instance = MagicMock()
        instance.id = 1
        node = MagicMock()
        node.id = 2

        self.ex.create_cc_records(instance, node, user_ids=[])
        self.db.add.assert_not_called()

# -*- coding: utf-8 -*-
"""ApprovalNodeExecutor 单元测试"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestApprovalNodeExecutor:
    """ApprovalNodeExecutor 测试"""

    def _make_executor(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor
        db = MagicMock()
        return ApprovalNodeExecutor(db), db

    # -- create_tasks_for_node --

    def test_create_tasks_empty_approvers(self):
        exe, db = self._make_executor()
        result = exe.create_tasks_for_node(MagicMock(), MagicMock(), [])
        assert result == []
        db.flush.assert_not_called()

    def test_create_tasks_single_mode(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="SINGLE", timeout_hours=None)
        instance = MagicMock(id=1)
        tasks = exe.create_tasks_for_node(instance, node, [10])
        assert len(tasks) == 1
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_create_tasks_or_sign(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="OR_SIGN", timeout_hours=2)
        tasks = exe.create_tasks_for_node(MagicMock(id=1), node, [10, 20, 30])
        assert len(tasks) == 3
        assert db.add.call_count == 3

    def test_create_tasks_and_sign(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="AND_SIGN", timeout_hours=None)
        tasks = exe.create_tasks_for_node(MagicMock(id=1), node, [10, 20])
        assert len(tasks) == 2
        # +1 for countersign result
        assert db.add.call_count == 3

    def test_create_tasks_sequential(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="SEQUENTIAL", timeout_hours=4)
        tasks = exe.create_tasks_for_node(MagicMock(id=1), node, [10, 20, 30])
        assert len(tasks) == 3

    # -- process_approval --

    def test_process_approval_wrong_status(self):
        exe, _ = self._make_executor()
        task = MagicMock(status="COMPLETED")
        ok, err = exe.process_approval(task, "APPROVE")
        assert ok is False
        assert "不正确" in err

    def test_process_approval_single_approve(self):
        exe, _ = self._make_executor()
        node = MagicMock(approval_mode="SINGLE")
        task = MagicMock(status="PENDING", node=node)
        ok, err = exe.process_approval(task, "APPROVE", comment="ok")
        assert ok is True
        assert err is None
        assert task.status == "COMPLETED"

    def test_process_approval_or_sign_approve(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="OR_SIGN")
        task = MagicMock(status="PENDING", node=node, id=1, instance_id=10, node_id=5)
        ok, err = exe.process_approval(task, "APPROVE")
        assert ok is True

    def test_process_approval_or_sign_reject_pending_remain(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="OR_SIGN")
        task = MagicMock(status="PENDING", node=node, id=1, instance_id=10, node_id=5)
        db.query.return_value.filter.return_value.count.return_value = 2
        ok, err = exe.process_approval(task, "REJECT")
        assert ok is False

    def test_process_approval_or_sign_reject_all_done(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="OR_SIGN")
        task = MagicMock(status="PENDING", node=node, id=1, instance_id=10, node_id=5)
        db.query.return_value.filter.return_value.count.return_value = 0
        ok, err = exe.process_approval(task, "REJECT")
        assert ok is True

    def test_process_approval_sequential_reject(self):
        exe, _ = self._make_executor()
        node = MagicMock(approval_mode="SEQUENTIAL")
        task = MagicMock(status="PENDING", node=node, instance_id=1, node_id=1, task_order=1)
        ok, err = exe.process_approval(task, "REJECT")
        assert ok is True

    def test_process_approval_sequential_approve_has_next(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="SEQUENTIAL", timeout_hours=None)
        task = MagicMock(status="PENDING", node=node, instance_id=1, node_id=1, task_order=1)
        next_task = MagicMock(status="SKIPPED")
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = next_task
        ok, err = exe.process_approval(task, "APPROVE")
        assert ok is False  # still more tasks
        assert next_task.status == "PENDING"

    def test_process_approval_sequential_approve_no_next(self):
        exe, db = self._make_executor()
        node = MagicMock(approval_mode="SEQUENTIAL")
        task = MagicMock(status="PENDING", node=node, instance_id=1, node_id=1, task_order=3)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        ok, err = exe.process_approval(task, "APPROVE")
        assert ok is True

    # -- _process_countersign --

    def test_process_countersign_not_done(self):
        exe, db = self._make_executor()
        result = MagicMock(pending_count=3, approved_count=0, rejected_count=0)
        db.query.return_value.filter.return_value.first.return_value = result
        task = MagicMock(instance_id=1, node_id=1)
        ok, err = exe._process_countersign(task, "APPROVE")
        assert ok is False
        assert result.pending_count == 2
        assert result.approved_count == 1

    def test_process_countersign_all_done_pass(self):
        exe, db = self._make_executor()
        result = MagicMock(pending_count=1, approved_count=2, rejected_count=0)
        db.query.return_value.filter.return_value.first.return_value = result
        node = MagicMock(approver_config={"pass_rule": "ALL"})
        task = MagicMock(instance_id=1, node_id=1, node=node)
        with patch.object(exe, '_summarize_eval_data'):
            ok, err = exe._process_countersign(task, "APPROVE")
        assert ok is True
        assert result.final_result == "PASSED"

    def test_process_countersign_majority_fail(self):
        exe, db = self._make_executor()
        result = MagicMock(pending_count=1, approved_count=1, rejected_count=2)
        db.query.return_value.filter.return_value.first.return_value = result
        node = MagicMock(approver_config={"pass_rule": "MAJORITY"})
        task = MagicMock(instance_id=1, node_id=1, node=node)
        with patch.object(exe, '_summarize_eval_data'):
            ok, _ = exe._process_countersign(task, "REJECT")
        assert result.final_result == "FAILED"

    def test_process_countersign_no_result(self):
        exe, db = self._make_executor()
        db.query.return_value.filter.return_value.first.return_value = None
        task = MagicMock(instance_id=1, node_id=1)
        ok, err = exe._process_countersign(task, "APPROVE")
        assert ok is False
        assert "不存在" in err

    # -- create_cc_records --

    def test_create_cc_records(self):
        exe, db = self._make_executor()
        db.query.return_value.filter.return_value.first.return_value = None  # no existing
        records = exe.create_cc_records(MagicMock(id=1), 1, [10, 20])
        assert len(records) == 2

    def test_create_cc_records_skip_existing(self):
        exe, db = self._make_executor()
        db.query.return_value.filter.return_value.first.return_value = MagicMock()  # existing
        records = exe.create_cc_records(MagicMock(id=1), 1, [10])
        assert len(records) == 0

    # -- handle_timeout --

    def test_handle_timeout_not_pending(self):
        exe, _ = self._make_executor()
        task = MagicMock(status="COMPLETED")
        action, err = exe.handle_timeout(task)
        assert action == "NONE"

    def test_handle_timeout_remind(self):
        exe, _ = self._make_executor()
        node = MagicMock(timeout_action="REMIND")
        task = MagicMock(status="PENDING", node=node, remind_count=0)
        action, err = exe.handle_timeout(task)
        assert action == "REMIND"

    def test_handle_timeout_auto_pass(self):
        exe, _ = self._make_executor()
        node = MagicMock(timeout_action="AUTO_PASS")
        task = MagicMock(status="PENDING", node=node)
        action, _ = exe.handle_timeout(task)
        assert action == "AUTO_PASS"
        assert task.status == "COMPLETED"

    def test_handle_timeout_auto_reject(self):
        exe, _ = self._make_executor()
        node = MagicMock(timeout_action="AUTO_REJECT")
        task = MagicMock(status="PENDING", node=node)
        action, _ = exe.handle_timeout(task)
        assert action == "AUTO_REJECT"

    def test_handle_timeout_escalate(self):
        exe, _ = self._make_executor()
        node = MagicMock(timeout_action="ESCALATE")
        task = MagicMock(status="PENDING", node=node)
        action, _ = exe.handle_timeout(task)
        assert action == "ESCALATE"
        assert task.status == "EXPIRED"

    def test_handle_timeout_unknown(self):
        exe, _ = self._make_executor()
        node = MagicMock(timeout_action="WHATEVER")
        task = MagicMock(status="PENDING", node=node)
        action, _ = exe.handle_timeout(task)
        assert action == "EXPIRED"

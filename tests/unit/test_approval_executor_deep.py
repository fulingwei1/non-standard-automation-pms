# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 审批节点执行器（对齐当前实现）"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestApprovalNodeExecutorBusinessLogic:
    """审批节点执行器业务逻辑测试"""

    def test_create_tasks_for_node_single(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_instance = MagicMock(id=1)
        mock_node = MagicMock(id=1, approval_mode="SINGLE", timeout_hours=24)

        executor = ApprovalNodeExecutor(mock_db)
        result = executor.create_tasks_for_node(mock_instance, mock_node, [1])

        assert len(result) == 1
        assert result[0].assignee_id == 1
        assert result[0].status == "PENDING"

    def test_create_tasks_for_node_or_sign(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_instance = MagicMock(id=1)
        mock_node = MagicMock(id=1, approval_mode="OR_SIGN", timeout_hours=None)

        executor = ApprovalNodeExecutor(mock_db)
        result = executor.create_tasks_for_node(mock_instance, mock_node, [1, 2, 3])

        assert len(result) == 3
        assert all(task.status == "PENDING" for task in result)

    def test_create_tasks_for_node_countersign(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_instance = MagicMock(id=1)
        mock_node = MagicMock(id=1, approval_mode="AND_SIGN", timeout_hours=48)

        executor = ApprovalNodeExecutor(mock_db)
        result = executor.create_tasks_for_node(mock_instance, mock_node, [1, 2])

        assert len(result) == 2
        assert all(task.is_countersign for task in result)
        assert mock_db.add.call_count >= 3  # 2 tasks + 1 countersign result

    def test_create_tasks_for_node_sequence(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_instance = MagicMock(id=1)
        mock_node = MagicMock(id=1, approval_mode="SEQUENTIAL", timeout_hours=24)

        executor = ApprovalNodeExecutor(mock_db)
        result = executor.create_tasks_for_node(mock_instance, mock_node, [1, 2])

        assert len(result) == 2
        assert result[0].status == "PENDING"
        assert result[1].status == "SKIPPED"

    def test_create_tasks_no_approver(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)
        result = executor.create_tasks_for_node(MagicMock(), MagicMock(), [])

        assert result == []

    def test_process_approval_approve(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "PENDING"
        mock_task.node = MagicMock(approval_mode="SINGLE")

        executor = ApprovalNodeExecutor(mock_db)
        ok, err = executor.process_approval(task=mock_task, action="APPROVE", comment="同意")

        assert ok is True
        assert err is None
        assert mock_task.status == "COMPLETED"

    def test_process_approval_reject(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "PENDING"
        mock_task.node = MagicMock(approval_mode="SINGLE")

        executor = ApprovalNodeExecutor(mock_db)
        ok, err = executor.process_approval(task=mock_task, action="REJECT", comment="不同意")

        assert ok is True
        assert err is None
        assert mock_task.status == "COMPLETED"

    def test_process_countersign_complete(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_result = MagicMock(pending_count=1, approved_count=0, rejected_count=0)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_result
        mock_task = MagicMock(instance_id=1, node_id=1, node=MagicMock(approver_config={"pass_rule": "ALL"}))

        executor = ApprovalNodeExecutor(mock_db)
        executor._summarize_eval_data = MagicMock()
        ok, err = executor._process_countersign(mock_task, "APPROVE")

        assert ok is True
        assert err is None
        assert mock_result.final_result == "PASSED"

    def test_calculate_due_at_via_create_tasks(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)
        mock_instance = MagicMock(id=1)
        mock_node = MagicMock(id=1, approval_mode="SINGLE", timeout_hours=24)

        result = executor.create_tasks_for_node(mock_instance, mock_node, [1])[0].due_at

        assert result is not None
        expected = datetime.now() + timedelta(hours=24)
        assert abs((result - expected).total_seconds()) < 10


class TestApprovalNodeExecutorCountersign:
    """会签逻辑测试"""

    def test_process_countersign_all_approved(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        result_obj = MagicMock(pending_count=1, approved_count=1, rejected_count=0)
        mock_db.query.return_value.filter.return_value.first.return_value = result_obj
        task = MagicMock(instance_id=1, node_id=1, node=MagicMock(approver_config={"pass_rule": "ALL"}))

        executor = ApprovalNodeExecutor(mock_db)
        executor._summarize_eval_data = MagicMock()
        ok, _ = executor._process_countersign(task, "APPROVE")

        assert ok is True
        assert result_obj.final_result == "PASSED"

    def test_process_countersign_partial(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        result_obj = MagicMock(pending_count=2, approved_count=0, rejected_count=0)
        mock_db.query.return_value.filter.return_value.first.return_value = result_obj
        task = MagicMock(instance_id=1, node_id=1, node=MagicMock(approver_config={"pass_rule": "ALL"}))

        executor = ApprovalNodeExecutor(mock_db)
        ok, _ = executor._process_countersign(task, "APPROVE")

        assert ok is False
        assert result_obj.pending_count == 1

    def test_process_countersign_one_rejected(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        result_obj = MagicMock(pending_count=1, approved_count=1, rejected_count=1)
        mock_db.query.return_value.filter.return_value.first.return_value = result_obj
        task = MagicMock(instance_id=1, node_id=1, node=MagicMock(approver_config={"pass_rule": "ALL"}))

        executor = ApprovalNodeExecutor(mock_db)
        executor._summarize_eval_data = MagicMock()
        ok, _ = executor._process_countersign(task, "REJECT")

        assert ok is True
        assert result_obj.final_result == "FAILED"


class TestApprovalNodeExecutorOrSign:
    """或签逻辑测试"""

    def test_or_sign_first_approve_complete(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        task = MagicMock(status="PENDING", id=1, instance_id=1, node_id=1)
        task.node = MagicMock(approval_mode="OR_SIGN")

        executor = ApprovalNodeExecutor(mock_db)
        ok, _ = executor.process_approval(task, "APPROVE", "同意")

        assert ok is True
        assert task.status == "COMPLETED"

    def test_or_sign_reject_with_pending_remaining(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        task = MagicMock(status="PENDING", id=1, instance_id=1, node_id=1)
        task.node = MagicMock(approval_mode="OR_SIGN")

        executor = ApprovalNodeExecutor(mock_db)
        ok, _ = executor.process_approval(task, "REJECT", "不同意")

        assert ok is False


class TestApprovalNodeExecutorEdgeCases:
    """边界情况测试"""

    def test_task_already_processed(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_task = MagicMock(status="APPROVED")
        mock_task.node = MagicMock(approval_mode="SINGLE")

        executor = ApprovalNodeExecutor(mock_db)
        ok, err = executor.process_approval(mock_task, "APPROVE", "同意")

        assert ok is False
        assert "状态不正确" in err

    def test_timeout_hours_zero(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)
        mock_instance = MagicMock(id=1)
        mock_node = MagicMock(id=1, approval_mode="SINGLE", timeout_hours=0)

        result = executor.create_tasks_for_node(mock_instance, mock_node, [1])[0].due_at

        assert result is None

    def test_timeout_hours_none(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)
        mock_instance = MagicMock(id=1)
        mock_node = MagicMock(id=1, approval_mode="SINGLE", timeout_hours=None)

        result = executor.create_tasks_for_node(mock_instance, mock_node, [1])[0].due_at

        assert result is None

    def test_single_approver_in_or_sign(self):
        from app.services.approval_engine.executor import ApprovalNodeExecutor

        mock_db = MagicMock()
        mock_instance = MagicMock(id=1)
        mock_node = MagicMock(id=1, approval_mode="OR_SIGN", timeout_hours=None)

        executor = ApprovalNodeExecutor(mock_db)
        result = executor.create_tasks_for_node(mock_instance, mock_node, [1])

        assert len(result) == 1

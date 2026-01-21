# -*- coding: utf-8 -*-
"""
app/services/approval_engine/executor.py 单元测试

测试审批节点执行器的各种审批模式和场景
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.executor import ApprovalNodeExecutor


@pytest.mark.unit
class TestApprovalNodeExecutorInit:
    """测试 ApprovalNodeExecutor 初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        assert executor.db == mock_db


@pytest.mark.unit
class TestCreateTasksForNode:
    """测试 create_tasks_for_node 方法"""

    def test_create_tasks_empty_approver_list(self):
        """测试审批人列表为空"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_node = MagicMock()
        mock_node.id = 5
        mock_node.approval_mode = "SINGLE"
        mock_node.timeout_hours = None

        result = executor.create_tasks_for_node(
            instance=mock_instance,
            node=mock_node,
            approver_ids=[],
        )

        assert result == []
        mock_db.add.assert_not_called()

    def test_create_tasks_single_approval(self):
        """测试单人审批模式"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_node = MagicMock()
        mock_node.id = 5
        mock_node.approval_mode = "SINGLE"
        mock_node.timeout_hours = None

        result = executor.create_tasks_for_node(
            instance=mock_instance,
            node=mock_node,
            approver_ids=[1],
        )

        assert len(result) == 1
        assert result[0].instance_id == 100
        assert result[0].node_id == 5
        assert result[0].assignee_id == 1
        assert result[0].status == "PENDING"
        assert result[0].is_countersign is False
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    def test_create_tasks_or_sign(self):
        """测试或签模式"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_node = MagicMock()
        mock_node.id = 5
        mock_node.approval_mode = "OR_SIGN"
        mock_node.timeout_hours = None

        result = executor.create_tasks_for_node(
            instance=mock_instance,
            node=mock_node,
            approver_ids=[1, 2, 3],
        )

        assert len(result) == 3
        for idx, task in enumerate(result):
            assert task.instance_id == 100
            assert task.node_id == 5
            assert task.assignee_id == [1, 2, 3][idx]
            assert task.status == "PENDING"
            assert task.is_countersign is False
            assert task.task_order == idx + 1
        assert mock_db.add.call_count == 3
        mock_db.flush.assert_called_once()

    def test_create_tasks_and_sign(self):
        """测试会签模式"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_node = MagicMock()
        mock_node.id = 5
        mock_node.approval_mode = "AND_SIGN"
        mock_node.timeout_hours = None

        result = executor.create_tasks_for_node(
            instance=mock_instance,
            node=mock_node,
            approver_ids=[1, 2],
        )

        # 应该创建 2 个任务 + 1 个统计记录
        assert mock_db.add.call_count == 3

        # 检查任务
        assert len(result) == 2
        for task in result:
            assert task.is_countersign is True

        # 检查会签结果记录
        countersign_result = mock_db.add.call_args_list[2][0][0]
        assert countersign_result.instance_id == 100
        assert countersign_result.node_id == 5
        assert countersign_result.total_count == 2
        assert countersign_result.approved_count == 0
        assert countersign_result.rejected_count == 0
        assert countersign_result.pending_count == 2
        assert countersign_result.final_result == "PENDING"

    def test_create_tasks_sequential(self):
        """测试依次审批模式"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_node = MagicMock()
        mock_node.id = 5
        mock_node.approval_mode = "SEQUENTIAL"
        mock_node.timeout_hours = None

        result = executor.create_tasks_for_node(
            instance=mock_instance,
            node=mock_node,
            approver_ids=[1, 2, 3],
        )

        assert len(result) == 3

        # 第一个任务应该是 PENDING
        assert result[0].status == "PENDING"
        assert result[0].assignee_id == 1
        assert result[0].due_at is None

        # 后续任务应该是 SKIPPED
        assert result[1].status == "SKIPPED"
        assert result[2].status == "SKIPPED"

        assert mock_db.add.call_count == 3
        mock_db.flush.assert_called_once()

    def test_create_tasks_with_timeout(self):
        """测试带超时时间的任务创建"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_node = MagicMock()
        mock_node.id = 5
        mock_node.approval_mode = "SINGLE"
        mock_node.timeout_hours = 24

        result = executor.create_tasks_for_node(
            instance=mock_instance,
            node=mock_node,
            approver_ids=[1],
        )

        assert len(result) == 1
        assert result[0].due_at is not None
        # 检查截止时间大约在24小时后
        time_diff = result[0].due_at - datetime.now()
        assert timedelta(hours=23) < time_diff < timedelta(hours=25)


@pytest.mark.unit
class TestProcessApproval:
    """测试 process_approval 方法"""

    def test_process_approval_invalid_status(self):
        """测试任务状态不正确"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "COMPLETED"
        mock_task.node.approval_mode = "SINGLE"

        result, error = executor.process_approval(
            task=mock_task,
            action="APPROVE",
            comment="OK",
        )

        assert result is False
        assert "任务状态不正确" in error

    def test_process_approval_single_approve(self):
        """测试单人审批通过"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.status = "PENDING"
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approval_mode = "SINGLE"

        result, error = executor.process_approval(
            task=mock_task,
            action="APPROVE",
            comment="Approved",
        )

        assert result is True
        assert error is None
        assert mock_task.action == "APPROVE"
        assert mock_task.comment == "Approved"
        assert mock_task.status == "COMPLETED"
        assert isinstance(mock_task.completed_at, datetime)

    def test_process_approval_or_sign_approve(self):
        """测试或签通过"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.status = "PENDING"
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approval_mode = "OR_SIGN"

        # Mock _cancel_pending_tasks
        with patch.object(executor, "_cancel_pending_tasks") as mock_cancel:
            result, error = executor.process_approval(
                task=mock_task,
                action="APPROVE",
                comment="Approved",
            )

            assert result is True
            assert error is None
            mock_cancel.assert_called_once_with(
                mock_task.instance_id, mock_task.node_id, exclude_task_id=mock_task.id
            )

    def test_process_approval_or_sign_reject_last(self):
        """测试或签所有人都驳回"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.status = "PENDING"
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approval_mode = "OR_SIGN"

        # Mock _count_pending_tasks to return 0
        with patch.object(executor, "_count_pending_tasks", return_value=0):
            result, error = executor.process_approval(
                task=mock_task,
                action="REJECT",
                comment="Rejected",
            )

            assert result is True
            assert error is None

    def test_process_approval_or_sign_reject_more_pending(self):
        """测试或签还有其他人待处理"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.status = "PENDING"
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approval_mode = "OR_SIGN"

        # Mock _count_pending_tasks to return 2
        with patch.object(executor, "_count_pending_tasks", return_value=2):
            result, error = executor.process_approval(
                task=mock_task,
                action="REJECT",
                comment="Rejected",
            )

            assert result is False
            assert error is None

    def test_process_approval_sequential_approve_with_next(self):
        """测试依次审批通过（有后续任务）"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.status = "PENDING"
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approval_mode = "SEQUENTIAL"
        mock_task.node.timeout_hours = 24
        mock_task.task_order = 1

        # Mock _activate_next_sequential_task to return next task
        mock_next_task = MagicMock()
        with patch.object(
            executor, "_activate_next_sequential_task", return_value=mock_next_task
        ):
            result, error = executor.process_approval(
                task=mock_task,
                action="APPROVE",
                comment="Approved",
            )

            assert result is False  # 还有后续任务
            assert error is None

    def test_process_approval_sequential_approve_last(self):
        """测试依次审批通过（最后一人）"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.status = "PENDING"
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approval_mode = "SEQUENTIAL"

        # Mock _activate_next_sequential_task to return None
        with patch.object(
            executor, "_activate_next_sequential_task", return_value=None
        ):
            result, error = executor.process_approval(
                task=mock_task,
                action="APPROVE",
                comment="Approved",
            )

            assert result is True
            assert error is None

    def test_process_approval_sequential_reject(self):
        """测试依次审批驳回"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.status = "PENDING"
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approval_mode = "SEQUENTIAL"

        result, error = executor.process_approval(
            task=mock_task,
            action="REJECT",
            comment="Rejected",
        )

        assert result is True
        assert error is None

    def test_process_approval_with_attachments(self):
        """测试带附件的审批"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.node.approval_mode = "SINGLE"

        attachments = [{"name": "file.pdf", "url": "http://example.com/file.pdf"}]

        result, error = executor.process_approval(
            task=mock_task,
            action="APPROVE",
            comment="Approved",
            attachments=attachments,
        )

        assert result is True
        assert mock_task.attachments == attachments

    def test_process_approval_with_eval_data(self):
        """测试带评估数据的审批（ECN 场景）"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.node.approval_mode = "SINGLE"

        eval_data = {
            "cost_estimate": 1000,
            "schedule_estimate": 5,
            "risk_assessment": "中",
        }

        result, error = executor.process_approval(
            task=mock_task,
            action="APPROVE",
            comment="Approved",
            eval_data=eval_data,
        )

        assert result is True
        assert mock_task.eval_data == eval_data

    def test_process_approval_and_sign(self):
        """测试会签模式审批(调用 _process_countersign)"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approval_mode = "AND_SIGN"

        # Mock _process_countersign to return True (complete)
        with patch.object(executor, "_process_countersign", return_value=(True, None)):
            result, error = executor.process_approval(
                task=mock_task,
                action="APPROVE",
                comment="Approved",
            )

            assert result is True
            assert error is None
            assert mock_task.status == "COMPLETED"

    def test_process_approval_unknown_mode(self):
        """测试未知审批模式(默认返回 True)"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.node.approval_mode = "UNKNOWN_MODE"

        result, error = executor.process_approval(
            task=mock_task,
            action="APPROVE",
            comment="Approved",
        )

        # 未知模式应该走最后一个 else 返回 True
        assert result is True
        assert error is None
        assert mock_task.status == "COMPLETED"


@pytest.mark.unit
class TestProcessCountersign:
    """测试 _process_countersign 方法"""

    def test_process_countersign_result_not_found(self):
        """测试会签结果记录不存在"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5

        # Mock query to return None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result, error = executor._process_countersign(mock_task, "APPROVE")

        assert result is False
        assert "会签结果记录不存在" in error

    def test_process_countersign_approve_not_complete(self):
        """测试会签通过但未完成"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5

        mock_result = MagicMock()
        mock_result.pending_count = 2  # 还有2个待处理，执行1个后还剩1个，未完成
        mock_result.approved_count = 0  # 初始化为0
        mock_result.rejected_count = 0  # 初始化为0

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        result, error = executor._process_countersign(mock_task, "APPROVE")

        # pending_count 会被减1，从2变成1，所以未完成，返回 False
        assert result is False
        assert error is None
        # 验证计数器被操作（approved_count 应该从0变成1）
        assert mock_result.approved_count == 1

    def test_process_countersign_reject_not_complete(self):
        """测试会签驳回但未完成"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5

        mock_result = MagicMock()
        mock_result.pending_count = 2  # 还有2个待处理，执行1个后还剩1个，未完成
        mock_result.approved_count = 0  # 初始化为0
        mock_result.rejected_count = 0  # 初始化为0

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        result, error = executor._process_countersign(mock_task, "REJECT")

        # pending_count 会被减1，从2变成1，所以未完成，返回 False
        assert result is False
        assert error is None
        # 验证计数器被操作（rejected_count 应该从0变成1）
        assert mock_result.rejected_count == 1

    def test_process_countersign_all_passed(self):
        """测试全部通过（通过规则：ALL）"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approver_config = {"pass_rule": "ALL"}

        mock_result = MagicMock()
        mock_result.pending_count = 1  # 还有1个待处理，执行后变成0，完成
        mock_result.approved_count = 2  # 执行前已有2个通过
        mock_result.rejected_count = 0

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        # Mock _summarize_eval_data
        with patch.object(executor, "_summarize_eval_data"):
            result, error = executor._process_countersign(mock_task, "APPROVE")

            assert result is True
            assert error is None
            assert mock_result.final_result == "PASSED"

    def test_process_countersign_all_rejected(self):
        """测试有驳回（通过规则：ALL）"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approver_config = {"pass_rule": "ALL"}

        mock_result = MagicMock()
        mock_result.pending_count = 1  # 还有1个待处理，执行后变成0，完成
        mock_result.approved_count = 2  # 执行前已有2个通过
        mock_result.rejected_count = 1  # 执行前已有1个驳回

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        with patch.object(executor, "_summarize_eval_data"):
            result, error = executor._process_countersign(mock_task, "APPROVE")

            assert result is True
            assert error is None
            assert mock_result.final_result == "FAILED"  # 有驳回，所以失败

    def test_process_countersign_majority_pass(self):
        """测试多数通过"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approver_config = {"pass_rule": "MAJORITY"}

        mock_result = MagicMock()
        mock_result.pending_count = 1  # 还有1个待处理，执行后变成0，完成
        mock_result.approved_count = 2  # 执行前已有2个通过
        mock_result.rejected_count = 1  # 执行前已有1个驳回

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        with patch.object(executor, "_summarize_eval_data"):
            result, error = executor._process_countersign(mock_task, "APPROVE")

            assert result is True
            assert error is None
            # 执行后：approved_count=3, rejected_count=1，3>1，所以通过
            assert mock_result.final_result == "PASSED"

    def test_process_countersign_any_pass(self):
        """测试任一通过"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approver_config = {"pass_rule": "ANY"}

        mock_result = MagicMock()
        mock_result.pending_count = 1  # 还有1个待处理，执行后变成0，完成
        mock_result.approved_count = 0  # 执行前没有通过
        mock_result.rejected_count = 3  # 执行前已有3个驳回

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        with patch.object(executor, "_summarize_eval_data"):
            result, error = executor._process_countersign(mock_task, "APPROVE")

            assert result is True
            assert error is None
            # 执行后：approved_count=1, rejected_count=3，approved_count>0，所以通过
            assert mock_result.final_result == "PASSED"

    def test_process_countersign_any_fail(self):
        """测试任一通过规则失败"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approver_config = {"pass_rule": "ANY"}

        mock_result = MagicMock()
        mock_result.pending_count = 1  # 还有1个待处理，执行后变成0，完成
        mock_result.approved_count = 0  # 执行前没有通过
        mock_result.rejected_count = 1  # 执行前已有1个驳回

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        with patch.object(executor, "_summarize_eval_data"):
            result, error = executor._process_countersign(mock_task, "REJECT")

            assert result is True
            assert error is None
            # 执行后：approved_count=0, rejected_count=2，approved_count=0，所以失败
            assert mock_result.final_result == "FAILED"

    def test_process_countersign_default_rule(self):
        """测试默认通过规则（ALL）"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.node.approver_config = None  # 无配置，使用默认

        mock_result = MagicMock()
        mock_result.pending_count = 1  # 还有1个待处理，执行后变成0，完成
        mock_result.approved_count = 1  # 执行前已有1个通过
        mock_result.rejected_count = 0  # 执行前没有驳回

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        with patch.object(executor, "_summarize_eval_data"):
            result, error = executor._process_countersign(mock_task, "APPROVE")

            assert result is True
            assert error is None
            # 执行后：approved_count=2, rejected_count=0，rejected_count=0，所以通过
            assert mock_result.final_result == "PASSED"


@pytest.mark.unit
class TestSummarizeEvalData:
    """测试 _summarize_eval_data 方法"""

    def test_summarize_eval_data_with_data(self):
        """测试汇总会签评估数据"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_result = MagicMock()
        mock_result.instance_id = 100
        mock_result.node_id = 5

        # Mock completed tasks
        mock_task1 = MagicMock()
        mock_task1.assignee_id = 1
        mock_task1.assignee_name = "User 1"
        mock_task1.action = "APPROVE"
        mock_task1.comment = "OK"
        mock_task1.eval_data = {
            "cost_estimate": 1000,
            "schedule_estimate": 5,
            "risk_assessment": "低",
        }

        mock_task2 = MagicMock()
        mock_task2.assignee_id = 2
        mock_task2.assignee_name = "User 2"
        mock_task2.action = "APPROVE"
        mock_task2.comment = "Good"
        mock_task2.eval_data = {
            "cost_estimate": 1200,
            "schedule_estimate": 6,
            "risk_assessment": "中",
        }

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_task1, mock_task2]
        mock_db.query.return_value = mock_query

        executor._summarize_eval_data(mock_result)

        assert mock_result.summary_data["total_cost"] == 2200
        assert mock_result.summary_data["total_schedule_days"] == 11
        assert mock_result.summary_data["max_risk"] == "中"
        assert len(mock_result.summary_data["evaluations"]) == 2

    def test_summarize_eval_data_without_eval_data(self):
        """测试任务没有评估数据"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_result = MagicMock()
        mock_result.instance_id = 100
        mock_result.node_id = 5

        mock_task = MagicMock()
        mock_task.assignee_id = 1
        mock_task.assignee_name = "User 1"
        mock_task.action = "APPROVE"
        mock_task.comment = "OK"
        mock_task.eval_data = None

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_task]
        mock_db.query.return_value = mock_query

        executor._summarize_eval_data(mock_result)

        assert mock_result.summary_data["total_cost"] == 0
        assert mock_result.summary_data["total_schedule_days"] == 0
        assert mock_result.summary_data["max_risk"] == "低"

    def test_summarize_eval_data_empty_tasks(self):
        """测试没有已完成的任务"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_result = MagicMock()
        mock_result.instance_id = 100
        mock_result.node_id = 5

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        executor._summarize_eval_data(mock_result)

        assert mock_result.summary_data["total_cost"] == 0
        assert mock_result.summary_data["total_schedule_days"] == 0
        assert mock_result.summary_data["max_risk"] == "低"
        assert mock_result.summary_data["evaluations"] == []


@pytest.mark.unit
class TestCancelPendingTasks:
    """测试 _cancel_pending_tasks 方法"""

    def test_cancel_pending_tasks_without_exclude(self):
        """测试取消所有待处理任务"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.update.return_value = None
        mock_db.query.return_value = mock_query

        executor._cancel_pending_tasks(instance_id=100, node_id=5)

        mock_db.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.filter.return_value.update.assert_called_once_with(
            {"status": "CANCELLED"}, synchronize_session=False
        )

    def test_cancel_pending_tasks_with_exclude(self):
        """测试取消待处理任务（排除指定任务）"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        # 创建链式调用的 mock
        mock_query = MagicMock()
        mock_filtered_query = MagicMock()  # 第一次 filter 后的结果
        mock_filtered_query2 = MagicMock()  # 第二次 filter 后的结果（如果有 exclude_task_id）
        mock_filtered_query2.update.return_value = None
        
        # 第一次 filter 返回 mock_filtered_query
        # 如果有 exclude_task_id，第二次 filter 返回 mock_filtered_query2
        mock_filtered_query.filter.return_value = mock_filtered_query2
        mock_query.filter.return_value = mock_filtered_query
        mock_db.query.return_value = mock_query

        executor._cancel_pending_tasks(instance_id=100, node_id=5, exclude_task_id=10)

        mock_db.query.assert_called_once()
        # 检查 filter 被调用（至少一次，如果有 exclude_task_id 则两次）
        assert mock_query.filter.call_count >= 1
        # 验证 update 被调用（在最终的 filtered query 上）
        mock_filtered_query2.update.assert_called_once_with(
            {"status": "CANCELLED"}, synchronize_session=False
        )


@pytest.mark.unit
class TestCountPendingTasks:
    """测试 _count_pending_tasks 方法"""

    def test_count_pending_tasks(self):
        """测试统计待处理任务数"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 3
        mock_db.query.return_value = mock_query

        result = executor._count_pending_tasks(instance_id=100, node_id=5)

        assert result == 3
        mock_db.query.assert_called_once()


@pytest.mark.unit
class TestActivateNextSequentialTask:
    """测试 _activate_next_sequential_task 方法"""

    def test_activate_next_sequential_task_found(self):
        """测试激活下一个依次审批任务"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_current_task = MagicMock()
        mock_current_task.instance_id = 100
        mock_current_task.node_id = 5
        mock_current_task.task_order = 1
        mock_current_task.node.timeout_hours = 24

        mock_next_task = MagicMock()
        mock_next_task.status = "SKIPPED"

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = (
            mock_next_task
        )
        mock_db.query.return_value = mock_query

        result = executor._activate_next_sequential_task(mock_current_task)

        assert result == mock_next_task
        assert mock_next_task.status == "PENDING"
        assert mock_next_task.due_at is not None

    def test_activate_next_sequential_task_not_found(self):
        """测试没有下一个任务"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_current_task = MagicMock()
        mock_current_task.instance_id = 100
        mock_current_task.node_id = 5
        mock_current_task.task_order = 3

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = executor._activate_next_sequential_task(mock_current_task)

        assert result is None


@pytest.mark.unit
class TestCreateCcRecords:
    """测试 create_cc_records 方法"""

    def test_create_cc_records_empty_list(self):
        """测试空抄送列表"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        result = executor.create_cc_records(
            instance=mock_instance, node_id=5, cc_user_ids=[]
        )

        assert result == []
        mock_db.add.assert_not_called()

    def test_create_cc_records_new_users(self):
        """测试添加新抄送用户"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = executor.create_cc_records(
            instance=mock_instance, node_id=5, cc_user_ids=[1, 2, 3]
        )

        assert len(result) == 3
        assert mock_db.add.call_count == 3
        mock_db.flush.assert_called_once()

    def test_create_cc_records_existing_user(self):
        """测试避免重复抄送"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        # 模拟第一个用户已存在
        mock_query = MagicMock()
        mock_query.filter.return_value.first.side_effect = [
            MagicMock(),  # 用户1已存在
            None,  # 用户2不存在
            None,  # 用户3不存在
        ]
        mock_db.query.return_value = mock_query

        result = executor.create_cc_records(
            instance=mock_instance, node_id=5, cc_user_ids=[1, 2, 3]
        )

        # 只应该添加2个新用户
        assert len(result) == 2
        assert mock_db.add.call_count == 2

    def test_create_cc_records_with_source(self):
        """测试指定抄送来源"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = executor.create_cc_records(
            instance=mock_instance,
            node_id=5,
            cc_user_ids=[1],
            cc_source="MANUAL",
            added_by=100,
        )

        assert len(result) == 1
        assert result[0].cc_source == "MANUAL"
        assert result[0].added_by == 100
        assert result[0].is_read is False


@pytest.mark.unit
class TestHandleTimeout:
    """测试 handle_timeout 方法"""

    def test_handle_timeout_invalid_status(self):
        """测试任务状态不正确"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "COMPLETED"

        action, error = executor.handle_timeout(mock_task)

        assert action == "NONE"
        assert "任务已不是待处理状态" in error

    def test_handle_timeout_remind(self):
        """测试催办提醒"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.node.timeout_action = "REMIND"
        mock_task.remind_count = 2

        action, error = executor.handle_timeout(mock_task)

        assert action == "REMIND"
        assert error is None
        assert mock_task.remind_count == 3
        assert isinstance(mock_task.reminded_at, datetime)

    def test_handle_timeout_auto_pass(self):
        """测试自动通过"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.node.timeout_action = "AUTO_PASS"

        action, error = executor.handle_timeout(mock_task)

        assert action == "AUTO_PASS"
        assert error is None
        assert mock_task.action == "APPROVE"
        assert "超时" in mock_task.comment
        assert mock_task.status == "COMPLETED"
        assert isinstance(mock_task.completed_at, datetime)

    def test_handle_timeout_auto_reject(self):
        """测试自动驳回"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.node.timeout_action = "AUTO_REJECT"

        action, error = executor.handle_timeout(mock_task)

        assert action == "AUTO_REJECT"
        assert error is None
        assert mock_task.action == "REJECT"
        assert "超时" in mock_task.comment
        assert mock_task.status == "COMPLETED"
        assert isinstance(mock_task.completed_at, datetime)

    def test_handle_timeout_escalate(self):
        """测试升级处理"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.node.timeout_action = "ESCALATE"

        action, error = executor.handle_timeout(mock_task)

        assert action == "ESCALATE"
        assert error is None
        assert mock_task.status == "EXPIRED"

    def test_handle_timeout_default(self):
        """测试默认处理(未知动作，timeout_action为未知值)"""
        mock_db = MagicMock()
        executor = ApprovalNodeExecutor(mock_db)

        mock_task = MagicMock()
        mock_task.status = "PENDING"
        mock_task.node.timeout_action = "UNKNOWN_ACTION"  # 未知动作，进入 else 分支

        action, error = executor.handle_timeout(mock_task)

        # 未知动作会进入 else 分支，返回 "EXPIRED"
        assert action == "EXPIRED"
        assert error is None
        assert mock_task.status == "EXPIRED"

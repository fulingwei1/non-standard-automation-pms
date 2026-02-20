# -*- coding: utf-8 -*-
"""
审批节点执行器增强测试
补充覆盖核心业务逻辑和异常场景,提升覆盖率到60%+
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from app.services.approval_engine.executor import ApprovalNodeExecutor


@pytest.fixture
def db_mock():
    """数据库mock"""
    return MagicMock()


@pytest.fixture
def executor(db_mock):
    """执行器实例"""
    return ApprovalNodeExecutor(db_mock)


@pytest.fixture
def sample_instance():
    """示例审批实例"""
    instance = MagicMock()
    instance.id = 50
    instance.template_id = 5
    instance.status = "PENDING"
    instance.title = "测试审批"
    return instance


@pytest.fixture
def sample_node():
    """示例审批节点"""
    node = MagicMock()
    node.id = 10
    node.flow_id = 2
    node.node_name = "部门审批"
    node.node_order = 1
    node.node_type = "APPROVAL"
    node.approval_mode = "SINGLE"
    node.approver_type = "FIXED_USER"
    node.approver_config = {}
    node.timeout_hours = 48
    node.timeout_action = "REMIND"
    node.can_transfer = True
    node.can_add_approver = True
    return node


@pytest.fixture
def sample_task():
    """示例审批任务"""
    task = MagicMock()
    task.id = 100
    task.instance_id = 50
    task.node_id = 10
    task.status = "PENDING"
    task.action = None
    task.comment = None
    task.completed_at = None
    task.assignee_id = 200
    
    task.node = MagicMock()
    task.node.id = 10
    task.node.approval_mode = "SINGLE"
    task.node.approver_config = {}
    task.node.timeout_action = "REMIND"
    
    task.instance = MagicMock()
    task.instance.id = 50
    task.instance.entity = MagicMock()
    task.instance.entity_id = 1
    
    return task


class TestCreateTasksForNode:
    """测试为节点创建任务"""
    
    def test_create_tasks_single_mode(self, executor, db_mock, sample_instance, sample_node):
        """测试单人审批模式"""
        sample_node.approval_mode = "SINGLE"
        approver_ids = [100]
        
        tasks = executor.create_tasks_for_node(sample_instance, sample_node, approver_ids)
        
        assert len(tasks) == 1
        assert tasks[0].assignee_id == 100
        assert tasks[0].status == "PENDING"
        assert tasks[0].is_countersign is False
        db_mock.add.assert_called_once()
        db_mock.flush.assert_called_once()
    
    def test_create_tasks_or_sign_mode(self, executor, db_mock, sample_instance, sample_node):
        """测试或签模式"""
        sample_node.approval_mode = "OR_SIGN"
        approver_ids = [100, 200, 300]
        
        tasks = executor.create_tasks_for_node(sample_instance, sample_node, approver_ids)
        
        assert len(tasks) == 3
        for task in tasks:
            assert task.status == "PENDING"
            assert task.is_countersign is False
    
    def test_create_tasks_and_sign_mode(self, executor, db_mock, sample_instance, sample_node):
        """测试会签模式"""
        sample_node.approval_mode = "AND_SIGN"
        approver_ids = [100, 200, 300]
        
        tasks = executor.create_tasks_for_node(sample_instance, sample_node, approver_ids)
        
        assert len(tasks) == 3
        for task in tasks:
            assert task.status == "PENDING"
            assert task.is_countersign is True
        # 验证创建了会签结果记录
        assert db_mock.add.call_count == 4  # 3个任务 + 1个会签结果
    
    def test_create_tasks_sequential_mode(self, executor, db_mock, sample_instance, sample_node):
        """测试依次审批模式"""
        sample_node.approval_mode = "SEQUENTIAL"
        approver_ids = [100, 200, 300]
        
        tasks = executor.create_tasks_for_node(sample_instance, sample_node, approver_ids)
        
        assert len(tasks) == 3
        assert tasks[0].status == "PENDING"
        assert tasks[1].status == "SKIPPED"
        assert tasks[2].status == "SKIPPED"
    
    def test_create_tasks_empty_approvers(self, executor, db_mock, sample_instance, sample_node):
        """测试空审批人列表"""
        tasks = executor.create_tasks_for_node(sample_instance, sample_node, [])
        
        assert len(tasks) == 0
    
    def test_create_tasks_with_timeout(self, executor, db_mock, sample_instance, sample_node):
        """测试设置超时时间"""
        sample_node.timeout_hours = 24
        approver_ids = [100]
        
        tasks = executor.create_tasks_for_node(sample_instance, sample_node, approver_ids)
        
        assert tasks[0].due_at is not None


class TestProcessApproval:
    """测试处理审批操作"""
    
    def test_process_approval_single_mode_approve(self, executor, db_mock, sample_task):
        """测试单人审批通过"""
        sample_task.node.approval_mode = "SINGLE"
        
        can_proceed, error = executor.process_approval(
            task=sample_task,
            action="APPROVE",
            comment="同意",
            attachments=[],
            eval_data=None
        )
        
        assert can_proceed is True
        assert error is None
        assert sample_task.action == "APPROVE"
        assert sample_task.comment == "同意"
        assert sample_task.status == "COMPLETED"
        assert sample_task.completed_at is not None
    
    def test_process_approval_invalid_status(self, executor, db_mock, sample_task):
        """测试任务状态不正确"""
        sample_task.status = "COMPLETED"
        
        can_proceed, error = executor.process_approval(
            task=sample_task,
            action="APPROVE",
            comment="同意"
        )
        
        assert can_proceed is False
        assert "状态不正确" in error
    
    def test_process_approval_or_sign_approve(self, executor, db_mock, sample_task):
        """测试或签通过"""
        sample_task.node.approval_mode = "OR_SIGN"
        
        with patch.object(executor, '_cancel_pending_tasks'):
            can_proceed, error = executor.process_approval(
                task=sample_task,
                action="APPROVE",
                comment="同意"
            )
        
        assert can_proceed is True
        executor._cancel_pending_tasks.assert_called_once()
    
    def test_process_approval_or_sign_reject_last_one(self, executor, db_mock, sample_task):
        """测试或签最后一个驳回"""
        sample_task.node.approval_mode = "OR_SIGN"
        
        with patch.object(executor, '_count_pending_tasks', return_value=0):
            can_proceed, error = executor.process_approval(
                task=sample_task,
                action="REJECT",
                comment="不同意"
            )
        
        assert can_proceed is True  # 全部驳回,可以流转
    
    def test_process_approval_or_sign_reject_not_last(self, executor, db_mock, sample_task):
        """测试或签非最后一个驳回"""
        sample_task.node.approval_mode = "OR_SIGN"
        
        with patch.object(executor, '_count_pending_tasks', return_value=2):
            can_proceed, error = executor.process_approval(
                task=sample_task,
                action="REJECT",
                comment="不同意"
            )
        
        assert can_proceed is False  # 还有待处理任务
    
    def test_process_approval_sequential_reject(self, executor, db_mock, sample_task):
        """测试依次审批驳回"""
        sample_task.node.approval_mode = "SEQUENTIAL"
        
        can_proceed, error = executor.process_approval(
            task=sample_task,
            action="REJECT",
            comment="不同意"
        )
        
        assert can_proceed is True
    
    def test_process_approval_sequential_approve_has_next(self, executor, db_mock, sample_task):
        """测试依次审批通过且有下一个"""
        sample_task.node.approval_mode = "SEQUENTIAL"
        next_task = MagicMock()
        
        with patch.object(executor, '_activate_next_sequential_task', return_value=next_task):
            can_proceed, error = executor.process_approval(
                task=sample_task,
                action="APPROVE",
                comment="同意"
            )
        
        assert can_proceed is False  # 还有后续任务
    
    def test_process_approval_sequential_approve_no_next(self, executor, db_mock, sample_task):
        """测试依次审批通过且无下一个"""
        sample_task.node.approval_mode = "SEQUENTIAL"
        
        with patch.object(executor, '_activate_next_sequential_task', return_value=None):
            can_proceed, error = executor.process_approval(
                task=sample_task,
                action="APPROVE",
                comment="同意"
            )
        
        assert can_proceed is True  # 所有人都通过了


class TestProcessCountersign:
    """测试处理会签"""
    
    def test_process_countersign_all_pass_rule(self, executor, db_mock, sample_task):
        """测试全部通过规则"""
        result = MagicMock()
        result.pending_count = 1
        result.approved_count = 2
        result.rejected_count = 0
        result.total_count = 3
        
        sample_task.node.approver_config = {"pass_rule": "ALL"}
        
        db_mock.query.return_value.filter.return_value.first.return_value = result
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        can_proceed, error = executor._process_countersign(sample_task, "APPROVE")
        
        assert can_proceed is True
        assert result.pending_count == 0
        assert result.approved_count == 3
        assert result.final_result == "PASSED"
    
    def test_process_countersign_all_rule_has_reject(self, executor, db_mock, sample_task):
        """测试全部通过规则但有驳回"""
        result = MagicMock()
        result.pending_count = 1
        result.approved_count = 1
        result.rejected_count = 1
        result.total_count = 3
        
        sample_task.node.approver_config = {"pass_rule": "ALL"}
        
        db_mock.query.return_value.filter.return_value.first.return_value = result
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        can_proceed, error = executor._process_countersign(sample_task, "APPROVE")
        
        assert can_proceed is True
        assert result.pending_count == 0
        assert result.final_result == "FAILED"
    
    def test_process_countersign_majority_rule(self, executor, db_mock, sample_task):
        """测试多数通过规则"""
        result = MagicMock()
        result.pending_count = 1
        result.approved_count = 2
        result.rejected_count = 1
        result.total_count = 4
        
        sample_task.node.approver_config = {"pass_rule": "MAJORITY"}
        
        db_mock.query.return_value.filter.return_value.first.return_value = result
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        can_proceed, error = executor._process_countersign(sample_task, "APPROVE")
        
        assert can_proceed is True
        assert result.final_result == "PASSED"  # 3 > 1
    
    def test_process_countersign_any_rule(self, executor, db_mock, sample_task):
        """测试任一通过规则"""
        result = MagicMock()
        result.pending_count = 1
        result.approved_count = 1
        result.rejected_count = 1
        result.total_count = 3
        
        sample_task.node.approver_config = {"pass_rule": "ANY"}
        
        db_mock.query.return_value.filter.return_value.first.return_value = result
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        can_proceed, error = executor._process_countersign(sample_task, "APPROVE")
        
        assert can_proceed is True
        assert result.final_result == "PASSED"
    
    def test_process_countersign_result_not_found(self, executor, db_mock, sample_task):
        """测试会签结果记录不存在"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        can_proceed, error = executor._process_countersign(sample_task, "APPROVE")
        
        assert can_proceed is False
        assert error == "会签结果记录不存在"
    
    def test_process_countersign_still_pending(self, executor, db_mock, sample_task):
        """测试还有待处理的会签"""
        result = MagicMock()
        result.pending_count = 2
        result.approved_count = 1
        result.rejected_count = 0
        
        db_mock.query.return_value.filter.return_value.first.return_value = result
        
        can_proceed, error = executor._process_countersign(sample_task, "APPROVE")
        
        assert can_proceed is False
        assert result.pending_count == 1


class TestSummarizeEvalData:
    """测试汇总评估数据"""
    
    def test_summarize_eval_data(self, executor, db_mock):
        """测试汇总评估数据"""
        result = MagicMock()
        result.instance_id = 50
        result.node_id = 10
        result.summary_data = None
        
        # Mock任务列表
        task1 = MagicMock()
        task1.assignee_id = 100
        task1.assignee_name = "张三"
        task1.action = "APPROVE"
        task1.comment = "同意"
        task1.eval_data = {
            "cost_estimate": 3000.0,
            "schedule_estimate": 2,
            "risk_assessment": "中"
        }
        
        task2 = MagicMock()
        task2.assignee_id = 200
        task2.assignee_name = "李四"
        task2.action = "APPROVE"
        task2.comment = "同意"
        task2.eval_data = {
            "cost_estimate": 2000.0,
            "schedule_estimate": 1,
            "risk_assessment": "高"
        }
        
        db_mock.query.return_value.filter.return_value.all.return_value = [task1, task2]
        
        executor._summarize_eval_data(result)
        
        assert result.summary_data["total_cost"] == 5000.0
        assert result.summary_data["total_schedule_days"] == 3
        assert result.summary_data["max_risk"] == "高"
        assert len(result.summary_data["evaluations"]) == 2


class TestCancelPendingTasks:
    """测试取消待处理任务"""
    
    def test_cancel_pending_tasks(self, executor, db_mock):
        """测试取消其他待处理任务"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 2
        db_mock.query.return_value = mock_query
        
        executor._cancel_pending_tasks(instance_id=50, node_id=10, exclude_task_id=100)
        
        mock_query.update.assert_called_once_with(
            {"status": "CANCELLED"},
            synchronize_session=False
        )


class TestActivateNextSequentialTask:
    """测试激活下一个依次审批任务"""
    
    def test_activate_next_sequential_task_found(self, executor, db_mock, sample_task):
        """测试找到下一个任务"""
        next_task = MagicMock()
        next_task.status = "SKIPPED"
        next_task.due_at = None
        
        sample_task.node.timeout_hours = 24
        
        db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = next_task
        
        result = executor._activate_next_sequential_task(sample_task)
        
        assert result == next_task
        assert next_task.status == "PENDING"
        assert next_task.due_at is not None
    
    def test_activate_next_sequential_task_not_found(self, executor, db_mock, sample_task):
        """测试没有下一个任务"""
        db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = executor._activate_next_sequential_task(sample_task)
        
        assert result is None


class TestCreateCcRecords:
    """测试创建抄送记录"""
    
    def test_create_cc_records(self, executor, db_mock, sample_instance):
        """测试创建抄送记录"""
        db_mock.query.return_value.filter.return_value.first.return_value = None  # 无重复
        
        records = executor.create_cc_records(
            instance=sample_instance,
            node_id=10,
            cc_user_ids=[100, 200, 300],
            cc_source="FLOW",
            added_by=50
        )
        
        assert len(records) == 3
        for record in records:
            assert record.instance_id == 50
            assert record.is_read is False
        db_mock.flush.assert_called_once()
    
    def test_create_cc_records_skip_duplicates(self, executor, db_mock, sample_instance):
        """测试跳过重复抄送"""
        existing = MagicMock()
        db_mock.query.return_value.filter.return_value.first.return_value = existing
        
        records = executor.create_cc_records(
            instance=sample_instance,
            node_id=10,
            cc_user_ids=[100],
            cc_source="FLOW"
        )
        
        assert len(records) == 0


class TestHandleTimeout:
    """测试处理超时"""
    
    def test_handle_timeout_remind(self, executor, db_mock, sample_task):
        """测试催办提醒"""
        sample_task.node.timeout_action = "REMIND"
        sample_task.remind_count = 0
        
        action, error = executor.handle_timeout(sample_task)
        
        assert action == "REMIND"
        assert error is None
        assert sample_task.remind_count == 1
        assert sample_task.reminded_at is not None
    
    def test_handle_timeout_auto_pass(self, executor, db_mock, sample_task):
        """测试自动通过"""
        sample_task.node.timeout_action = "AUTO_PASS"
        
        action, error = executor.handle_timeout(sample_task)
        
        assert action == "AUTO_PASS"
        assert sample_task.action == "APPROVE"
        assert sample_task.status == "COMPLETED"
        assert "系统自动通过（超时）" in sample_task.comment
    
    def test_handle_timeout_auto_reject(self, executor, db_mock, sample_task):
        """测试自动驳回"""
        sample_task.node.timeout_action = "AUTO_REJECT"
        
        action, error = executor.handle_timeout(sample_task)
        
        assert action == "AUTO_REJECT"
        assert sample_task.action == "REJECT"
        assert sample_task.status == "COMPLETED"
        assert "系统自动驳回（超时）" in sample_task.comment
    
    def test_handle_timeout_escalate(self, executor, db_mock, sample_task):
        """测试升级处理"""
        sample_task.node.timeout_action = "ESCALATE"
        
        action, error = executor.handle_timeout(sample_task)
        
        assert action == "ESCALATE"
        assert sample_task.status == "EXPIRED"
    
    def test_handle_timeout_invalid_status(self, executor, db_mock, sample_task):
        """测试任务状态不正确"""
        sample_task.status = "COMPLETED"
        
        action, error = executor.handle_timeout(sample_task)
        
        assert action == "NONE"
        assert "已不是待处理状态" in error

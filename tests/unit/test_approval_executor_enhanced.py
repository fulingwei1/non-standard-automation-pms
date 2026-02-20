# -*- coding: utf-8 -*-
"""
审批节点执行器增强测试套件

覆盖 ApprovalNodeExecutor 的所有核心方法和边界条件
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch, PropertyMock

from app.models.approval import (
    ApprovalCarbonCopy,
    ApprovalCountersignResult,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
)
from app.services.approval_engine.executor import ApprovalNodeExecutor


class TestApprovalNodeExecutor(unittest.TestCase):
    """ApprovalNodeExecutor 测试类"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.db)
        
        # Mock 实例
        self.mock_instance = MagicMock(spec=ApprovalInstance)
        self.mock_instance.id = 1
        
        # Mock 节点
        self.mock_node = MagicMock(spec=ApprovalNodeDefinition)
        self.mock_node.id = 10
        self.mock_node.timeout_hours = 24
        self.mock_node.approver_config = {}

    def tearDown(self):
        """测试后清理"""
        self.db.reset_mock()

    # ==================== create_tasks_for_node 测试 ====================

    def test_create_tasks_empty_approvers(self):
        """测试空审批人列表"""
        self.mock_node.approval_mode = "SINGLE"
        tasks = self.executor.create_tasks_for_node(
            self.mock_instance, self.mock_node, []
        )
        self.assertEqual(tasks, [])
        self.db.add.assert_not_called()

    def test_create_tasks_single_mode(self):
        """测试单人审批模式"""
        self.mock_node.approval_mode = "SINGLE"
        tasks = self.executor.create_tasks_for_node(
            self.mock_instance, self.mock_node, [101]
        )
        
        self.assertEqual(len(tasks), 1)
        self.db.add.assert_called_once()
        
        task = tasks[0]
        self.assertEqual(task.instance_id, 1)
        self.assertEqual(task.node_id, 10)
        self.assertEqual(task.assignee_id, 101)
        self.assertEqual(task.status, "PENDING")
        self.assertEqual(task.is_countersign, False)

    def test_create_tasks_or_sign_mode(self):
        """测试或签模式 - 多个审批人"""
        self.mock_node.approval_mode = "OR_SIGN"
        approver_ids = [101, 102, 103]
        
        tasks = self.executor.create_tasks_for_node(
            self.mock_instance, self.mock_node, approver_ids
        )
        
        self.assertEqual(len(tasks), 3)
        self.assertEqual(self.db.add.call_count, 3)
        
        for idx, task in enumerate(tasks):
            self.assertEqual(task.assignee_id, approver_ids[idx])
            self.assertEqual(task.status, "PENDING")
            self.assertEqual(task.task_order, idx + 1)

    def test_create_tasks_and_sign_mode(self):
        """测试会签模式 - 创建会签结果记录"""
        self.mock_node.approval_mode = "AND_SIGN"
        approver_ids = [101, 102]
        
        tasks = self.executor.create_tasks_for_node(
            self.mock_instance, self.mock_node, approver_ids
        )
        
        self.assertEqual(len(tasks), 2)
        # 2个任务 + 1个会签结果记录
        self.assertEqual(self.db.add.call_count, 3)
        
        for task in tasks:
            self.assertEqual(task.is_countersign, True)
            self.assertEqual(task.status, "PENDING")

    def test_create_tasks_sequential_mode(self):
        """测试依次审批模式 - 只有第一个是PENDING"""
        self.mock_node.approval_mode = "SEQUENTIAL"
        approver_ids = [101, 102, 103]
        
        tasks = self.executor.create_tasks_for_node(
            self.mock_instance, self.mock_node, approver_ids
        )
        
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].status, "PENDING")
        self.assertEqual(tasks[1].status, "SKIPPED")
        self.assertEqual(tasks[2].status, "SKIPPED")
        
        # 只有第一个任务有截止时间
        self.assertIsNotNone(tasks[0].due_at)
        self.assertIsNone(tasks[1].due_at)

    def test_create_tasks_with_timeout(self):
        """测试带超时设置的任务创建"""
        self.mock_node.approval_mode = "SINGLE"
        self.mock_node.timeout_hours = 48
        
        with patch('app.services.approval_engine.executor.datetime') as mock_datetime:
            mock_now = datetime(2026, 2, 21, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            tasks = self.executor.create_tasks_for_node(
                self.mock_instance, self.mock_node, [101]
            )
            
            expected_due = mock_now + timedelta(hours=48)
            self.assertEqual(tasks[0].due_at, expected_due)

    def test_create_tasks_no_timeout(self):
        """测试无超时设置"""
        self.mock_node.approval_mode = "SINGLE"
        self.mock_node.timeout_hours = None
        
        tasks = self.executor.create_tasks_for_node(
            self.mock_instance, self.mock_node, [101]
        )
        
        self.assertIsNone(tasks[0].due_at)

    # ==================== process_approval 测试 ====================

    def test_process_approval_invalid_status(self):
        """测试处理非PENDING状态的任务"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.status = "COMPLETED"
        
        can_proceed, error = self.executor.process_approval(
            mock_task, "APPROVE"
        )
        
        self.assertFalse(can_proceed)
        self.assertIn("任务状态不正确", error)

    def test_process_approval_single_mode_approve(self):
        """测试单人审批通过"""
        mock_task = self._create_mock_task("SINGLE")
        
        with patch('app.services.approval_engine.executor.datetime') as mock_datetime:
            mock_now = datetime(2026, 2, 21, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            can_proceed, error = self.executor.process_approval(
                mock_task, "APPROVE", "同意"
            )
            
            self.assertTrue(can_proceed)
            self.assertIsNone(error)
            self.assertEqual(mock_task.action, "APPROVE")
            self.assertEqual(mock_task.comment, "同意")
            self.assertEqual(mock_task.status, "COMPLETED")
            self.assertEqual(mock_task.completed_at, mock_now)

    def test_process_approval_or_sign_first_approve(self):
        """测试或签模式 - 第一个人通过"""
        mock_task = self._create_mock_task("OR_SIGN")
        
        with patch.object(self.executor, '_cancel_pending_tasks') as mock_cancel:
            can_proceed, error = self.executor.process_approval(
                mock_task, "APPROVE"
            )
            
            self.assertTrue(can_proceed)
            self.assertIsNone(error)
            mock_cancel.assert_called_once_with(
                mock_task.instance_id, 
                mock_task.node_id, 
                exclude_task_id=mock_task.id
            )

    def test_process_approval_or_sign_reject_with_pending(self):
        """测试或签模式 - 驳回但还有其他待处理任务"""
        mock_task = self._create_mock_task("OR_SIGN")
        
        with patch.object(self.executor, '_count_pending_tasks', return_value=2):
            can_proceed, error = self.executor.process_approval(
                mock_task, "REJECT"
            )
            
            self.assertFalse(can_proceed)
            self.assertIsNone(error)

    def test_process_approval_or_sign_all_rejected(self):
        """测试或签模式 - 所有人都驳回"""
        mock_task = self._create_mock_task("OR_SIGN")
        
        with patch.object(self.executor, '_count_pending_tasks', return_value=0):
            can_proceed, error = self.executor.process_approval(
                mock_task, "REJECT"
            )
            
            self.assertTrue(can_proceed)
            self.assertIsNone(error)

    def test_process_approval_sequential_approve(self):
        """测试依次审批 - 通过并激活下一个"""
        mock_task = self._create_mock_task("SEQUENTIAL")
        mock_next_task = MagicMock(spec=ApprovalTask)
        
        with patch.object(self.executor, '_activate_next_sequential_task', return_value=mock_next_task):
            can_proceed, error = self.executor.process_approval(
                mock_task, "APPROVE"
            )
            
            self.assertFalse(can_proceed)  # 还有后续任务
            self.assertIsNone(error)

    def test_process_approval_sequential_last_approve(self):
        """测试依次审批 - 最后一个人通过"""
        mock_task = self._create_mock_task("SEQUENTIAL")
        
        with patch.object(self.executor, '_activate_next_sequential_task', return_value=None):
            can_proceed, error = self.executor.process_approval(
                mock_task, "APPROVE"
            )
            
            self.assertTrue(can_proceed)  # 所有人都已通过
            self.assertIsNone(error)

    def test_process_approval_sequential_reject(self):
        """测试依次审批 - 驳回直接结束"""
        mock_task = self._create_mock_task("SEQUENTIAL")
        
        can_proceed, error = self.executor.process_approval(
            mock_task, "REJECT"
        )
        
        self.assertTrue(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_with_attachments(self):
        """测试带附件的审批"""
        mock_task = self._create_mock_task("SINGLE")
        attachments = [{"name": "file.pdf", "url": "http://example.com/file.pdf"}]
        
        can_proceed, error = self.executor.process_approval(
            mock_task, "APPROVE", attachments=attachments
        )
        
        self.assertTrue(can_proceed)
        self.assertEqual(mock_task.attachments, attachments)

    def test_process_approval_with_eval_data(self):
        """测试带评估数据的审批（ECN场景）"""
        mock_task = self._create_mock_task("SINGLE")
        eval_data = {
            "cost_estimate": 5000,
            "schedule_estimate": 10,
            "risk_assessment": "中"
        }
        
        can_proceed, error = self.executor.process_approval(
            mock_task, "APPROVE", eval_data=eval_data
        )
        
        self.assertTrue(can_proceed)
        self.assertEqual(mock_task.eval_data, eval_data)

    # ==================== _process_countersign 测试 ====================

    def test_process_countersign_no_result_record(self):
        """测试会签处理 - 结果记录不存在"""
        mock_task = self._create_mock_task("AND_SIGN")
        
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        can_proceed, error = self.executor._process_countersign(
            mock_task, "APPROVE"
        )
        
        self.assertFalse(can_proceed)
        self.assertEqual(error, "会签结果记录不存在")

    def test_process_countersign_approve_not_complete(self):
        """测试会签 - 通过但未全部完成"""
        mock_task = self._create_mock_task("AND_SIGN")
        mock_result = self._create_mock_countersign_result(3, 1, 0, 2)
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_result
        
        can_proceed, error = self.executor._process_countersign(
            mock_task, "APPROVE"
        )
        
        self.assertFalse(can_proceed)
        self.assertIsNone(error)
        self.assertEqual(mock_result.approved_count, 2)
        self.assertEqual(mock_result.pending_count, 1)

    def test_process_countersign_all_approved(self):
        """测试会签 - 全部通过（默认规则）"""
        mock_task = self._create_mock_task("AND_SIGN")
        mock_result = self._create_mock_countersign_result(3, 2, 0, 1)
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_result
        
        with patch.object(self.executor, '_summarize_eval_data'):
            can_proceed, error = self.executor._process_countersign(
                mock_task, "APPROVE"
            )
            
            self.assertTrue(can_proceed)
            self.assertIsNone(error)
            self.assertEqual(mock_result.approved_count, 3)
            self.assertEqual(mock_result.pending_count, 0)
            self.assertEqual(mock_result.final_result, "PASSED")

    def test_process_countersign_one_rejected(self):
        """测试会签 - 有人驳回（ALL规则失败）"""
        mock_task = self._create_mock_task("AND_SIGN")
        mock_result = self._create_mock_countersign_result(3, 2, 0, 1)
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_result
        
        with patch.object(self.executor, '_summarize_eval_data'):
            can_proceed, error = self.executor._process_countersign(
                mock_task, "REJECT"
            )
            
            self.assertTrue(can_proceed)
            self.assertEqual(mock_result.rejected_count, 1)
            self.assertEqual(mock_result.final_result, "FAILED")

    def test_process_countersign_majority_rule(self):
        """测试会签 - 多数通过规则"""
        mock_task = self._create_mock_task("AND_SIGN")
        mock_task.node.approver_config = {"pass_rule": "MAJORITY"}
        mock_result = self._create_mock_countersign_result(5, 2, 2, 1)
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_result
        
        with patch.object(self.executor, '_summarize_eval_data'):
            can_proceed, error = self.executor._process_countersign(
                mock_task, "APPROVE"
            )
            
            self.assertTrue(can_proceed)
            self.assertEqual(mock_result.approved_count, 3)
            self.assertEqual(mock_result.rejected_count, 2)
            self.assertEqual(mock_result.final_result, "PASSED")

    def test_process_countersign_any_rule(self):
        """测试会签 - 任一通过规则"""
        mock_task = self._create_mock_task("AND_SIGN")
        mock_task.node.approver_config = {"pass_rule": "ANY"}
        mock_result = self._create_mock_countersign_result(3, 0, 2, 1)
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_result
        
        with patch.object(self.executor, '_summarize_eval_data'):
            can_proceed, error = self.executor._process_countersign(
                mock_task, "APPROVE"
            )
            
            self.assertTrue(can_proceed)
            self.assertEqual(mock_result.final_result, "PASSED")

    # ==================== _summarize_eval_data 测试 ====================

    def test_summarize_eval_data_no_tasks(self):
        """测试汇总评估数据 - 无任务"""
        mock_result = self._create_mock_countersign_result(0, 0, 0, 0)
        
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        self.executor._summarize_eval_data(mock_result)
        
        # 即使没有任务，也会生成空的汇总数据
        self.assertIsNotNone(mock_result.summary_data)
        self.assertEqual(mock_result.summary_data["total_cost"], 0)
        self.assertEqual(mock_result.summary_data["total_schedule_days"], 0)
        self.assertEqual(mock_result.summary_data["evaluations"], [])

    def test_summarize_eval_data_with_evaluations(self):
        """测试汇总评估数据 - 有评估数据"""
        mock_result = self._create_mock_countersign_result(3, 3, 0, 0)
        
        mock_tasks = [
            self._create_task_with_eval(101, "APPROVE", 5000, 10, "中"),
            self._create_task_with_eval(102, "APPROVE", 3000, 7, "低"),
            self._create_task_with_eval(103, "APPROVE", 2000, 5, "高"),
        ]
        
        self.db.query.return_value.filter.return_value.all.return_value = mock_tasks
        
        self.executor._summarize_eval_data(mock_result)
        
        summary = mock_result.summary_data
        self.assertEqual(summary["total_cost"], 10000)
        self.assertEqual(summary["total_schedule_days"], 22)
        self.assertEqual(summary["max_risk"], "高")
        self.assertEqual(len(summary["evaluations"]), 3)

    def test_summarize_eval_data_none_values(self):
        """测试汇总评估数据 - 包含None值"""
        mock_result = self._create_mock_countersign_result(2, 2, 0, 0)
        
        mock_task1 = self._create_task_with_eval(101, "APPROVE", None, 10, "中")
        mock_task2 = self._create_task_with_eval(102, "APPROVE", 5000, None, "低")
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_task1, mock_task2]
        
        self.executor._summarize_eval_data(mock_result)
        
        summary = mock_result.summary_data
        self.assertEqual(summary["total_cost"], 5000)
        self.assertEqual(summary["total_schedule_days"], 10)

    # ==================== _cancel_pending_tasks 测试 ====================

    def test_cancel_pending_tasks(self):
        """测试取消待处理任务"""
        mock_filter = MagicMock()
        mock_query = MagicMock()
        self.db.query.return_value.filter.return_value.filter.return_value = mock_filter
        
        self.executor._cancel_pending_tasks(1, 10, exclude_task_id=5)
        
        mock_filter.update.assert_called_once_with(
            {"status": "CANCELLED"}, 
            synchronize_session=False
        )

    def test_cancel_pending_tasks_no_exclude(self):
        """测试取消所有待处理任务（无排除）"""
        mock_query = MagicMock()
        self.db.query.return_value.filter.return_value = mock_query
        
        self.executor._cancel_pending_tasks(1, 10)
        
        # 验证没有调用exclude过滤
        self.assertTrue(mock_query.update.called)

    # ==================== _count_pending_tasks 测试 ====================

    def test_count_pending_tasks(self):
        """测试统计待处理任务数"""
        self.db.query.return_value.filter.return_value.count.return_value = 3
        
        count = self.executor._count_pending_tasks(1, 10)
        
        self.assertEqual(count, 3)

    def test_count_pending_tasks_zero(self):
        """测试统计待处理任务数 - 为0"""
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        count = self.executor._count_pending_tasks(1, 10)
        
        self.assertEqual(count, 0)

    # ==================== _activate_next_sequential_task 测试 ====================

    def test_activate_next_sequential_task_exists(self):
        """测试激活下一个任务 - 存在"""
        mock_current = MagicMock(spec=ApprovalTask)
        mock_current.instance_id = 1
        mock_current.node_id = 10
        mock_current.task_order = 1
        mock_current.node.timeout_hours = 24
        
        mock_next = MagicMock(spec=ApprovalTask)
        mock_next.status = "SKIPPED"
        
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_next
        
        with patch('app.services.approval_engine.executor.datetime') as mock_datetime:
            mock_now = datetime(2026, 2, 21, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            result = self.executor._activate_next_sequential_task(mock_current)
            
            self.assertIsNotNone(result)
            self.assertEqual(mock_next.status, "PENDING")
            self.assertIsNotNone(mock_next.due_at)

    def test_activate_next_sequential_task_not_exists(self):
        """测试激活下一个任务 - 不存在"""
        mock_current = MagicMock(spec=ApprovalTask)
        
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = self.executor._activate_next_sequential_task(mock_current)
        
        self.assertIsNone(result)

    def test_activate_next_sequential_task_no_timeout(self):
        """测试激活下一个任务 - 无超时设置"""
        mock_current = MagicMock(spec=ApprovalTask)
        mock_current.node.timeout_hours = None
        
        mock_next = MagicMock(spec=ApprovalTask)
        
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_next
        
        result = self.executor._activate_next_sequential_task(mock_current)
        
        self.assertIsNotNone(result)
        # due_at 不应该被设置（保持原值）

    # ==================== create_cc_records 测试 ====================

    def test_create_cc_records_new_users(self):
        """测试创建抄送记录 - 新用户"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        records = self.executor.create_cc_records(
            self.mock_instance, 10, [201, 202], "FLOW", 100
        )
        
        self.assertEqual(len(records), 2)
        self.assertEqual(self.db.add.call_count, 2)
        
        for record in records:
            self.assertEqual(record.instance_id, 1)
            self.assertEqual(record.node_id, 10)
            self.assertEqual(record.cc_source, "FLOW")
            self.assertEqual(record.added_by, 100)
            self.assertFalse(record.is_read)

    def test_create_cc_records_duplicate_skip(self):
        """测试创建抄送记录 - 跳过重复"""
        mock_existing = MagicMock(spec=ApprovalCarbonCopy)
        self.db.query.return_value.filter.return_value.first.return_value = mock_existing
        
        records = self.executor.create_cc_records(
            self.mock_instance, 10, [201], "FLOW"
        )
        
        self.assertEqual(len(records), 0)
        self.db.add.assert_not_called()

    def test_create_cc_records_mixed(self):
        """测试创建抄送记录 - 部分重复"""
        def side_effect(*args, **kwargs):
            # 第一次查询返回已存在的记录，第二次返回None
            if not hasattr(side_effect, 'call_count'):
                side_effect.call_count = 0
            side_effect.call_count += 1
            
            if side_effect.call_count == 1:
                return MagicMock(spec=ApprovalCarbonCopy)
            return None
        
        self.db.query.return_value.filter.return_value.first.side_effect = side_effect
        
        records = self.executor.create_cc_records(
            self.mock_instance, 10, [201, 202], "MANUAL", 100
        )
        
        self.assertEqual(len(records), 1)
        self.db.add.assert_called_once()

    # ==================== handle_timeout 测试 ====================

    def test_handle_timeout_not_pending(self):
        """测试处理超时 - 任务非待处理状态"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.status = "COMPLETED"
        
        action, error = self.executor.handle_timeout(mock_task)
        
        self.assertEqual(action, "NONE")
        self.assertIn("任务已不是待处理状态", error)

    def test_handle_timeout_remind(self):
        """测试超时处理 - 催办提醒"""
        mock_task = self._create_mock_task("SINGLE")
        mock_task.node.timeout_action = "REMIND"
        mock_task.remind_count = 0
        
        with patch('app.services.approval_engine.executor.datetime') as mock_datetime:
            mock_now = datetime(2026, 2, 21, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            action, error = self.executor.handle_timeout(mock_task)
            
            self.assertEqual(action, "REMIND")
            self.assertIsNone(error)
            self.assertEqual(mock_task.remind_count, 1)
            self.assertEqual(mock_task.reminded_at, mock_now)

    def test_handle_timeout_auto_pass(self):
        """测试超时处理 - 自动通过"""
        mock_task = self._create_mock_task("SINGLE")
        mock_task.node.timeout_action = "AUTO_PASS"
        
        with patch('app.services.approval_engine.executor.datetime') as mock_datetime:
            mock_now = datetime(2026, 2, 21, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            action, error = self.executor.handle_timeout(mock_task)
            
            self.assertEqual(action, "AUTO_PASS")
            self.assertIsNone(error)
            self.assertEqual(mock_task.action, "APPROVE")
            self.assertEqual(mock_task.status, "COMPLETED")
            self.assertIn("自动通过", mock_task.comment)

    def test_handle_timeout_auto_reject(self):
        """测试超时处理 - 自动驳回"""
        mock_task = self._create_mock_task("SINGLE")
        mock_task.node.timeout_action = "AUTO_REJECT"
        
        action, error = self.executor.handle_timeout(mock_task)
        
        self.assertEqual(action, "AUTO_REJECT")
        self.assertIsNone(error)
        self.assertEqual(mock_task.action, "REJECT")
        self.assertEqual(mock_task.status, "COMPLETED")
        self.assertIn("自动驳回", mock_task.comment)

    def test_handle_timeout_escalate(self):
        """测试超时处理 - 升级"""
        mock_task = self._create_mock_task("SINGLE")
        mock_task.node.timeout_action = "ESCALATE"
        
        action, error = self.executor.handle_timeout(mock_task)
        
        self.assertEqual(action, "ESCALATE")
        self.assertIsNone(error)
        self.assertEqual(mock_task.status, "EXPIRED")

    def test_handle_timeout_unknown_action(self):
        """测试超时处理 - 未知动作"""
        mock_task = self._create_mock_task("SINGLE")
        mock_task.node.timeout_action = "UNKNOWN"
        
        action, error = self.executor.handle_timeout(mock_task)
        
        self.assertEqual(action, "EXPIRED")
        self.assertEqual(mock_task.status, "EXPIRED")

    # ==================== 辅助方法 ====================

    def _create_mock_task(self, approval_mode: str) -> MagicMock:
        """创建Mock任务"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.id = 100
        mock_task.instance_id = 1
        mock_task.node_id = 10
        mock_task.status = "PENDING"
        
        mock_node = MagicMock(spec=ApprovalNodeDefinition)
        mock_node.id = 10
        mock_node.approval_mode = approval_mode
        mock_node.approver_config = {}
        mock_node.timeout_hours = 24
        
        mock_task.node = mock_node
        
        return mock_task

    def _create_mock_countersign_result(
        self, total: int, approved: int, rejected: int, pending: int
    ) -> MagicMock:
        """创建Mock会签结果"""
        mock_result = MagicMock(spec=ApprovalCountersignResult)
        mock_result.total_count = total
        mock_result.approved_count = approved
        mock_result.rejected_count = rejected
        mock_result.pending_count = pending
        mock_result.summary_data = None
        
        return mock_result

    def _create_task_with_eval(
        self, assignee_id: int, action: str, cost, schedule, risk: str
    ) -> MagicMock:
        """创建带评估数据的Mock任务"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.assignee_id = assignee_id
        mock_task.assignee_name = f"User{assignee_id}"
        mock_task.action = action
        mock_task.comment = "评审意见"
        mock_task.eval_data = {
            "cost_estimate": cost,
            "schedule_estimate": schedule,
            "risk_assessment": risk,
        }
        
        return mock_task


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
审批节点执行器单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库Session）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from app.services.approval_engine.executor import ApprovalNodeExecutor
from app.models.approval import (
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalCountersignResult,
    ApprovalCarbonCopy,
)


class TestApprovalNodeExecutorCreateTasks(unittest.TestCase):
    """测试任务创建方法 create_tasks_for_node"""

    def setUp(self):
        self.db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.db)

    def test_create_tasks_single_mode(self):
        """测试单人审批模式"""
        instance = ApprovalInstance(id=1)
        node = ApprovalNodeDefinition(
            id=10,
            approval_mode="SINGLE",
            timeout_hours=24,
        )
        approver_ids = [101, 102, 103]

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 单人模式：只创建一个任务
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].assignee_id, 101)
        self.assertEqual(tasks[0].status, "PENDING")
        self.assertEqual(tasks[0].task_order, 1)
        self.assertFalse(tasks[0].is_countersign)

    def test_create_tasks_or_sign_mode(self):
        """测试或签模式"""
        instance = ApprovalInstance(id=2)
        node = ApprovalNodeDefinition(
            id=20,
            approval_mode="OR_SIGN",
            timeout_hours=48,
        )
        approver_ids = [201, 202, 203]

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 或签模式：为每个人创建任务，全部PENDING
        self.assertEqual(len(tasks), 3)
        for i, task in enumerate(tasks):
            self.assertEqual(task.assignee_id, approver_ids[i])
            self.assertEqual(task.status, "PENDING")
            self.assertEqual(task.task_order, i + 1)
            self.assertFalse(task.is_countersign)

    def test_create_tasks_and_sign_mode(self):
        """测试会签模式（含会签统计记录）"""
        instance = ApprovalInstance(id=3)
        node = ApprovalNodeDefinition(
            id=30,
            approval_mode="AND_SIGN",
            timeout_hours=None,
        )
        approver_ids = [301, 302, 303, 304]

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 会签模式：每个人一个任务
        self.assertEqual(len(tasks), 4)
        for i, task in enumerate(tasks):
            self.assertEqual(task.assignee_id, approver_ids[i])
            self.assertEqual(task.status, "PENDING")
            self.assertTrue(task.is_countersign)
            self.assertIsNone(task.due_at)  # 没有timeout_hours

        # 检查是否创建了会签统计记录
        added_objs = [call[0][0] for call in self.db.add.call_args_list]
        countersign_result = next(
            (obj for obj in added_objs if isinstance(obj, ApprovalCountersignResult)),
            None
        )
        self.assertIsNotNone(countersign_result)
        self.assertEqual(countersign_result.total_count, 4)
        self.assertEqual(countersign_result.approved_count, 0)
        self.assertEqual(countersign_result.rejected_count, 0)
        self.assertEqual(countersign_result.pending_count, 4)
        self.assertEqual(countersign_result.final_result, "PENDING")

    def test_create_tasks_sequential_mode(self):
        """测试依次审批模式"""
        instance = ApprovalInstance(id=4)
        node = ApprovalNodeDefinition(
            id=40,
            approval_mode="SEQUENTIAL",
            timeout_hours=12,
        )
        approver_ids = [401, 402, 403]

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 依次审批：只有第一个是PENDING，其他是SKIPPED
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].status, "PENDING")
        self.assertIsNotNone(tasks[0].due_at)
        for i in range(1, 3):
            self.assertEqual(tasks[i].status, "SKIPPED")
            self.assertIsNone(tasks[i].due_at)

    def test_create_tasks_empty_approvers(self):
        """测试空审批人列表"""
        instance = ApprovalInstance(id=5)
        node = ApprovalNodeDefinition(id=50, approval_mode="SINGLE")
        tasks = self.executor.create_tasks_for_node(instance, node, [])
        self.assertEqual(tasks, [])

    def test_create_tasks_with_timeout_calculation(self):
        """测试超时时间计算"""
        instance = ApprovalInstance(id=6)
        node = ApprovalNodeDefinition(
            id=60,
            approval_mode="SINGLE",
            timeout_hours=72,
        )
        approver_ids = [601]

        before = datetime.now()
        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)
        after = datetime.now()

        expected_due = before + timedelta(hours=72)
        # 允许几秒钟的误差
        self.assertIsNotNone(tasks[0].due_at)
        self.assertLessEqual(abs((tasks[0].due_at - expected_due).total_seconds()), 5)


class TestApprovalNodeExecutorProcessApproval(unittest.TestCase):
    """测试审批处理方法 process_approval"""

    def setUp(self):
        self.db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.db)

    def test_process_approval_single_mode_approve(self):
        """测试单人模式-通过"""
        node = ApprovalNodeDefinition(id=10, approval_mode="SINGLE")
        task = ApprovalTask(
            id=1,
            instance_id=100,
            node_id=10,
            status="PENDING",
            node=node,
        )

        can_proceed, error = self.executor.process_approval(
            task, "APPROVE", "同意", None, None
        )

        # 单人审批：直接流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)
        self.assertEqual(task.action, "APPROVE")
        self.assertEqual(task.comment, "同意")
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)

    def test_process_approval_task_not_pending(self):
        """测试任务状态不是PENDING"""
        node = ApprovalNodeDefinition(id=10, approval_mode="SINGLE")
        task = ApprovalTask(
            id=1,
            status="COMPLETED",  # 已完成
            node=node,
        )

        can_proceed, error = self.executor.process_approval(task, "APPROVE")

        self.assertFalse(can_proceed)
        self.assertIn("任务状态不正确", error)

    def test_process_approval_or_sign_approve(self):
        """测试或签模式-有人通过"""
        node = ApprovalNodeDefinition(id=20, approval_mode="OR_SIGN")
        task = ApprovalTask(
            id=2,
            instance_id=200,
            node_id=20,
            status="PENDING",
            node=node,
        )

        # Mock _cancel_pending_tasks 方法
        self.executor._cancel_pending_tasks = MagicMock()

        can_proceed, error = self.executor.process_approval(task, "APPROVE")

        # 或签通过：应该流转，并取消其他任务
        self.assertTrue(can_proceed)
        self.assertIsNone(error)
        self.executor._cancel_pending_tasks.assert_called_once_with(200, 20, exclude_task_id=2)

    def test_process_approval_or_sign_reject_with_pending(self):
        """测试或签模式-驳回但还有其他待处理"""
        node = ApprovalNodeDefinition(id=20, approval_mode="OR_SIGN")
        task = ApprovalTask(
            id=3,
            instance_id=200,
            node_id=20,
            status="PENDING",
            node=node,
        )

        # Mock _count_pending_tasks 返回还有1个待处理
        self.executor._count_pending_tasks = MagicMock(return_value=1)

        can_proceed, error = self.executor.process_approval(task, "REJECT")

        # 还有人未审批：不能流转
        self.assertFalse(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_or_sign_reject_all(self):
        """测试或签模式-全部驳回"""
        node = ApprovalNodeDefinition(id=20, approval_mode="OR_SIGN")
        task = ApprovalTask(
            id=4,
            instance_id=200,
            node_id=20,
            status="PENDING",
            node=node,
        )

        # Mock _count_pending_tasks 返回0
        self.executor._count_pending_tasks = MagicMock(return_value=0)

        can_proceed, error = self.executor.process_approval(task, "REJECT")

        # 全部驳回：可以流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_and_sign_in_progress(self):
        """测试会签模式-审批中"""
        node = ApprovalNodeDefinition(
            id=30,
            approval_mode="AND_SIGN",
            approver_config={"pass_rule": "ALL"}
        )
        task = ApprovalTask(
            id=5,
            instance_id=300,
            node_id=30,
            status="PENDING",
            node=node,
        )

        # Mock _process_countersign 返回False（还未完成）
        self.executor._process_countersign = MagicMock(return_value=(False, None))

        can_proceed, error = self.executor.process_approval(task, "APPROVE")

        # 会签未完成：不能流转
        self.assertFalse(can_proceed)
        self.assertIsNone(error)
        self.executor._process_countersign.assert_called_once_with(task, "APPROVE")

    def test_process_approval_and_sign_completed(self):
        """测试会签模式-全部完成"""
        node = ApprovalNodeDefinition(
            id=30,
            approval_mode="AND_SIGN",
            approver_config={"pass_rule": "ALL"}
        )
        task = ApprovalTask(
            id=6,
            instance_id=300,
            node_id=30,
            status="PENDING",
            node=node,
        )

        # Mock _process_countersign 返回True（已完成）
        self.executor._process_countersign = MagicMock(return_value=(True, None))

        can_proceed, error = self.executor.process_approval(task, "APPROVE")

        # 会签完成：可以流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_sequential_approve_with_next(self):
        """测试依次审批-通过但还有下一个"""
        node = ApprovalNodeDefinition(id=40, approval_mode="SEQUENTIAL")
        task = ApprovalTask(
            id=7,
            instance_id=400,
            node_id=40,
            task_order=1,
            status="PENDING",
            node=node,
        )

        # Mock _activate_next_sequential_task 返回下一个任务
        next_task = ApprovalTask(id=8, task_order=2)
        self.executor._activate_next_sequential_task = MagicMock(return_value=next_task)

        can_proceed, error = self.executor.process_approval(task, "APPROVE")

        # 还有下一个：不能流转
        self.assertFalse(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_sequential_approve_last(self):
        """测试依次审批-最后一个通过"""
        node = ApprovalNodeDefinition(id=40, approval_mode="SEQUENTIAL")
        task = ApprovalTask(
            id=9,
            instance_id=400,
            node_id=40,
            task_order=3,
            status="PENDING",
            node=node,
        )

        # Mock _activate_next_sequential_task 返回None（没有下一个）
        self.executor._activate_next_sequential_task = MagicMock(return_value=None)

        can_proceed, error = self.executor.process_approval(task, "APPROVE")

        # 所有人都通过：可以流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_sequential_reject(self):
        """测试依次审批-驳回"""
        node = ApprovalNodeDefinition(id=40, approval_mode="SEQUENTIAL")
        task = ApprovalTask(
            id=10,
            instance_id=400,
            node_id=40,
            status="PENDING",
            node=node,
        )

        can_proceed, error = self.executor.process_approval(task, "REJECT")

        # 驳回时直接流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_with_attachments_and_eval_data(self):
        """测试带附件和评估数据的审批"""
        node = ApprovalNodeDefinition(id=50, approval_mode="SINGLE")
        task = ApprovalTask(
            id=11,
            status="PENDING",
            node=node,
        )

        attachments = [{"name": "file.pdf", "url": "http://example.com/file.pdf"}]
        eval_data = {
            "cost_estimate": 50000,
            "schedule_estimate": 30,
            "risk_assessment": "中",
        }

        can_proceed, error = self.executor.process_approval(
            task, "APPROVE", "技术可行", attachments, eval_data
        )

        self.assertTrue(can_proceed)
        self.assertEqual(task.comment, "技术可行")
        self.assertEqual(task.attachments, attachments)
        self.assertEqual(task.eval_data, eval_data)


class TestApprovalNodeExecutorCountersign(unittest.TestCase):
    """测试会签逻辑 _process_countersign"""

    def setUp(self):
        self.db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.db)

    def test_process_countersign_not_completed(self):
        """测试会签未完成"""
        node = ApprovalNodeDefinition(
            id=30,
            approver_config={"pass_rule": "ALL"}
        )
        task = ApprovalTask(
            id=1,
            instance_id=300,
            node_id=30,
            node=node,
        )

        # Mock查询返回会签统计
        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
            total_count=5,
            approved_count=0,
            rejected_count=0,
            pending_count=5,
        )
        self.db.query().filter().first.return_value = result

        can_proceed, error = self.executor._process_countersign(task, "APPROVE")

        # 还有4个待处理
        self.assertFalse(can_proceed)
        self.assertIsNone(error)
        self.assertEqual(result.approved_count, 1)
        self.assertEqual(result.pending_count, 4)

    def test_process_countersign_all_pass_rule_all_success(self):
        """测试会签-ALL规则-全部通过"""
        node = ApprovalNodeDefinition(
            id=30,
            approver_config={"pass_rule": "ALL"}
        )
        task = ApprovalTask(
            id=2,
            instance_id=300,
            node_id=30,
            node=node,
        )

        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
            total_count=3,
            approved_count=2,
            rejected_count=0,
            pending_count=1,  # 当前这个是最后一个
        )
        self.db.query().filter().first.return_value = result
        self.executor._summarize_eval_data = MagicMock()

        can_proceed, error = self.executor._process_countersign(task, "APPROVE")

        # 全部通过：可以流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)
        self.assertEqual(result.approved_count, 3)
        self.assertEqual(result.rejected_count, 0)
        self.assertEqual(result.pending_count, 0)
        self.assertEqual(result.final_result, "PASSED")
        self.executor._summarize_eval_data.assert_called_once()

    def test_process_countersign_all_pass_rule_all_failed(self):
        """测试会签-ALL规则-有人驳回"""
        node = ApprovalNodeDefinition(
            id=30,
            approver_config={"pass_rule": "ALL"}
        )
        task = ApprovalTask(
            id=3,
            instance_id=300,
            node_id=30,
            node=node,
        )

        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
            total_count=3,
            approved_count=2,
            rejected_count=0,
            pending_count=1,
        )
        self.db.query().filter().first.return_value = result
        self.executor._summarize_eval_data = MagicMock()

        can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 有人驳回：失败
        self.assertTrue(can_proceed)
        self.assertEqual(result.rejected_count, 1)
        self.assertEqual(result.final_result, "FAILED")

    def test_process_countersign_majority_rule_pass(self):
        """测试会签-MAJORITY规则-多数通过"""
        node = ApprovalNodeDefinition(
            id=30,
            approver_config={"pass_rule": "MAJORITY"}
        )
        task = ApprovalTask(
            id=4,
            instance_id=300,
            node_id=30,
            node=node,
        )

        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
            total_count=5,
            approved_count=3,
            rejected_count=1,
            pending_count=1,
        )
        self.db.query().filter().first.return_value = result
        self.executor._summarize_eval_data = MagicMock()

        can_proceed, error = self.executor._process_countersign(task, "APPROVE")

        # 4 > 1：多数通过
        self.assertTrue(can_proceed)
        self.assertEqual(result.approved_count, 4)
        self.assertEqual(result.final_result, "PASSED")

    def test_process_countersign_majority_rule_fail(self):
        """测试会签-MAJORITY规则-多数驳回"""
        node = ApprovalNodeDefinition(
            id=30,
            approver_config={"pass_rule": "MAJORITY"}
        )
        task = ApprovalTask(
            id=5,
            instance_id=300,
            node_id=30,
            node=node,
        )

        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
            total_count=5,
            approved_count=1,
            rejected_count=3,
            pending_count=1,
        )
        self.db.query().filter().first.return_value = result
        self.executor._summarize_eval_data = MagicMock()

        can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 1 < 4：多数驳回
        self.assertTrue(can_proceed)
        self.assertEqual(result.rejected_count, 4)
        self.assertEqual(result.final_result, "FAILED")

    def test_process_countersign_any_rule_pass(self):
        """测试会签-ANY规则-任一通过"""
        node = ApprovalNodeDefinition(
            id=30,
            approver_config={"pass_rule": "ANY"}
        )
        task = ApprovalTask(
            id=6,
            instance_id=300,
            node_id=30,
            node=node,
        )

        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
            total_count=3,
            approved_count=1,
            rejected_count=1,
            pending_count=1,
        )
        self.db.query().filter().first.return_value = result
        self.executor._summarize_eval_data = MagicMock()

        can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 有1个通过：成功
        self.assertTrue(can_proceed)
        self.assertEqual(result.final_result, "PASSED")

    def test_process_countersign_any_rule_fail(self):
        """测试会签-ANY规则-全部驳回"""
        node = ApprovalNodeDefinition(
            id=30,
            approver_config={"pass_rule": "ANY"}
        )
        task = ApprovalTask(
            id=7,
            instance_id=300,
            node_id=30,
            node=node,
        )

        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
            total_count=3,
            approved_count=0,
            rejected_count=2,
            pending_count=1,
        )
        self.db.query().filter().first.return_value = result
        self.executor._summarize_eval_data = MagicMock()

        can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 没有通过：失败
        self.assertTrue(can_proceed)
        self.assertEqual(result.final_result, "FAILED")

    def test_process_countersign_no_result_record(self):
        """测试会签统计记录不存在"""
        task = ApprovalTask(
            id=8,
            instance_id=300,
            node_id=30,
            node=MagicMock(),
        )

        self.db.query().filter().first.return_value = None

        can_proceed, error = self.executor._process_countersign(task, "APPROVE")

        self.assertFalse(can_proceed)
        self.assertEqual(error, "会签结果记录不存在")

    def test_process_countersign_default_rule(self):
        """测试会签-默认规则（无pass_rule或未知规则）"""
        node = ApprovalNodeDefinition(
            id=30,
            approver_config={"pass_rule": "UNKNOWN"}  # 未知规则
        )
        task = ApprovalTask(
            id=9,
            instance_id=300,
            node_id=30,
            node=node,
        )

        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
            total_count=2,
            approved_count=1,
            rejected_count=0,
            pending_count=1,
        )
        self.db.query().filter().first.return_value = result
        self.executor._summarize_eval_data = MagicMock()

        can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 默认使用ALL规则：有驳回即失败
        self.assertTrue(can_proceed)
        self.assertEqual(result.final_result, "FAILED")


class TestApprovalNodeExecutorSummarizeEvalData(unittest.TestCase):
    """测试评估数据汇总 _summarize_eval_data"""

    def setUp(self):
        self.db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.db)

    def test_summarize_eval_data_basic(self):
        """测试基本评估数据汇总"""
        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
        )

        tasks = [
            ApprovalTask(
                assignee_id=101,
                assignee_name="张三",
                action="APPROVE",
                comment="可行",
                eval_data={
                    "cost_estimate": 10000,
                    "schedule_estimate": 10,
                    "risk_assessment": "低",
                },
            ),
            ApprovalTask(
                assignee_id=102,
                assignee_name="李四",
                action="APPROVE",
                comment="需要注意风险",
                eval_data={
                    "cost_estimate": 20000,
                    "schedule_estimate": 15,
                    "risk_assessment": "中",
                },
            ),
            ApprovalTask(
                assignee_id=103,
                assignee_name="王五",
                action="APPROVE",
                comment="高风险项目",
                eval_data={
                    "cost_estimate": 30000,
                    "schedule_estimate": 20,
                    "risk_assessment": "高",
                },
            ),
        ]

        self.db.query().filter().all.return_value = tasks

        self.executor._summarize_eval_data(result)

        # 验证汇总结果
        self.assertIsNotNone(result.summary_data)
        self.assertEqual(result.summary_data["total_cost"], 60000)
        self.assertEqual(result.summary_data["total_schedule_days"], 45)
        self.assertEqual(result.summary_data["max_risk"], "高")
        self.assertEqual(len(result.summary_data["evaluations"]), 3)

    def test_summarize_eval_data_with_none_values(self):
        """测试包含None值的评估数据"""
        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
        )

        tasks = [
            ApprovalTask(
                assignee_id=101,
                assignee_name="张三",
                action="APPROVE",
                comment="可行",
                eval_data={
                    "cost_estimate": None,
                    "schedule_estimate": 10,
                    "risk_assessment": "低",
                },
            ),
            ApprovalTask(
                assignee_id=102,
                assignee_name="李四",
                action="APPROVE",
                comment="需要注意风险",
                eval_data={
                    "cost_estimate": 5000,
                    "schedule_estimate": None,
                    "risk_assessment": "中",
                },
            ),
        ]

        self.db.query().filter().all.return_value = tasks

        self.executor._summarize_eval_data(result)

        # None值应被视为0
        self.assertEqual(result.summary_data["total_cost"], 5000)
        self.assertEqual(result.summary_data["total_schedule_days"], 10)
        self.assertEqual(result.summary_data["max_risk"], "中")

    def test_summarize_eval_data_no_eval_data(self):
        """测试没有评估数据的任务"""
        result = ApprovalCountersignResult(
            instance_id=300,
            node_id=30,
        )

        tasks = [
            ApprovalTask(
                assignee_id=101,
                assignee_name="张三",
                action="APPROVE",
                comment="可行",
                eval_data=None,
            ),
        ]

        self.db.query().filter().all.return_value = tasks

        self.executor._summarize_eval_data(result)

        # 应该有空的evaluations
        self.assertEqual(result.summary_data["total_cost"], 0)
        self.assertEqual(result.summary_data["total_schedule_days"], 0)
        self.assertEqual(result.summary_data["max_risk"], "低")
        self.assertEqual(len(result.summary_data["evaluations"]), 0)


class TestApprovalNodeExecutorHelperMethods(unittest.TestCase):
    """测试辅助方法"""

    def setUp(self):
        self.db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.db)

    def test_cancel_pending_tasks(self):
        """测试取消待处理任务"""
        mock_query = self.db.query.return_value.filter.return_value

        self.executor._cancel_pending_tasks(100, 10, exclude_task_id=5)

        # 验证调用了update
        mock_query.filter.return_value.update.assert_called_once_with(
            {"status": "CANCELLED"},
            synchronize_session=False
        )

    def test_cancel_pending_tasks_no_exclude(self):
        """测试取消所有待处理任务"""
        mock_query = self.db.query.return_value.filter.return_value

        self.executor._cancel_pending_tasks(100, 10)

        # 验证调用了update（没有exclude过滤）
        mock_query.update.assert_called_once()

    def test_count_pending_tasks(self):
        """测试统计待处理任务"""
        self.db.query.return_value.filter.return_value.count.return_value = 3

        count = self.executor._count_pending_tasks(100, 10)

        self.assertEqual(count, 3)

    def test_activate_next_sequential_task(self):
        """测试激活下一个依次审批任务"""
        current_task = ApprovalTask(
            id=1,
            instance_id=100,
            node_id=10,
            task_order=1,
            node=ApprovalNodeDefinition(id=10, timeout_hours=24),
        )

        next_task = ApprovalTask(
            id=2,
            task_order=2,
            status="SKIPPED",
        )
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = next_task

        before = datetime.now()
        result = self.executor._activate_next_sequential_task(current_task)
        after = datetime.now()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, "PENDING")
        self.assertIsNotNone(result.due_at)
        expected_due = before + timedelta(hours=24)
        self.assertLessEqual(abs((result.due_at - expected_due).total_seconds()), 5)

    def test_activate_next_sequential_task_no_next(self):
        """测试没有下一个任务"""
        current_task = ApprovalTask(
            id=3,
            instance_id=100,
            node_id=10,
            task_order=3,
        )

        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = self.executor._activate_next_sequential_task(current_task)

        self.assertIsNone(result)

    def test_activate_next_sequential_task_no_timeout(self):
        """测试激活任务（节点无超时设置）"""
        current_task = ApprovalTask(
            id=1,
            instance_id=100,
            node_id=10,
            task_order=1,
            node=ApprovalNodeDefinition(id=10, timeout_hours=None),
        )

        next_task = ApprovalTask(
            id=2,
            task_order=2,
            status="SKIPPED",
        )
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = next_task

        result = self.executor._activate_next_sequential_task(current_task)

        self.assertIsNotNone(result)
        # 没有timeout_hours时，due_at保持None（原来的值）
        # 注意：这里实际上代码会设置due_at，因为只有timeout_hours为None时才不设置
        # 从代码逻辑看，如果node.timeout_hours为None，代码不会设置due_at


class TestApprovalNodeExecutorCarbonCopy(unittest.TestCase):
    """测试抄送记录创建 create_cc_records"""

    def setUp(self):
        self.db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.db)

    def test_create_cc_records_new(self):
        """测试创建新的抄送记录"""
        instance = ApprovalInstance(id=100)

        # Mock查询，不存在重复抄送
        self.db.query.return_value.filter.return_value.first.return_value = None

        records = self.executor.create_cc_records(
            instance, 10, [201, 202, 203], "FLOW", added_by=1001
        )

        self.assertEqual(len(records), 3)
        for i, record in enumerate(records):
            self.assertEqual(record.instance_id, 100)
            self.assertEqual(record.node_id, 10)
            self.assertEqual(record.cc_user_id, [201, 202, 203][i])
            self.assertEqual(record.cc_source, "FLOW")
            self.assertEqual(record.added_by, 1001)
            self.assertFalse(record.is_read)

    def test_create_cc_records_duplicate(self):
        """测试避免重复抄送"""
        instance = ApprovalInstance(id=100)

        # Mock查询，第二个用户已存在抄送
        call_count = [0]
        
        def mock_first():
            call_count[0] += 1
            if call_count[0] == 2:  # 第二次查询返回已存在
                return ApprovalCarbonCopy(id=999, cc_user_id=202)
            return None

        # 每次调用query().filter()都返回同一个mock对象，但first()行为不同
        self.db.query.return_value.filter.return_value.first = mock_first

        records = self.executor.create_cc_records(
            instance, 10, [201, 202, 203], "MANUAL"
        )

        # 应该只创建2条记录（跳过202）
        self.assertEqual(len(records), 2)
        cc_user_ids = [r.cc_user_id for r in records]
        self.assertIn(201, cc_user_ids)
        self.assertIn(203, cc_user_ids)
        self.assertNotIn(202, cc_user_ids)

    def test_create_cc_records_empty(self):
        """测试空抄送列表"""
        instance = ApprovalInstance(id=100)

        records = self.executor.create_cc_records(instance, 10, [], "FLOW")

        self.assertEqual(records, [])


class TestApprovalNodeExecutorHandleTimeout(unittest.TestCase):
    """测试超时处理 handle_timeout"""

    def setUp(self):
        self.db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.db)

    def test_handle_timeout_remind(self):
        """测试超时催办"""
        node = ApprovalNodeDefinition(id=10, timeout_action="REMIND")
        task = ApprovalTask(
            id=1,
            status="PENDING",
            remind_count=0,
            node=node,
        )

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "REMIND")
        self.assertIsNone(error)
        self.assertEqual(task.remind_count, 1)
        self.assertIsNotNone(task.reminded_at)

    def test_handle_timeout_remind_multiple(self):
        """测试多次催办"""
        node = ApprovalNodeDefinition(id=10, timeout_action="REMIND")
        task = ApprovalTask(
            id=1,
            status="PENDING",
            remind_count=2,
            node=node,
        )

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "REMIND")
        self.assertEqual(task.remind_count, 3)

    def test_handle_timeout_auto_pass(self):
        """测试超时自动通过"""
        node = ApprovalNodeDefinition(id=10, timeout_action="AUTO_PASS")
        task = ApprovalTask(
            id=2,
            status="PENDING",
            node=node,
        )

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "AUTO_PASS")
        self.assertIsNone(error)
        self.assertEqual(task.action, "APPROVE")
        self.assertEqual(task.comment, "系统自动通过（超时）")
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)

    def test_handle_timeout_auto_reject(self):
        """测试超时自动驳回"""
        node = ApprovalNodeDefinition(id=10, timeout_action="AUTO_REJECT")
        task = ApprovalTask(
            id=3,
            status="PENDING",
            node=node,
        )

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "AUTO_REJECT")
        self.assertIsNone(error)
        self.assertEqual(task.action, "REJECT")
        self.assertEqual(task.comment, "系统自动驳回（超时）")
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)

    def test_handle_timeout_escalate(self):
        """测试超时升级处理"""
        node = ApprovalNodeDefinition(id=10, timeout_action="ESCALATE")
        task = ApprovalTask(
            id=4,
            status="PENDING",
            node=node,
        )

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "ESCALATE")
        self.assertIsNone(error)
        self.assertEqual(task.status, "EXPIRED")

    def test_handle_timeout_expired(self):
        """测试超时标记为过期"""
        node = ApprovalNodeDefinition(id=10, timeout_action="EXPIRED")
        task = ApprovalTask(
            id=5,
            status="PENDING",
            node=node,
        )

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "EXPIRED")
        self.assertIsNone(error)
        self.assertEqual(task.status, "EXPIRED")

    def test_handle_timeout_default_action(self):
        """测试默认超时处理（无timeout_action）"""
        node = ApprovalNodeDefinition(id=10, timeout_action=None)
        task = ApprovalTask(
            id=6,
            status="PENDING",
            node=node,
        )

        action, error = self.executor.handle_timeout(task)

        # 默认应该是REMIND
        self.assertEqual(action, "REMIND")

    def test_handle_timeout_task_not_pending(self):
        """测试非PENDING任务的超时处理"""
        node = ApprovalNodeDefinition(id=10, timeout_action="AUTO_PASS")
        task = ApprovalTask(
            id=7,
            status="COMPLETED",
            node=node,
        )

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "NONE")
        self.assertIn("任务已不是待处理状态", error)


if __name__ == "__main__":
    unittest.main()

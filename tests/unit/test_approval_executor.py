# -*- coding: utf-8 -*-
"""
审批节点执行器单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, call, patch

from app.services.approval_engine.executor import ApprovalNodeExecutor


class TestApprovalNodeExecutor(unittest.TestCase):
    """测试审批节点执行器"""

    def setUp(self):
        """初始化测试环境"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        self.executor = ApprovalNodeExecutor(self.mock_db)

    def _create_mock_instance(self, instance_id=1):
        """创建mock审批实例"""
        instance = Mock()
        instance.id = instance_id
        instance.instance_no = f"AP{instance_id:06d}"
        instance.status = "PENDING"
        return instance

    def _create_mock_node(
        self,
        node_id=1,
        approval_mode="SINGLE",
        timeout_hours=24,
        timeout_action="REMIND",
        approver_config=None,
    ):
        """创建mock节点定义"""
        node = Mock()
        node.id = node_id
        node.node_name = f"节点{node_id}"
        node.approval_mode = approval_mode
        node.timeout_hours = timeout_hours
        node.timeout_action = timeout_action
        node.approver_config = approver_config or {}
        return node

    def _create_mock_task(
        self,
        task_id=1,
        instance_id=1,
        node_id=1,
        assignee_id=1,
        status="PENDING",
        task_order=1,
        is_countersign=False,
    ):
        """创建mock审批任务"""
        task = Mock()
        task.id = task_id
        task.instance_id = instance_id
        task.node_id = node_id
        task.assignee_id = assignee_id
        task.status = status
        task.task_order = task_order
        task.is_countersign = is_countersign
        task.action = None
        task.comment = None
        task.attachments = None
        task.eval_data = None
        task.completed_at = None
        task.remind_count = 0
        task.reminded_at = None

        # 关联mock node
        task.node = self._create_mock_node(
            node_id=node_id,
            approval_mode="SINGLE",
        )
        return task


class TestCreateTasksForNode(TestApprovalNodeExecutor):
    """测试 create_tasks_for_node() 方法"""

    def test_create_tasks_empty_approvers(self):
        """测试空审批人列表"""
        instance = self._create_mock_instance()
        node = self._create_mock_node()

        tasks = self.executor.create_tasks_for_node(instance, node, [])

        self.assertEqual(tasks, [])
        self.mock_db.add.assert_not_called()

    def test_create_tasks_single_mode(self):
        """测试单人审批模式"""
        instance = self._create_mock_instance()
        node = self._create_mock_node(
            approval_mode="SINGLE",
            timeout_hours=24,
        )
        approver_ids = [101]

        # Mock add方法，捕获添加的对象
        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 验证只创建了一个任务
        self.assertEqual(len(tasks), 1)
        self.assertEqual(len(added_tasks), 1)

        # 验证任务属性
        task = tasks[0]
        self.assertEqual(task.instance_id, instance.id)
        self.assertEqual(task.node_id, node.id)
        self.assertEqual(task.assignee_id, 101)
        self.assertEqual(task.status, "PENDING")
        self.assertEqual(task.task_order, 1)
        self.assertFalse(task.is_countersign)
        self.assertIsNotNone(task.due_at)

        # 验证db.flush被调用
        self.mock_db.flush.assert_called_once()

    def test_create_tasks_or_sign_mode(self):
        """测试或签模式"""
        instance = self._create_mock_instance()
        node = self._create_mock_node(approval_mode="OR_SIGN")
        approver_ids = [101, 102, 103]

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 验证为每个审批人创建了任务
        self.assertEqual(len(tasks), 3)
        self.assertEqual(len(added_tasks), 3)

        # 验证所有任务都是PENDING
        for idx, task in enumerate(tasks):
            self.assertEqual(task.assignee_id, approver_ids[idx])
            self.assertEqual(task.status, "PENDING")
            self.assertEqual(task.task_order, idx + 1)
            self.assertFalse(task.is_countersign)

    def test_create_tasks_and_sign_mode(self):
        """测试会签模式"""
        instance = self._create_mock_instance()
        node = self._create_mock_node(approval_mode="AND_SIGN")
        approver_ids = [101, 102, 103]

        added_objects = []
        self.mock_db.add.side_effect = lambda obj: added_objects.append(obj)

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 验证创建了3个任务 + 1个会签结果记录
        self.assertEqual(len(tasks), 3)
        self.assertEqual(len(added_objects), 4)  # 3 tasks + 1 countersign result

        # 验证会签任务属性
        for task in tasks:
            self.assertTrue(task.is_countersign)
            self.assertEqual(task.status, "PENDING")

        # 验证会签结果记录
        from app.models.approval import ApprovalCountersignResult

        countersign_result = [
            obj for obj in added_objects if isinstance(obj, ApprovalCountersignResult)
        ][0]
        self.assertEqual(countersign_result.instance_id, instance.id)
        self.assertEqual(countersign_result.node_id, node.id)
        self.assertEqual(countersign_result.total_count, 3)
        self.assertEqual(countersign_result.approved_count, 0)
        self.assertEqual(countersign_result.rejected_count, 0)
        self.assertEqual(countersign_result.pending_count, 3)
        self.assertEqual(countersign_result.final_result, "PENDING")

    def test_create_tasks_sequential_mode(self):
        """测试依次审批模式"""
        instance = self._create_mock_instance()
        node = self._create_mock_node(approval_mode="SEQUENTIAL")
        approver_ids = [101, 102, 103]

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 验证创建了3个任务
        self.assertEqual(len(tasks), 3)

        # 第一个任务是PENDING，其他是SKIPPED
        self.assertEqual(tasks[0].status, "PENDING")
        self.assertIsNotNone(tasks[0].due_at)

        for task in tasks[1:]:
            self.assertEqual(task.status, "SKIPPED")
            self.assertIsNone(task.due_at)

    def test_create_tasks_no_timeout(self):
        """测试无超时设置"""
        instance = self._create_mock_instance()
        node = self._create_mock_node(timeout_hours=None)
        approver_ids = [101]

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        tasks = self.executor.create_tasks_for_node(instance, node, approver_ids)

        # 验证due_at为None
        self.assertIsNone(tasks[0].due_at)


class TestProcessApproval(TestApprovalNodeExecutor):
    """测试 process_approval() 方法"""

    def test_process_approval_invalid_status(self):
        """测试任务状态不正确"""
        task = self._create_mock_task(status="COMPLETED")

        can_proceed, error = self.executor.process_approval(task, "APPROVE")

        self.assertFalse(can_proceed)
        self.assertIn("任务状态不正确", error)

    def test_process_approval_single_mode_approve(self):
        """测试单人审批 - 通过"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(approval_mode="SINGLE")

        can_proceed, error = self.executor.process_approval(
            task,
            "APPROVE",
            comment="同意",
            attachments=[{"url": "file.pdf"}],
        )

        # 验证任务更新
        self.assertEqual(task.action, "APPROVE")
        self.assertEqual(task.comment, "同意")
        self.assertEqual(task.attachments, [{"url": "file.pdf"}])
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)

        # 单人审批直接流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_single_mode_reject(self):
        """测试单人审批 - 驳回"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(approval_mode="SINGLE")

        can_proceed, error = self.executor.process_approval(task, "REJECT", comment="不同意")

        self.assertEqual(task.action, "REJECT")
        self.assertEqual(task.comment, "不同意")
        self.assertEqual(task.status, "COMPLETED")
        self.assertTrue(can_proceed)

    def test_process_approval_or_sign_first_approve(self):
        """测试或签 - 第一个人通过"""
        task = self._create_mock_task(task_id=1, node_id=1)
        task.node = self._create_mock_node(node_id=1, approval_mode="OR_SIGN")

        # Mock _cancel_pending_tasks
        with patch.object(
            self.executor, "_cancel_pending_tasks"
        ) as mock_cancel:
            can_proceed, error = self.executor.process_approval(task, "APPROVE")

            # 验证取消其他待处理任务
            mock_cancel.assert_called_once_with(
                task.instance_id, task.node_id, exclude_task_id=task.id
            )

            # 或签一人通过即可流转
            self.assertTrue(can_proceed)
            self.assertIsNone(error)

    def test_process_approval_or_sign_all_reject(self):
        """测试或签 - 全部驳回"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(approval_mode="OR_SIGN")

        # Mock _count_pending_tasks 返回0（没有待处理任务了）
        with patch.object(
            self.executor, "_count_pending_tasks", return_value=0
        ):
            can_proceed, error = self.executor.process_approval(task, "REJECT")

            # 全部驳回，可以流转
            self.assertTrue(can_proceed)
            self.assertIsNone(error)

    def test_process_approval_or_sign_reject_has_pending(self):
        """测试或签 - 驳回但还有待处理任务"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(approval_mode="OR_SIGN")

        # Mock _count_pending_tasks 返回2（还有2个待处理任务）
        with patch.object(
            self.executor, "_count_pending_tasks", return_value=2
        ):
            can_proceed, error = self.executor.process_approval(task, "REJECT")

            # 还有待处理任务，不流转
            self.assertFalse(can_proceed)
            self.assertIsNone(error)

    def test_process_approval_and_sign(self):
        """测试会签"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(approval_mode="AND_SIGN")

        # Mock _process_countersign
        with patch.object(
            self.executor, "_process_countersign", return_value=(True, None)
        ) as mock_countersign:
            can_proceed, error = self.executor.process_approval(task, "APPROVE")

            # 验证调用了_process_countersign
            mock_countersign.assert_called_once_with(task, "APPROVE")
            self.assertTrue(can_proceed)
            self.assertIsNone(error)

    def test_process_approval_sequential_approve(self):
        """测试依次审批 - 通过"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(approval_mode="SEQUENTIAL")

        # Mock _activate_next_sequential_task 返回下一个任务
        next_task = Mock()
        with patch.object(
            self.executor, "_activate_next_sequential_task", return_value=next_task
        ):
            can_proceed, error = self.executor.process_approval(task, "APPROVE")

            # 还有后续任务，不流转
            self.assertFalse(can_proceed)
            self.assertIsNone(error)

    def test_process_approval_sequential_approve_last(self):
        """测试依次审批 - 最后一个人通过"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(approval_mode="SEQUENTIAL")

        # Mock _activate_next_sequential_task 返回None（没有下一个任务）
        with patch.object(
            self.executor, "_activate_next_sequential_task", return_value=None
        ):
            can_proceed, error = self.executor.process_approval(task, "APPROVE")

            # 所有人都通过，可以流转
            self.assertTrue(can_proceed)
            self.assertIsNone(error)

    def test_process_approval_sequential_reject(self):
        """测试依次审批 - 驳回"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(approval_mode="SEQUENTIAL")

        can_proceed, error = self.executor.process_approval(task, "REJECT")

        # 驳回时直接流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)

    def test_process_approval_with_eval_data(self):
        """测试带评估数据的审批"""
        task = self._create_mock_task()
        task.node = self._create_mock_node()

        eval_data = {
            "cost_estimate": 5000,
            "schedule_estimate": 3,
            "risk_assessment": "中",
        }

        can_proceed, error = self.executor.process_approval(
            task, "APPROVE", eval_data=eval_data
        )

        self.assertEqual(task.eval_data, eval_data)
        self.assertTrue(can_proceed)


class TestProcessCountersign(TestApprovalNodeExecutor):
    """测试 _process_countersign() 方法"""

    def _create_mock_countersign_result(
        self, approved_count=0, rejected_count=0, pending_count=3
    ):
        """创建mock会签结果"""
        result = Mock()
        result.instance_id = 1
        result.node_id = 1
        result.approved_count = approved_count
        result.rejected_count = rejected_count
        result.pending_count = pending_count
        result.final_result = "PENDING"
        return result

    def test_process_countersign_not_complete(self):
        """测试会签未完成"""
        task = self._create_mock_task()
        result = self._create_mock_countersign_result(
            approved_count=1, pending_count=2
        )

        # Mock query
        self.mock_db.query.return_value.filter.return_value.first.return_value = result

        can_proceed, error = self.executor._process_countersign(task, "APPROVE")

        # 验证统计更新
        self.assertEqual(result.approved_count, 2)  # 1 + 1
        self.assertEqual(result.pending_count, 1)  # 2 - 1

        # 未完成，不流转
        self.assertFalse(can_proceed)
        self.assertIsNone(error)

    def test_process_countersign_complete_all_pass(self):
        """测试会签完成 - 全部通过"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(
            approver_config={"pass_rule": "ALL"}
        )
        result = self._create_mock_countersign_result(
            approved_count=2, rejected_count=0, pending_count=1
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = result

        # Mock _summarize_eval_data
        with patch.object(self.executor, "_summarize_eval_data"):
            can_proceed, error = self.executor._process_countersign(task, "APPROVE")

        # 验证统计更新
        self.assertEqual(result.approved_count, 3)
        self.assertEqual(result.pending_count, 0)
        self.assertEqual(result.final_result, "PASSED")

        # 可以流转
        self.assertTrue(can_proceed)
        self.assertIsNone(error)

    def test_process_countersign_complete_has_reject(self):
        """测试会签完成 - 有驳回"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(
            approver_config={"pass_rule": "ALL"}
        )
        result = self._create_mock_countersign_result(
            approved_count=2, rejected_count=1, pending_count=1
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = result

        with patch.object(self.executor, "_summarize_eval_data"):
            can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 有驳回，结果为FAILED
        self.assertEqual(result.final_result, "FAILED")
        self.assertTrue(can_proceed)

    def test_process_countersign_majority_pass(self):
        """测试会签完成 - 多数通过"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(
            approver_config={"pass_rule": "MAJORITY"}
        )
        result = self._create_mock_countersign_result(
            approved_count=3, rejected_count=1, pending_count=1
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = result

        with patch.object(self.executor, "_summarize_eval_data"):
            can_proceed, error = self.executor._process_countersign(task, "APPROVE")

        # 4:1，多数通过
        self.assertEqual(result.final_result, "PASSED")

    def test_process_countersign_majority_fail(self):
        """测试会签完成 - 多数驳回"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(
            approver_config={"pass_rule": "MAJORITY"}
        )
        result = self._create_mock_countersign_result(
            approved_count=1, rejected_count=2, pending_count=1
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = result

        with patch.object(self.executor, "_summarize_eval_data"):
            can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 1:3，多数驳回
        self.assertEqual(result.final_result, "FAILED")

    def test_process_countersign_any_pass(self):
        """测试会签完成 - 任一通过"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(
            approver_config={"pass_rule": "ANY"}
        )
        result = self._create_mock_countersign_result(
            approved_count=1, rejected_count=2, pending_count=1
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = result

        with patch.object(self.executor, "_summarize_eval_data"):
            can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 有1人通过，结果为PASSED
        self.assertEqual(result.final_result, "PASSED")

    def test_process_countersign_no_result_record(self):
        """测试会签结果记录不存在"""
        task = self._create_mock_task()

        # Mock query 返回None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        can_proceed, error = self.executor._process_countersign(task, "APPROVE")

        self.assertFalse(can_proceed)
        self.assertIn("会签结果记录不存在", error)


class TestSummarizeEvalData(TestApprovalNodeExecutor):
    """测试 _summarize_eval_data() 方法"""

    def test_summarize_eval_data_basic(self):
        """测试基本评估数据汇总"""
        result = Mock()
        result.instance_id = 1
        result.node_id = 1

        # Mock tasks
        task1 = Mock()
        task1.assignee_id = 101
        task1.assignee_name = "张三"
        task1.action = "APPROVE"
        task1.comment = "同意"
        task1.eval_data = {
            "cost_estimate": 5000,
            "schedule_estimate": 3,
            "risk_assessment": "中",
        }

        task2 = Mock()
        task2.assignee_id = 102
        task2.assignee_name = "李四"
        task2.action = "APPROVE"
        task2.comment = "同意"
        task2.eval_data = {
            "cost_estimate": 10000,
            "schedule_estimate": 5,
            "risk_assessment": "高",
        }

        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            task1,
            task2,
        ]

        self.executor._summarize_eval_data(result)

        # 验证汇总数据
        self.assertEqual(result.summary_data["total_cost"], 15000)
        self.assertEqual(result.summary_data["total_schedule_days"], 8)
        self.assertEqual(result.summary_data["max_risk"], "高")
        self.assertEqual(len(result.summary_data["evaluations"]), 2)

    def test_summarize_eval_data_no_eval(self):
        """测试无评估数据"""
        result = Mock()
        result.instance_id = 1
        result.node_id = 1

        task = Mock()
        task.assignee_id = 101
        task.assignee_name = "张三"
        task.action = "APPROVE"
        task.comment = "同意"
        task.eval_data = None

        self.mock_db.query.return_value.filter.return_value.all.return_value = [task]

        self.executor._summarize_eval_data(result)

        # 无评估数据时，汇总为0
        self.assertEqual(result.summary_data["total_cost"], 0)
        self.assertEqual(result.summary_data["total_schedule_days"], 0)
        self.assertEqual(result.summary_data["max_risk"], "低")
        self.assertEqual(len(result.summary_data["evaluations"]), 0)

    def test_summarize_eval_data_partial_data(self):
        """测试部分评估数据缺失"""
        result = Mock()
        result.instance_id = 1
        result.node_id = 1

        task = Mock()
        task.assignee_id = 101
        task.assignee_name = "张三"
        task.action = "APPROVE"
        task.comment = "同意"
        task.eval_data = {
            "cost_estimate": None,  # 缺失
            "schedule_estimate": 3,
            # risk_assessment 缺失
        }

        self.mock_db.query.return_value.filter.return_value.all.return_value = [task]

        self.executor._summarize_eval_data(result)

        # None应被处理为0
        self.assertEqual(result.summary_data["total_cost"], 0)
        self.assertEqual(result.summary_data["total_schedule_days"], 3)
        self.assertEqual(result.summary_data["max_risk"], "低")


class TestCancelPendingTasks(TestApprovalNodeExecutor):
    """测试 _cancel_pending_tasks() 方法"""

    def test_cancel_pending_tasks(self):
        """测试取消待处理任务"""
        # 创建一个mock update方法
        mock_update = Mock()
        
        # 创建mock查询对象，filter()返回自己以支持链式调用
        # update()返回mock_update的返回值
        mock_query_obj = Mock()
        mock_query_obj.filter.return_value = mock_query_obj  # 支持链式调用
        mock_query_obj.update = mock_update
        
        # query()返回mock查询对象
        self.mock_db.query.return_value = mock_query_obj

        self.executor._cancel_pending_tasks(
            instance_id=1, node_id=1, exclude_task_id=10
        )

        # 验证update调用
        mock_update.assert_called_once_with(
            {"status": "CANCELLED"}, synchronize_session=False
        )

    def test_cancel_pending_tasks_no_exclude(self):
        """测试取消所有待处理任务（无排除）"""
        mock_query = Mock()
        self.mock_db.query.return_value = mock_query

        self.executor._cancel_pending_tasks(instance_id=1, node_id=1)

        # 验证没有添加exclude_task_id过滤条件
        # 实际实现中会少一次filter调用
        self.mock_db.query.assert_called_once()


class TestCountPendingTasks(TestApprovalNodeExecutor):
    """测试 _count_pending_tasks() 方法"""

    def test_count_pending_tasks(self):
        """测试统计待处理任务"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5

        count = self.executor._count_pending_tasks(instance_id=1, node_id=1)

        self.assertEqual(count, 5)
        self.mock_db.query.assert_called_once()

    def test_count_pending_tasks_zero(self):
        """测试统计结果为0"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        count = self.executor._count_pending_tasks(instance_id=1, node_id=1)

        self.assertEqual(count, 0)


class TestActivateNextSequentialTask(TestApprovalNodeExecutor):
    """测试 _activate_next_sequential_task() 方法"""

    def test_activate_next_task_success(self):
        """测试激活下一个任务成功"""
        current_task = self._create_mock_task(task_order=1)
        current_task.node = self._create_mock_node(timeout_hours=24)

        next_task = Mock()
        next_task.status = "SKIPPED"
        next_task.due_at = None

        # Mock query
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = (
            next_task
        )

        result = self.executor._activate_next_sequential_task(current_task)

        # 验证激活成功
        self.assertEqual(result, next_task)
        self.assertEqual(next_task.status, "PENDING")
        self.assertIsNotNone(next_task.due_at)

    def test_activate_next_task_no_next(self):
        """测试没有下一个任务"""
        current_task = self._create_mock_task(task_order=3)

        # Mock query 返回None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = None

        result = self.executor._activate_next_sequential_task(current_task)

        self.assertIsNone(result)

    def test_activate_next_task_no_timeout(self):
        """测试激活下一个任务（无超时设置）"""
        current_task = self._create_mock_task()
        current_task.node = self._create_mock_node(timeout_hours=None)

        next_task = Mock()
        next_task.status = "SKIPPED"
        next_task.due_at = None

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = (
            next_task
        )

        result = self.executor._activate_next_sequential_task(current_task)

        # 无超时设置时，due_at保持为None
        self.assertEqual(next_task.status, "PENDING")
        self.assertIsNone(next_task.due_at)


class TestCreateCCRecords(TestApprovalNodeExecutor):
    """测试 create_cc_records() 方法"""

    def test_create_cc_records_basic(self):
        """测试创建抄送记录"""
        instance = self._create_mock_instance()
        cc_user_ids = [201, 202, 203]

        # Mock query 返回None（不存在重复记录）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        added_records = []
        self.mock_db.add.side_effect = lambda obj: added_records.append(obj)

        records = self.executor.create_cc_records(
            instance,
            node_id=1,
            cc_user_ids=cc_user_ids,
            cc_source="FLOW",
            added_by=100,
        )

        # 验证创建了3条记录
        self.assertEqual(len(records), 3)
        self.assertEqual(len(added_records), 3)

        # 验证记录属性
        for idx, record in enumerate(records):
            self.assertEqual(record.instance_id, instance.id)
            self.assertEqual(record.node_id, 1)
            self.assertEqual(record.cc_user_id, cc_user_ids[idx])
            self.assertEqual(record.cc_source, "FLOW")
            self.assertEqual(record.added_by, 100)
            self.assertFalse(record.is_read)

        self.mock_db.flush.assert_called_once()

    def test_create_cc_records_skip_duplicate(self):
        """测试跳过重复抄送"""
        instance = self._create_mock_instance()
        cc_user_ids = [201, 202]

        # 第一个用户已存在
        existing_record = Mock()
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            existing_record,  # 201已存在
            None,  # 202不存在
        ]

        added_records = []
        self.mock_db.add.side_effect = lambda obj: added_records.append(obj)

        records = self.executor.create_cc_records(
            instance, node_id=1, cc_user_ids=cc_user_ids
        )

        # 只创建了1条记录（跳过了重复的）
        self.assertEqual(len(records), 1)
        self.assertEqual(len(added_records), 1)
        self.assertEqual(records[0].cc_user_id, 202)

    def test_create_cc_records_empty_list(self):
        """测试空抄送列表"""
        instance = self._create_mock_instance()

        records = self.executor.create_cc_records(instance, node_id=1, cc_user_ids=[])

        self.assertEqual(records, [])
        self.mock_db.add.assert_not_called()

    def test_create_cc_records_no_node(self):
        """测试无节点抄送（发起时抄送）"""
        instance = self._create_mock_instance()

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        added_records = []
        self.mock_db.add.side_effect = lambda obj: added_records.append(obj)

        records = self.executor.create_cc_records(
            instance, node_id=None, cc_user_ids=[201]
        )

        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].node_id)


class TestHandleTimeout(TestApprovalNodeExecutor):
    """测试 handle_timeout() 方法"""

    def test_handle_timeout_task_not_pending(self):
        """测试任务不是待处理状态"""
        task = self._create_mock_task(status="COMPLETED")

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "NONE")
        self.assertIn("任务已不是待处理状态", error)

    def test_handle_timeout_remind(self):
        """测试催办提醒"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(timeout_action="REMIND")
        task.remind_count = 0

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "REMIND")
        self.assertIsNone(error)
        self.assertEqual(task.remind_count, 1)
        self.assertIsNotNone(task.reminded_at)

    def test_handle_timeout_remind_increment(self):
        """测试多次催办"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(timeout_action="REMIND")
        task.remind_count = 2

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "REMIND")
        self.assertEqual(task.remind_count, 3)

    def test_handle_timeout_auto_pass(self):
        """测试自动通过"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(timeout_action="AUTO_PASS")

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "AUTO_PASS")
        self.assertIsNone(error)
        self.assertEqual(task.action, "APPROVE")
        self.assertEqual(task.comment, "系统自动通过（超时）")
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)

    def test_handle_timeout_auto_reject(self):
        """测试自动驳回"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(timeout_action="AUTO_REJECT")

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "AUTO_REJECT")
        self.assertIsNone(error)
        self.assertEqual(task.action, "REJECT")
        self.assertEqual(task.comment, "系统自动驳回（超时）")
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)

    def test_handle_timeout_escalate(self):
        """测试升级处理"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(timeout_action="ESCALATE")

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "ESCALATE")
        self.assertIsNone(error)
        self.assertEqual(task.status, "EXPIRED")

    def test_handle_timeout_unknown_action(self):
        """测试未知超时动作"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(timeout_action="UNKNOWN")

        action, error = self.executor.handle_timeout(task)

        self.assertEqual(action, "EXPIRED")
        self.assertIsNone(error)
        self.assertEqual(task.status, "EXPIRED")

    def test_handle_timeout_default_action(self):
        """测试默认超时动作"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(timeout_action=None)

        action, error = self.executor.handle_timeout(task)

        # 默认为REMIND
        self.assertEqual(action, "REMIND")
        self.assertEqual(task.remind_count, 1)


class TestEdgeCases(TestApprovalNodeExecutor):
    """测试边界情况"""

    def _create_mock_countersign_result(
        self, approved_count=0, rejected_count=0, pending_count=3
    ):
        """创建mock会签结果"""
        result = Mock()
        result.instance_id = 1
        result.node_id = 1
        result.approved_count = approved_count
        result.rejected_count = rejected_count
        result.pending_count = pending_count
        result.final_result = "PENDING"
        return result

    def test_create_tasks_with_single_approver_list(self):
        """测试单个审批人的列表（各种模式）"""
        instance = self._create_mock_instance()
        approver_ids = [101]

        for mode in ["SINGLE", "OR_SIGN", "AND_SIGN", "SEQUENTIAL"]:
            with self.subTest(mode=mode):
                node = self._create_mock_node(approval_mode=mode)
                self.mock_db.reset_mock()

                added_objects = []
                self.mock_db.add.side_effect = lambda obj: added_objects.append(obj)

                tasks = self.executor.create_tasks_for_node(
                    instance, node, approver_ids
                )

                self.assertEqual(len(tasks), 1)

    def test_process_approval_with_all_parameters(self):
        """测试带所有参数的审批处理"""
        task = self._create_mock_task()
        task.node = self._create_mock_node()

        can_proceed, error = self.executor.process_approval(
            task,
            action="APPROVE",
            comment="同意，但有建议",
            attachments=[{"name": "file1.pdf"}, {"name": "file2.docx"}],
            eval_data={
                "cost_estimate": 8000,
                "schedule_estimate": 5,
                "risk_assessment": "高",
                "custom_field": "自定义值",
            },
        )

        # 验证所有参数都被正确设置
        self.assertEqual(task.action, "APPROVE")
        self.assertEqual(task.comment, "同意，但有建议")
        self.assertEqual(len(task.attachments), 2)
        self.assertEqual(task.eval_data["custom_field"], "自定义值")
        self.assertTrue(can_proceed)

    def test_countersign_default_pass_rule(self):
        """测试会签默认通过规则"""
        task = self._create_mock_task()
        task.node = self._create_mock_node(
            approver_config={}  # 空配置，应使用默认ALL规则
        )
        result = self._create_mock_countersign_result(
            approved_count=2, rejected_count=1, pending_count=1
        )

        self.mock_db.query.return_value.filter.return_value.first.return_value = result

        with patch.object(self.executor, "_summarize_eval_data"):
            can_proceed, error = self.executor._process_countersign(task, "REJECT")

        # 默认ALL规则，有驳回则失败
        self.assertEqual(result.final_result, "FAILED")


if __name__ == "__main__":
    unittest.main()

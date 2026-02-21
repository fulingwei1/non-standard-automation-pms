# -*- coding: utf-8 -*-
"""
外协工作流服务增强单元测试

全面测试 OutsourcingWorkflowService 业务逻辑，目标覆盖率 70%+
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from app.services.outsourcing_workflow import OutsourcingWorkflowService


class TestOutsourcingWorkflowServiceEnhanced(unittest.TestCase):
    """外协工作流服务增强测试类"""

    def setUp(self):
        """测试准备"""
        self.db_mock = MagicMock()
        self.service = OutsourcingWorkflowService(self.db_mock)

    def tearDown(self):
        """测试清理"""
        self.db_mock.reset_mock()

    # ==================== 初始化测试 ====================

    def test_init_creates_service_with_db_session(self):
        """测试服务初始化创建数据库会话"""
        self.assertIsNotNone(self.service.db)
        self.assertEqual(self.service.db, self.db_mock)

    def test_init_creates_approval_engine(self):
        """测试服务初始化创建审批引擎"""
        self.assertIsNotNone(self.service.engine)

    # ==================== submit_orders_for_approval 测试 ====================

    def test_submit_single_order_success(self):
        """测试提交单个订单审批成功"""
        order_mock = self._create_order_mock(1, "OUT-001", "DRAFT")
        self.db_mock.query.return_value.filter.return_value.first.return_value = order_mock

        instance_mock = MagicMock()
        instance_mock.id = 100
        self.service.engine.submit = MagicMock(return_value=instance_mock)

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=10, urgency="NORMAL", comment="测试提交"
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["order_id"], 1)
        self.assertEqual(result["success"][0]["order_no"], "OUT-001")
        self.assertEqual(result["success"][0]["instance_id"], 100)
        self.assertEqual(result["success"][0]["status"], "submitted")

    def test_submit_multiple_orders_success(self):
        """测试批量提交多个订单审批成功"""
        order1 = self._create_order_mock(1, "OUT-001", "DRAFT")
        order2 = self._create_order_mock(2, "OUT-002", "REJECTED")

        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            order1, order2
        ]

        instance_mock1 = MagicMock(id=100)
        instance_mock2 = MagicMock(id=101)
        self.service.engine.submit = MagicMock(side_effect=[instance_mock1, instance_mock2])

        result = self.service.submit_orders_for_approval(
            order_ids=[1, 2], initiator_id=10, urgency="HIGH"
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.engine.submit.call_count, 2)

    def test_submit_order_not_found(self):
        """测试提交不存在的订单"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        result = self.service.submit_orders_for_approval(
            order_ids=[999], initiator_id=10
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["order_id"], 999)
        self.assertIn("不存在", result["errors"][0]["error"])

    def test_submit_order_invalid_status_approved(self):
        """测试提交已审批通过的订单"""
        order_mock = self._create_order_mock(1, "OUT-001", "APPROVED")
        self.db_mock.query.return_value.filter.return_value.first.return_value = order_mock

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=10
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_submit_order_invalid_status_pending(self):
        """测试提交审批中的订单"""
        order_mock = self._create_order_mock(1, "OUT-001", "PENDING_APPROVAL")
        self.db_mock.query.return_value.filter.return_value.first.return_value = order_mock

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=10
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)

    def test_submit_order_with_null_amount(self):
        """测试提交含税金额为空的订单"""
        order_mock = self._create_order_mock(1, "OUT-001", "DRAFT")
        order_mock.amount_with_tax = None

        self.db_mock.query.return_value.filter.return_value.first.return_value = order_mock

        instance_mock = MagicMock(id=100)
        self.service.engine.submit = MagicMock(return_value=instance_mock)

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=10
        )

        self.assertEqual(len(result["success"]), 1)
        # 验证传递给引擎的数据中 amount_with_tax 为 0
        call_args = self.service.engine.submit.call_args
        self.assertEqual(call_args[1]["form_data"]["amount_with_tax"], 0)

    def test_submit_order_engine_exception(self):
        """测试提交时审批引擎抛出异常"""
        order_mock = self._create_order_mock(1, "OUT-001", "DRAFT")
        self.db_mock.query.return_value.filter.return_value.first.return_value = order_mock

        self.service.engine.submit = MagicMock(side_effect=Exception("引擎错误"))

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=10
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("引擎错误", result["errors"][0]["error"])

    def test_submit_mixed_success_and_failure(self):
        """测试部分成功部分失败的批量提交"""
        order1 = self._create_order_mock(1, "OUT-001", "DRAFT")
        order2_none = None  # 不存在
        order3 = self._create_order_mock(3, "OUT-003", "APPROVED")  # 状态不允许

        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            order1, order2_none, order3
        ]

        instance_mock = MagicMock(id=100)
        self.service.engine.submit = MagicMock(return_value=instance_mock)

        result = self.service.submit_orders_for_approval(
            order_ids=[1, 2, 3], initiator_id=10
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 2)

    # ==================== get_pending_tasks 测试 ====================

    def test_get_pending_tasks_with_results(self):
        """测试获取待审批任务列表（有任务）"""
        task_mock = self._create_task_mock(1, 100, 1)
        order_mock = self._create_order_mock(1, "OUT-001", "PENDING_APPROVAL")

        self.service.engine.get_pending_tasks = MagicMock(return_value=[task_mock])
        self.db_mock.query.return_value.filter.return_value.first.return_value = order_mock

        result = self.service.get_pending_tasks(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["order_no"], "OUT-001")

    def test_get_pending_tasks_empty_list(self):
        """测试获取待审批任务列表（无任务）"""
        self.service.engine.get_pending_tasks = MagicMock(return_value=[])

        result = self.service.get_pending_tasks(user_id=10)

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_pending_tasks_pagination(self):
        """测试分页获取待审批任务"""
        tasks = [self._create_task_mock(i, 100 + i, i) for i in range(1, 16)]
        self.service.engine.get_pending_tasks = MagicMock(return_value=tasks)

        orders = [self._create_order_mock(i, f"OUT-{i:03d}", "PENDING_APPROVAL") for i in range(1, 16)]
        self.db_mock.query.return_value.filter.return_value.first.side_effect = orders[:10]

        result = self.service.get_pending_tasks(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 15)
        self.assertEqual(len(result["items"]), 10)

    def test_get_pending_tasks_second_page(self):
        """测试获取第二页待审批任务"""
        tasks = [self._create_task_mock(i, 100 + i, i) for i in range(1, 16)]
        self.service.engine.get_pending_tasks = MagicMock(return_value=tasks)

        orders = [self._create_order_mock(i, f"OUT-{i:03d}", "PENDING_APPROVAL") for i in range(11, 16)]
        self.db_mock.query.return_value.filter.return_value.first.side_effect = orders

        result = self.service.get_pending_tasks(user_id=10, offset=10, limit=10)

        self.assertEqual(result["total"], 15)
        self.assertEqual(len(result["items"]), 5)

    def test_get_pending_tasks_order_not_found(self):
        """测试获取任务时订单不存在"""
        task_mock = self._create_task_mock(1, 100, 999)
        self.service.engine.get_pending_tasks = MagicMock(return_value=[task_mock])
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_pending_tasks(user_id=10)

        self.assertEqual(len(result["items"]), 1)
        self.assertIsNone(result["items"][0]["order_no"])
        self.assertIsNone(result["items"][0]["order_title"])

    def test_get_pending_tasks_without_vendor(self):
        """测试获取任务时订单无供应商"""
        task_mock = self._create_task_mock(1, 100, 1)
        order_mock = self._create_order_mock(1, "OUT-001", "PENDING_APPROVAL")
        order_mock.vendor = None

        self.service.engine.get_pending_tasks = MagicMock(return_value=[task_mock])
        self.db_mock.query.return_value.filter.return_value.first.return_value = order_mock

        result = self.service.get_pending_tasks(user_id=10)

        self.assertIsNone(result["items"][0]["vendor_name"])

    def test_get_pending_tasks_without_project(self):
        """测试获取任务时订单无项目"""
        task_mock = self._create_task_mock(1, 100, 1)
        order_mock = self._create_order_mock(1, "OUT-001", "PENDING_APPROVAL")
        order_mock.project = None

        self.service.engine.get_pending_tasks = MagicMock(return_value=[task_mock])
        self.db_mock.query.return_value.filter.return_value.first.return_value = order_mock

        result = self.service.get_pending_tasks(user_id=10)

        self.assertIsNone(result["items"][0]["project_name"])

    # ==================== perform_approval_action 测试 ====================

    def test_perform_approval_action_approve_success(self):
        """测试执行审批通过成功"""
        result_mock = MagicMock()
        result_mock.status = "APPROVED"
        result_mock.entity_id = 1

        self.service.engine.approve = MagicMock(return_value=result_mock)
        self.service._trigger_cost_collection = MagicMock()

        result = self.service.perform_approval_action(
            task_id=1, approver_id=10, action="approve", comment="同意"
        )

        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service._trigger_cost_collection.assert_called_once_with(1, 10)

    def test_perform_approval_action_approve_pending(self):
        """测试审批通过但流程未结束"""
        result_mock = MagicMock()
        result_mock.status = "PENDING"
        result_mock.entity_id = 1

        self.service.engine.approve = MagicMock(return_value=result_mock)
        self.service._trigger_cost_collection = MagicMock()

        result = self.service.perform_approval_action(
            task_id=1, approver_id=10, action="approve"
        )

        self.assertEqual(result["instance_status"], "PENDING")
        self.service._trigger_cost_collection.assert_not_called()

    def test_perform_approval_action_reject_success(self):
        """测试执行审批驳回成功"""
        result_mock = MagicMock()
        result_mock.status = "REJECTED"

        self.service.engine.reject = MagicMock(return_value=result_mock)

        result = self.service.perform_approval_action(
            task_id=1, approver_id=10, action="reject", comment="不同意"
        )

        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")

    def test_perform_approval_action_invalid_action(self):
        """测试执行审批时传入无效操作"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_approval_action(
                task_id=1, approver_id=10, action="cancel"
            )

        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_approval_action_empty_action(self):
        """测试执行审批时操作为空字符串"""
        with self.assertRaises(ValueError):
            self.service.perform_approval_action(
                task_id=1, approver_id=10, action=""
            )

    # ==================== perform_batch_approval 测试 ====================

    def test_perform_batch_approval_all_success(self):
        """测试批量审批全部成功"""
        result_mock = MagicMock()
        result_mock.status = "APPROVED"
        result_mock.entity_id = 1

        self.service.engine.approve = MagicMock(return_value=result_mock)
        self.service._trigger_cost_collection = MagicMock()

        result = self.service.perform_batch_approval(
            task_ids=[1, 2, 3], approver_id=10, action="approve"
        )

        self.assertEqual(len(result["success"]), 3)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.engine.approve.call_count, 3)

    def test_perform_batch_approval_reject(self):
        """测试批量驳回"""
        self.service.engine.reject = MagicMock()

        result = self.service.perform_batch_approval(
            task_ids=[1, 2], approver_id=10, action="reject", comment="批量驳回"
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.engine.reject.call_count, 2)

    def test_perform_batch_approval_partial_failure(self):
        """测试批量审批部分失败"""
        self.service.engine.approve = MagicMock(
            side_effect=[MagicMock(status="APPROVED", entity_id=1), Exception("审批失败")]
        )
        self.service._trigger_cost_collection = MagicMock()

        result = self.service.perform_batch_approval(
            task_ids=[1, 2], approver_id=10, action="approve"
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("审批失败", result["errors"][0]["error"])

    def test_perform_batch_approval_invalid_action(self):
        """测试批量审批时传入无效操作"""
        result = self.service.perform_batch_approval(
            task_ids=[1, 2], approver_id=10, action="invalid"
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 2)
        for error in result["errors"]:
            self.assertIn("不支持的操作", error["error"])

    def test_perform_batch_approval_empty_task_ids(self):
        """测试批量审批时任务ID列表为空"""
        result = self.service.perform_batch_approval(
            task_ids=[], approver_id=10, action="approve"
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 0)

    # ==================== get_approval_status 测试 ====================

    def test_get_approval_status_with_instance(self):
        """测试查询审批状态（有审批实例）"""
        order_mock = self._create_order_mock(1, "OUT-001", "PENDING_APPROVAL")
        instance_mock = self._create_instance_mock(100, 1, "PENDING")
        task_mock = self._create_task_for_status(1, "PENDING", None)

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = order_mock
        query_mock.filter.return_value.order_by.return_value.first.return_value = instance_mock
        query_mock.filter.return_value.order_by.return_value.all.return_value = [task_mock]

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "OUT-001")
        self.assertEqual(result["instance_id"], 100)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)

    def test_get_approval_status_no_instance(self):
        """测试查询审批状态（无审批实例）"""
        order_mock = self._create_order_mock(1, "OUT-001", "DRAFT")

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = order_mock
        query_mock.filter.return_value.order_by.return_value.first.return_value = None

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "OUT-001")
        self.assertIsNone(result["approval_instance"])

    def test_get_approval_status_order_not_found(self):
        """测试查询审批状态时订单不存在"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_approval_status(order_id=999)

        self.assertIn("不存在", str(context.exception))

    def test_get_approval_status_completed_instance(self):
        """测试查询已完成的审批状态"""
        order_mock = self._create_order_mock(1, "OUT-001", "APPROVED")
        instance_mock = self._create_instance_mock(100, 1, "APPROVED")
        instance_mock.completed_at = datetime(2026, 2, 20, 15, 0, 0)

        task1 = self._create_task_for_status(1, "APPROVED", "approve")
        task1.completed_at = datetime(2026, 2, 20, 14, 0, 0)
        task2 = self._create_task_for_status(2, "APPROVED", "approve")
        task2.completed_at = datetime(2026, 2, 20, 15, 0, 0)

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = order_mock
        query_mock.filter.return_value.order_by.return_value.first.return_value = instance_mock
        query_mock.filter.return_value.order_by.return_value.all.return_value = [task1, task2]

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["instance_status"], "APPROVED")
        self.assertIsNotNone(result["completed_at"])
        self.assertEqual(len(result["task_history"]), 2)

    # ==================== withdraw_approval 测试 ====================

    def test_withdraw_approval_success(self):
        """测试撤回审批成功"""
        order_mock = self._create_order_mock(1, "OUT-001", "PENDING_APPROVAL")
        instance_mock = MagicMock()
        instance_mock.id = 100
        instance_mock.initiator_id = 10

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.side_effect = [order_mock, instance_mock]

        self.service.engine.withdraw = MagicMock()

        result = self.service.withdraw_approval(order_id=1, user_id=10, reason="撤回测试")

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "OUT-001")
        self.assertEqual(result["status"], "withdrawn")
        self.service.engine.withdraw.assert_called_once_with(instance_id=100, user_id=10)

    def test_withdraw_approval_order_not_found(self):
        """测试撤回审批时订单不存在"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=999, user_id=10)

        self.assertIn("不存在", str(context.exception))

    def test_withdraw_approval_no_pending_instance(self):
        """测试撤回审批时没有进行中的审批"""
        order_mock = self._create_order_mock(1, "OUT-001", "APPROVED")

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.side_effect = [order_mock, None]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=10)

        self.assertIn("没有进行中的审批", str(context.exception))

    def test_withdraw_approval_not_initiator(self):
        """测试撤回审批时不是发起人"""
        order_mock = self._create_order_mock(1, "OUT-001", "PENDING_APPROVAL")
        instance_mock = MagicMock()
        instance_mock.initiator_id = 10

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.side_effect = [order_mock, instance_mock]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=20)

        self.assertIn("只能撤回自己提交的审批", str(context.exception))

    # ==================== get_approval_history 测试 ====================

    def test_get_approval_history_with_results(self):
        """测试获取审批历史（有记录）"""
        task_mock = MagicMock()
        task_mock.id = 1
        task_mock.action = "approve"
        task_mock.status = "APPROVED"
        task_mock.comment = "同意"
        task_mock.completed_at = datetime(2026, 2, 20, 12, 0, 0)

        instance_mock = MagicMock()
        instance_mock.entity_id = 1
        task_mock.instance = instance_mock

        order_mock = self._create_order_mock(1, "OUT-001", "APPROVED")

        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 1
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [task_mock]
        query_mock.filter.return_value.first.return_value = order_mock

        result = self.service.get_approval_history(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["action"], "approve")

    def test_get_approval_history_empty(self):
        """测试获取审批历史（无记录）"""
        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 0
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = self.service.get_approval_history(user_id=10)

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_approval_history_with_status_filter(self):
        """测试获取审批历史（带状态筛选）"""
        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.join.return_value.filter.return_value
        filter_mock.filter.return_value.count.return_value = 5
        filter_mock.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = self.service.get_approval_history(
            user_id=10, offset=0, limit=10, status_filter="APPROVED"
        )

        self.assertEqual(result["total"], 5)

    def test_get_approval_history_pagination(self):
        """测试审批历史分页"""
        tasks = []
        for i in range(1, 21):
            task = MagicMock()
            task.id = i
            task.action = "approve"
            task.status = "APPROVED"
            task.comment = f"第{i}个"
            task.completed_at = datetime(2026, 2, 20, 10, i, 0)
            task.instance = MagicMock(entity_id=i)
            tasks.append(task)

        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 20
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = tasks[:10]

        orders = [self._create_order_mock(i, f"OUT-{i:03d}", "APPROVED") for i in range(1, 11)]
        self.db_mock.query.return_value.filter.return_value.first.side_effect = orders

        result = self.service.get_approval_history(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 20)
        self.assertEqual(len(result["items"]), 10)

    # ==================== _trigger_cost_collection 测试 ====================

    @patch("app.services.outsourcing_workflow.outsourcing_workflow_service.logger")
    @patch("app.services.cost_collection_service.CostCollectionService")
    def test_trigger_cost_collection_success(self, mock_service_class, mock_logger):
        """测试触发成本归集成功"""
        mock_service_class.collect_from_outsourcing_order = MagicMock()

        self.service._trigger_cost_collection(order_id=1, user_id=10)

        mock_service_class.collect_from_outsourcing_order.assert_called_once_with(
            self.db_mock, 1, created_by=10
        )
        mock_logger.error.assert_not_called()

    @patch("app.services.outsourcing_workflow.outsourcing_workflow_service.logger")
    @patch("app.services.cost_collection_service.CostCollectionService")
    def test_trigger_cost_collection_failure(self, mock_service_class, mock_logger):
        """测试触发成本归集失败"""
        mock_service_class.collect_from_outsourcing_order = MagicMock(
            side_effect=Exception("成本归集失败")
        )

        self.service._trigger_cost_collection(order_id=1, user_id=10)

        mock_logger.error.assert_called_once()
        self.assertIn("Failed to collect cost", mock_logger.error.call_args[0][0])

    @patch("app.services.outsourcing_workflow.outsourcing_workflow_service.logger")
    def test_trigger_cost_collection_import_error(self, mock_logger):
        """测试成本归集服务导入失败"""
        with patch("builtins.__import__", side_effect=ImportError("模块不存在")):
            self.service._trigger_cost_collection(order_id=1, user_id=10)

            mock_logger.error.assert_called_once()

    # ==================== 辅助方法 ====================

    def _create_order_mock(self, order_id, order_no, status):
        """创建订单Mock对象"""
        order = MagicMock()
        order.id = order_id
        order.order_no = order_no
        order.order_title = f"订单标题 {order_no}"
        order.order_type = "SERVICE"
        order.status = status
        order.amount_with_tax = Decimal("10000.00")
        order.vendor_id = 1
        order.project_id = 1
        order.machine_id = None
        order.vendor = MagicMock(vendor_name="供应商A")
        order.project = MagicMock(project_name="项目A")
        return order

    def _create_task_mock(self, task_id, instance_id, entity_id):
        """创建任务Mock对象"""
        task = MagicMock()
        task.id = task_id

        instance = MagicMock()
        instance.id = instance_id
        instance.entity_id = entity_id
        instance.urgency = "NORMAL"
        instance.created_at = datetime(2026, 2, 20, 10, 0, 0)
        instance.initiator = MagicMock(real_name="张三")

        task.instance = instance
        task.node = MagicMock(node_name="部门审批")

        return task

    def _create_instance_mock(self, instance_id, entity_id, status):
        """创建审批实例Mock对象"""
        instance = MagicMock()
        instance.id = instance_id
        instance.entity_id = entity_id
        instance.status = status
        instance.urgency = "NORMAL"
        instance.created_at = datetime(2026, 2, 20, 10, 0, 0)
        instance.completed_at = None
        return instance

    def _create_task_for_status(self, task_id, status, action):
        """创建用于状态查询的任务Mock对象"""
        task = MagicMock()
        task.id = task_id
        task.status = status
        task.action = action
        task.comment = None
        task.completed_at = None
        task.node = MagicMock(node_name="审批节点")
        task.assignee = MagicMock(real_name="李四")
        return task


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
外协工作流服务单元测试

测试 OutsourcingWorkflowService 业务逻辑。
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.outsourcing_workflow import OutsourcingWorkflowService


class TestOutsourcingWorkflowService(unittest.TestCase):
    """外协工作流服务测试类"""

    def setUp(self):
        """测试准备"""
        self.db_mock = MagicMock()
        self.service = OutsourcingWorkflowService(self.db_mock)

    def test_init(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.engine)

    def test_submit_orders_for_approval_success(self):
        """测试提交审批成功"""
        # Mock 订单
        order_mock = MagicMock()
        order_mock.id = 1
        order_mock.order_no = "OUT-001"
        order_mock.order_title = "测试订单"
        order_mock.order_type = "SERVICE"
        order_mock.status = "DRAFT"
        order_mock.amount_with_tax = 10000.00
        order_mock.vendor_id = 1
        order_mock.project_id = 1
        order_mock.machine_id = None

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            order_mock
        )

        # Mock 审批引擎
        instance_mock = MagicMock()
        instance_mock.id = 100
        self.service.engine.submit = MagicMock(return_value=instance_mock)

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=10, urgency="NORMAL"
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["order_id"], 1)
        self.assertEqual(result["success"][0]["instance_id"], 100)

    def test_submit_orders_order_not_found(self):
        """测试提交审批时订单不存在"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        result = self.service.submit_orders_for_approval(
            order_ids=[999], initiator_id=10, urgency="NORMAL"
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不存在", result["errors"][0]["error"])

    def test_submit_orders_invalid_status(self):
        """测试提交审批时订单状态不允许"""
        order_mock = MagicMock()
        order_mock.status = "APPROVED"

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            order_mock
        )

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=10, urgency="NORMAL"
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_get_pending_tasks(self):
        """测试获取待审批任务列表"""
        # Mock 任务
        task_mock = MagicMock()
        task_mock.id = 1
        instance_mock = MagicMock()
        instance_mock.id = 100
        instance_mock.entity_id = 1
        instance_mock.urgency = "NORMAL"
        instance_mock.created_at = datetime(2026, 2, 20, 10, 0, 0)
        instance_mock.initiator.real_name = "张三"
        task_mock.instance = instance_mock

        node_mock = MagicMock()
        node_mock.node_name = "部门审批"
        task_mock.node = node_mock

        order_mock = MagicMock()
        order_mock.order_no = "OUT-001"
        order_mock.order_title = "测试订单"
        order_mock.order_type = "SERVICE"
        order_mock.amount_with_tax = 10000.00
        order_mock.vendor = MagicMock(vendor_name="供应商A")
        order_mock.project = MagicMock(project_name="项目A")

        self.service.engine.get_pending_tasks = MagicMock(return_value=[task_mock])
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            order_mock
        )

        result = self.service.get_pending_tasks(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["order_no"], "OUT-001")

    def test_perform_approval_action_approve(self):
        """测试执行审批通过操作"""
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

    def test_perform_approval_action_reject(self):
        """测试执行审批驳回操作"""
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
                task_id=1, approver_id=10, action="invalid", comment=None
            )

        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_batch_approval(self):
        """测试批量审批"""
        result_mock = MagicMock()
        result_mock.status = "APPROVED"
        result_mock.entity_id = 1

        self.service.engine.approve = MagicMock(return_value=result_mock)
        self.service._trigger_cost_collection = MagicMock()

        result = self.service.perform_batch_approval(
            task_ids=[1, 2], approver_id=10, action="approve", comment="批量同意"
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 0)

    def test_get_approval_status_with_instance(self):
        """测试查询审批状态（有审批实例）"""
        order_mock = MagicMock()
        order_mock.id = 1
        order_mock.order_no = "OUT-001"
        order_mock.status = "PENDING_APPROVAL"

        instance_mock = MagicMock()
        instance_mock.id = 100
        instance_mock.status = "PENDING"
        instance_mock.urgency = "NORMAL"
        instance_mock.created_at = datetime(2026, 2, 20, 10, 0, 0)
        instance_mock.completed_at = None

        task_mock = MagicMock()
        task_mock.id = 1
        task_mock.status = "PENDING"
        task_mock.action = None
        task_mock.comment = None
        task_mock.completed_at = None
        task_mock.node = MagicMock(node_name="部门审批")
        task_mock.assignee = MagicMock(real_name="李四")

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = order_mock
        query_mock.filter.return_value.order_by.return_value.first.return_value = (
            instance_mock
        )
        query_mock.filter.return_value.order_by.return_value.all.return_value = [
            task_mock
        ]

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["instance_id"], 100)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)

    def test_get_approval_status_no_instance(self):
        """测试查询审批状态（无审批实例）"""
        order_mock = MagicMock()
        order_mock.id = 1
        order_mock.order_no = "OUT-001"
        order_mock.status = "DRAFT"

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = order_mock
        query_mock.filter.return_value.order_by.return_value.first.return_value = None

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertIsNone(result["approval_instance"])

    def test_get_approval_status_order_not_found(self):
        """测试查询审批状态时订单不存在"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_approval_status(order_id=999)

        self.assertIn("不存在", str(context.exception))

    def test_withdraw_approval_success(self):
        """测试撤回审批成功"""
        order_mock = MagicMock()
        order_mock.id = 1
        order_mock.order_no = "OUT-001"

        instance_mock = MagicMock()
        instance_mock.id = 100
        instance_mock.initiator_id = 10

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.side_effect = [order_mock, instance_mock]

        self.service.engine.withdraw = MagicMock()

        result = self.service.withdraw_approval(order_id=1, user_id=10, reason="测试")

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.service.engine.withdraw.assert_called_once_with(instance_id=100, user_id=10)

    def test_withdraw_approval_not_initiator(self):
        """测试撤回审批时不是发起人"""
        order_mock = MagicMock()
        order_mock.id = 1

        instance_mock = MagicMock()
        instance_mock.initiator_id = 10

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.side_effect = [order_mock, instance_mock]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=20, reason="测试")

        self.assertIn("只能撤回自己提交的审批", str(context.exception))

    def test_get_approval_history(self):
        """测试获取审批历史"""
        task_mock = MagicMock()
        task_mock.id = 1
        task_mock.action = "approve"
        task_mock.status = "APPROVED"
        task_mock.comment = "同意"
        task_mock.completed_at = datetime(2026, 2, 20, 12, 0, 0)

        instance_mock = MagicMock()
        instance_mock.entity_id = 1
        task_mock.instance = instance_mock

        order_mock = MagicMock()
        order_mock.order_no = "OUT-001"
        order_mock.order_title = "测试订单"
        order_mock.order_type = "SERVICE"
        order_mock.amount_with_tax = 10000.00

        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 1
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            task_mock
        ]
        query_mock.filter.return_value.first.return_value = order_mock

        result = self.service.get_approval_history(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["action"], "approve")

    @patch("app.services.outsourcing_workflow.outsourcing_workflow_service.logger")
    def test_trigger_cost_collection_success(self, mock_logger):
        """测试触发成本归集成功"""
        with patch(
            "app.services.outsourcing_workflow.outsourcing_workflow_service.CostCollectionService"
        ) as mock_service:
            mock_service.collect_from_outsourcing_order = MagicMock()

            self.service._trigger_cost_collection(order_id=1, user_id=10)

            mock_service.collect_from_outsourcing_order.assert_called_once_with(
                self.db_mock, 1, created_by=10
            )
            mock_logger.error.assert_not_called()

    @patch("app.services.outsourcing_workflow.outsourcing_workflow_service.logger")
    def test_trigger_cost_collection_failure(self, mock_logger):
        """测试触发成本归集失败"""
        with patch(
            "app.services.outsourcing_workflow.outsourcing_workflow_service.CostCollectionService"
        ) as mock_service:
            mock_service.collect_from_outsourcing_order = MagicMock(
                side_effect=Exception("成本归集失败")
            )

            self.service._trigger_cost_collection(order_id=1, user_id=10)

            mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()

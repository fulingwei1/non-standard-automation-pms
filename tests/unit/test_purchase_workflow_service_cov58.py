# -*- coding: utf-8 -*-
"""
采购工作流服务单元测试

测试 PurchaseWorkflowService 的所有核心方法。
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.purchase_workflow.service import PurchaseWorkflowService


class TestPurchaseWorkflowService(unittest.TestCase):
    """采购工作流服务测试类"""

    def setUp(self):
        """初始化测试环境"""
        self.db = MagicMock()
        self.service = PurchaseWorkflowService(self.db)

    def test_submit_orders_success(self):
        """测试成功提交采购订单审批"""
        # Mock 数据
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "DRAFT"
        mock_order.order_no = "PO-2024-001"
        mock_order.order_title = "测试订单"
        mock_order.amount_with_tax = 1000.00
        mock_order.supplier_id = 10
        mock_order.project_id = 20

        mock_instance = MagicMock()
        mock_instance.id = 100

        self.db.query.return_value.filter.return_value.first.return_value = mock_order
        self.service.engine.submit = MagicMock(return_value=mock_instance)

        # 执行测试
        result = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=5,
            urgency="HIGH",
        )

        # 验证结果
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["order_id"], 1)
        self.assertEqual(result["success"][0]["instance_id"], 100)

    def test_submit_orders_order_not_found(self):
        """测试提交不存在的订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.submit_orders_for_approval(
            order_ids=[999],
            initiator_id=5,
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["order_id"], 999)
        self.assertIn("不存在", result["errors"][0]["error"])

    def test_submit_orders_invalid_status(self):
        """测试提交状态不允许的订单"""
        mock_order = MagicMock()
        mock_order.status = "APPROVED"

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        result = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=5,
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交", result["errors"][0]["error"])

    def test_get_pending_tasks(self):
        """测试获取待审批任务列表"""
        # Mock 数据
        mock_task = MagicMock()
        mock_task.id = 1
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.entity_id = 10
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_instance.urgency = "HIGH"
        mock_instance.initiator.real_name = "张三"
        mock_task.instance = mock_instance

        mock_node = MagicMock()
        mock_node.node_name = "部门审批"
        mock_task.node = mock_node

        mock_order = MagicMock()
        mock_order.order_no = "PO-2024-001"
        mock_order.order_title = "测试订单"
        mock_order.amount_with_tax = 5000.00
        mock_supplier = MagicMock()
        mock_supplier.vendor_name = "供应商A"
        mock_order.supplier = mock_supplier

        self.service.engine.get_pending_tasks = MagicMock(return_value=[mock_task])
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        # 执行测试
        result = self.service.get_pending_tasks(user_id=5, offset=0, limit=20)

        # 验证结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["order_no"], "PO-2024-001")
        self.assertEqual(result["items"][0]["urgency"], "HIGH")

    def test_perform_approval_action_approve(self):
        """测试审批通过操作"""
        mock_result = MagicMock()
        mock_result.status = "APPROVED"

        self.service.engine.approve = MagicMock(return_value=mock_result)

        result = self.service.perform_approval_action(
            task_id=1,
            action="approve",
            approver_id=5,
            comment="同意",
        )

        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service.engine.approve.assert_called_once_with(
            task_id=1,
            approver_id=5,
            comment="同意",
        )

    def test_perform_approval_action_reject(self):
        """测试审批驳回操作"""
        mock_result = MagicMock()
        mock_result.status = "REJECTED"

        self.service.engine.reject = MagicMock(return_value=mock_result)

        result = self.service.perform_approval_action(
            task_id=1,
            action="reject",
            approver_id=5,
            comment="不同意",
        )

        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")

    def test_perform_approval_action_invalid(self):
        """测试无效的审批操作类型"""
        with self.assertRaises(HTTPException) as context:
            self.service.perform_approval_action(
                task_id=1,
                action="invalid_action",
                approver_id=5,
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("不支持", context.exception.detail)

    def test_perform_batch_approval(self):
        """测试批量审批操作"""
        self.service.engine.approve = MagicMock()

        result = self.service.perform_batch_approval(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=5,
            comment="批量通过",
        )

        self.assertEqual(len(result["success"]), 3)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.engine.approve.call_count, 3)

    def test_get_approval_status_with_instance(self):
        """测试查询有审批记录的订单状态"""
        mock_order = MagicMock()
        mock_order.order_no = "PO-2024-001"
        mock_order.status = "PENDING"

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.urgency = "HIGH"
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_instance.completed_at = None

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "PENDING"
        mock_task.action = None
        mock_task.comment = None
        mock_task.completed_at = None
        mock_node = MagicMock()
        mock_node.node_name = "部门审批"
        mock_task.node = mock_node
        mock_assignee = MagicMock()
        mock_assignee.real_name = "李四"
        mock_task.assignee = mock_assignee

        with patch("app.services.purchase_workflow.service.get_or_404", return_value=mock_order):
            self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_instance
            self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task]

            result = self.service.get_approval_status(order_id=1)

            self.assertEqual(result["order_id"], 1)
            self.assertEqual(result["instance_id"], 100)
            self.assertEqual(result["instance_status"], "PENDING")
            self.assertEqual(len(result["task_history"]), 1)

    def test_get_approval_status_no_instance(self):
        """测试查询无审批记录的订单状态"""
        mock_order = MagicMock()
        mock_order.order_no = "PO-2024-001"
        mock_order.status = "DRAFT"

        with patch("app.services.purchase_workflow.service.get_or_404", return_value=mock_order):
            self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

            result = self.service.get_approval_status(order_id=1)

            self.assertEqual(result["order_id"], 1)
            self.assertIsNone(result["approval_instance"])

    def test_withdraw_approval_success(self):
        """测试成功撤回审批"""
        mock_order = MagicMock()
        mock_order.order_no = "PO-2024-001"

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.initiator_id = 5
        mock_instance.status = "PENDING"

        with patch("app.services.purchase_workflow.service.get_or_404", return_value=mock_order):
            self.db.query.return_value.filter.return_value.first.return_value = mock_instance
            self.service.engine.withdraw = MagicMock()

            result = self.service.withdraw_approval(
                order_id=1,
                user_id=5,
                reason="测试撤回",
            )

            self.assertEqual(result["order_id"], 1)
            self.assertEqual(result["status"], "withdrawn")
            self.service.engine.withdraw.assert_called_once_with(instance_id=100, user_id=5)

    def test_withdraw_approval_no_pending(self):
        """测试撤回无进行中审批的订单"""
        mock_order = MagicMock()

        with patch("app.services.purchase_workflow.service.get_or_404", return_value=mock_order):
            self.db.query.return_value.filter.return_value.first.return_value = None

            with self.assertRaises(HTTPException) as context:
                self.service.withdraw_approval(order_id=1, user_id=5)

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("可撤回", context.exception.detail)

    def test_withdraw_approval_not_initiator(self):
        """测试非发起人撤回审批"""
        mock_order = MagicMock()

        mock_instance = MagicMock()
        mock_instance.initiator_id = 10  # 不同的用户

        with patch("app.services.purchase_workflow.service.get_or_404", return_value=mock_order):
            self.db.query.return_value.filter.return_value.first.return_value = mock_instance

            with self.assertRaises(HTTPException) as context:
                self.service.withdraw_approval(order_id=1, user_id=5)

            self.assertEqual(context.exception.status_code, 403)
            self.assertIn("只能撤回自己", context.exception.detail)

    def test_get_approval_history(self):
        """测试获取审批历史"""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.action = "approve"
        mock_task.status = "APPROVED"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 1, 10, 0, 0)

        mock_instance = MagicMock()
        mock_instance.entity_id = 10
        mock_task.instance = mock_instance

        mock_order = MagicMock()
        mock_order.order_no = "PO-2024-001"
        mock_order.order_title = "测试订单"
        mock_order.amount_with_tax = 3000.00

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_task]

        self.db.query.return_value = mock_query
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        result = self.service.get_approval_history(
            user_id=5,
            offset=0,
            limit=20,
        )

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["action"], "approve")


if __name__ == "__main__":
    unittest.main()

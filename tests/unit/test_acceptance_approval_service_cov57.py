# -*- coding: utf-8 -*-
"""
验收单审批服务层单元测试
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.acceptance_approval import AcceptanceApprovalService


class TestAcceptanceApprovalService(unittest.TestCase):
    """验收单审批服务测试"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = AcceptanceApprovalService(self.db)

    def tearDown(self):
        """测试后清理"""
        self.db = None
        self.service = None

    def test_submit_orders_for_approval_success(self):
        """测试成功提交审批"""
        # Mock 验收单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.status = "COMPLETED"
        mock_order.overall_result = "PASSED"
        mock_order.pass_rate = 95.5
        mock_order.passed_items = 19
        mock_order.failed_items = 1
        mock_order.total_items = 20
        mock_order.project_id = 1
        mock_order.machine_id = 1
        mock_order.conclusion = "验收合格"
        mock_order.conditions = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        # Mock 审批引擎
        mock_instance = MagicMock()
        mock_instance.id = 100
        self.service.engine.submit = MagicMock(return_value=mock_instance)

        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=1, urgency="NORMAL"
        )

        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(results[0]["order_id"], 1)
        self.assertEqual(results[0]["instance_id"], 100)
        self.service.engine.submit.assert_called_once()

    def test_submit_orders_order_not_found(self):
        """测试提交审批时验收单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        results, errors = self.service.submit_orders_for_approval(
            order_ids=[999], initiator_id=1
        )

        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["order_id"], 999)
        self.assertIn("不存在", errors[0]["error"])

    def test_submit_orders_invalid_status(self):
        """测试提交审批时状态无效"""
        mock_order = MagicMock()
        mock_order.status = "DRAFT"
        mock_order.overall_result = "PASSED"

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=1
        )

        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不允许提交审批", errors[0]["error"])

    def test_submit_orders_no_result(self):
        """测试提交审批时无验收结论"""
        mock_order = MagicMock()
        mock_order.status = "COMPLETED"
        mock_order.overall_result = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=1
        )

        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("验收结论", errors[0]["error"])

    def test_get_pending_tasks(self):
        """测试获取待审批任务"""
        # Mock 任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.entity_id = 1
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_instance.urgency = "NORMAL"
        mock_instance.initiator = MagicMock(real_name="张三")
        mock_task.instance = mock_instance
        mock_task.node = MagicMock(node_name="部门经理审批")

        # Mock 验收单
        mock_order = MagicMock()
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"
        mock_order.pass_rate = 95.5
        mock_order.project = MagicMock(project_name="项目A")
        mock_order.machine = MagicMock(machine_code="M001")

        self.service.engine.get_pending_tasks = MagicMock(return_value=[mock_task])
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        items, total = self.service.get_pending_tasks(
            user_id=1, offset=0, limit=20
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["order_no"], "ACC-001")

    def test_perform_approval_action_approve(self):
        """测试审批通过操作"""
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        self.service.engine.approve = MagicMock(return_value=mock_result)

        result = self.service.perform_approval_action(
            task_id=1, action="approve", approver_id=1, comment="同意"
        )

        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service.engine.approve.assert_called_once_with(
            task_id=1, approver_id=1, comment="同意"
        )

    def test_perform_approval_action_reject(self):
        """测试审批驳回操作"""
        mock_result = MagicMock()
        mock_result.status = "REJECTED"
        self.service.engine.reject = MagicMock(return_value=mock_result)

        result = self.service.perform_approval_action(
            task_id=1, action="reject", approver_id=1, comment="不合格"
        )

        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "reject")
        self.service.engine.reject.assert_called_once()

    def test_perform_approval_action_invalid_action(self):
        """测试无效的审批操作"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_approval_action(
                task_id=1, action="invalid", approver_id=1
            )

        self.assertIn("不支持的操作类型", str(context.exception))

    def test_batch_approval_success(self):
        """测试批量审批成功"""
        self.service.engine.approve = MagicMock()

        results, errors = self.service.batch_approval(
            task_ids=[1, 2], action="approve", approver_id=1
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.service.engine.approve.call_count, 2)

    def test_batch_approval_partial_failure(self):
        """测试批量审批部分失败"""
        # 第一个成功，第二个失败
        self.service.engine.approve = MagicMock(
            side_effect=[None, Exception("审批失败")]
        )

        results, errors = self.service.batch_approval(
            task_ids=[1, 2], action="approve", approver_id=1
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["task_id"], 2)

    def test_get_approval_status_found(self):
        """测试获取审批状态（存在）"""
        # Mock 验收单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"
        mock_order.status = "IN_APPROVAL"

        # Mock 审批实例
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.urgency = "NORMAL"
        mock_instance.created_at = datetime(2024, 1, 1)
        mock_instance.completed_at = None

        # Mock 任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.node = MagicMock(node_name="经理审批")
        mock_task.assignee = MagicMock(real_name="李四")
        mock_task.status = "PENDING"
        mock_task.action = None
        mock_task.comment = None
        mock_task.completed_at = None

        # 配置查询返回
        query_results = [mock_order, mock_instance, [mock_task]]
        self.db.query.return_value.filter.return_value.first.side_effect = (
            query_results[:2]
        )
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_instance
        )
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            query_results[2]
        )

        data = self.service.get_approval_status(order_id=1)

        self.assertEqual(data["order_id"], 1)
        self.assertEqual(data["instance_id"], 100)
        self.assertEqual(len(data["task_history"]), 1)

    def test_get_approval_status_not_found(self):
        """测试获取审批状态（验收单不存在）"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_approval_status(order_id=999)

        self.assertIn("不存在", str(context.exception))

    def test_withdraw_approval_success(self):
        """测试成功撤回审批"""
        # Mock 验收单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "ACC-001"

        # Mock 审批实例
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.initiator_id = 1

        query_results = [mock_order, mock_instance]
        self.db.query.return_value.filter.return_value.first.side_effect = query_results

        self.service.engine.withdraw = MagicMock()

        result = self.service.withdraw_approval(order_id=1, user_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.service.engine.withdraw.assert_called_once()

    def test_withdraw_approval_permission_denied(self):
        """测试撤回审批权限不足"""
        mock_order = MagicMock()
        mock_instance = MagicMock()
        mock_instance.initiator_id = 1

        query_results = [mock_order, mock_instance]
        self.db.query.return_value.filter.return_value.first.side_effect = query_results

        with self.assertRaises(PermissionError) as context:
            self.service.withdraw_approval(order_id=1, user_id=2)

        self.assertIn("只能撤回自己提交的审批", str(context.exception))

    def test_get_approval_history(self):
        """测试获取审批历史"""
        # Mock 任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.action = "approve"
        mock_task.status = "APPROVED"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 1)

        # Mock 审批实例
        mock_instance = MagicMock()
        mock_instance.entity_id = 1
        mock_task.instance = mock_instance

        # Mock 验收单
        mock_order = MagicMock()
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"

        # 配置查询
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

        items, total = self.service.get_approval_history(
            user_id=1, offset=0, limit=20
        )

        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 1)


if __name__ == "__main__":
    unittest.main()

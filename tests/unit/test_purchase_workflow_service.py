# -*- coding: utf-8 -*-
"""
采购工作流服务单元测试

目标：
1. 只mock外部依赖（db, engine）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 覆盖率 70%+
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from fastapi import HTTPException

from app.services.purchase_workflow.service import PurchaseWorkflowService


class TestPurchaseWorkflowServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init(self):
        """测试构造函数"""
        mock_db = MagicMock()
        with patch("app.services.purchase_workflow.service.ApprovalEngineService") as MockEngine:
            service = PurchaseWorkflowService(mock_db)
            self.assertEqual(service.db, mock_db)
            MockEngine.assert_called_once_with(mock_db)
            self.assertIsNotNone(service.engine)


class TestSubmitOrdersForApproval(unittest.TestCase):
    """测试提交采购订单审批"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_engine = MagicMock()
        with patch("app.services.purchase_workflow.service.ApprovalEngineService", return_value=self.mock_engine):
            self.service = PurchaseWorkflowService(self.mock_db)

    def test_submit_single_order_success(self):
        """测试提交单个订单成功"""
        # Mock数据库查询
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO2024001"
        mock_order.order_title = "测试采购单"
        mock_order.status = "DRAFT"
        mock_order.amount_with_tax = 5000.00
        mock_order.supplier_id = 10
        mock_order.project_id = 20

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        # Mock审批引擎
        mock_instance = MagicMock()
        mock_instance.id = 100
        self.mock_engine.submit.return_value = mock_instance

        # 执行
        result = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=999,
            urgency="HIGH",
            comment="紧急采购"
        )

        # 验证
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["order_id"], 1)
        self.assertEqual(result["success"][0]["order_no"], "PO2024001")
        self.assertEqual(result["success"][0]["instance_id"], 100)
        self.assertEqual(result["success"][0]["status"], "submitted")

        # 验证engine.submit被正确调用
        self.mock_engine.submit.assert_called_once()
        call_args = self.mock_engine.submit.call_args[1]
        self.assertEqual(call_args["template_code"], "PURCHASE_ORDER_APPROVAL")
        self.assertEqual(call_args["entity_type"], "PURCHASE_ORDER")
        self.assertEqual(call_args["entity_id"], 1)
        self.assertEqual(call_args["initiator_id"], 999)
        self.assertEqual(call_args["urgency"], "HIGH")
        self.assertEqual(call_args["form_data"]["order_no"], "PO2024001")
        self.assertEqual(call_args["form_data"]["amount_with_tax"], 5000.00)

    def test_submit_order_not_found(self):
        """测试订单不存在"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        result = self.service.submit_orders_for_approval(
            order_ids=[999],
            initiator_id=1
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["order_id"], 999)
        self.assertIn("不存在", result["errors"][0]["error"])

    def test_submit_order_invalid_status(self):
        """测试订单状态不允许提交"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "APPROVED"  # 已审批状态不能再次提交

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        result = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=1
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交", result["errors"][0]["error"])

    def test_submit_order_with_rejected_status(self):
        """测试驳回状态可以重新提交"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO2024002"
        mock_order.status = "REJECTED"
        mock_order.amount_with_tax = 3000.00
        mock_order.supplier_id = 10
        mock_order.project_id = 20
        mock_order.order_title = "重新提交"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        mock_instance = MagicMock()
        mock_instance.id = 200
        self.mock_engine.submit.return_value = mock_instance

        result = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=1
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)

    def test_submit_batch_orders_mixed(self):
        """测试批量提交混合成功和失败"""
        # 第一个订单成功
        mock_order1 = MagicMock()
        mock_order1.id = 1
        mock_order1.order_no = "PO001"
        mock_order1.status = "DRAFT"
        mock_order1.amount_with_tax = 1000.00
        mock_order1.supplier_id = 10
        mock_order1.project_id = 20
        mock_order1.order_title = "订单1"

        # 第二个订单不存在
        # 第三个订单状态错误
        mock_order3 = MagicMock()
        mock_order3.id = 3
        mock_order3.status = "COMPLETED"

        def query_side_effect(*args):
            mock_q = MagicMock()
            
            def filter_side_effect(*filter_args):
                # 通过检查过滤条件来决定返回哪个订单
                mock_f = MagicMock()
                
                # 简化：根据调用次数返回不同结果
                if not hasattr(query_side_effect, 'call_count'):
                    query_side_effect.call_count = 0
                query_side_effect.call_count += 1
                
                if query_side_effect.call_count == 1:
                    mock_f.first.return_value = mock_order1
                elif query_side_effect.call_count == 2:
                    mock_f.first.return_value = None
                else:
                    mock_f.first.return_value = mock_order3
                
                return mock_f
            
            mock_q.filter = filter_side_effect
            return mock_q

        self.mock_db.query.side_effect = query_side_effect

        mock_instance = MagicMock()
        mock_instance.id = 100
        self.mock_engine.submit.return_value = mock_instance

        result = self.service.submit_orders_for_approval(
            order_ids=[1, 2, 3],
            initiator_id=1
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 2)

    def test_submit_order_engine_exception(self):
        """测试审批引擎抛出异常"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "DRAFT"
        mock_order.amount_with_tax = 1000.00
        mock_order.supplier_id = 10
        mock_order.project_id = 20
        mock_order.order_title = "测试"
        mock_order.order_no = "PO001"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        self.mock_engine.submit.side_effect = Exception("审批模板不存在")

        result = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=1
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("审批模板不存在", result["errors"][0]["error"])

    def test_submit_order_with_none_amount(self):
        """测试金额为None的订单"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO001"
        mock_order.status = "DRAFT"
        mock_order.amount_with_tax = None  # 金额为None
        mock_order.supplier_id = 10
        mock_order.project_id = 20
        mock_order.order_title = "测试"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        mock_instance = MagicMock()
        mock_instance.id = 100
        self.mock_engine.submit.return_value = mock_instance

        result = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=1
        )

        # 应该成功，金额转换为0
        self.assertEqual(len(result["success"]), 1)
        call_args = self.mock_engine.submit.call_args[1]
        self.assertEqual(call_args["form_data"]["amount_with_tax"], 0)


class TestGetPendingTasks(unittest.TestCase):
    """测试获取待审批任务"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_engine = MagicMock()
        with patch("app.services.purchase_workflow.service.ApprovalEngineService", return_value=self.mock_engine):
            self.service = PurchaseWorkflowService(self.mock_db)

    def test_get_pending_tasks_success(self):
        """测试获取待审批任务成功"""
        # Mock任务数据
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task1.instance = MagicMock()
        mock_task1.instance.id = 100
        mock_task1.instance.entity_id = 10
        mock_task1.instance.urgency = "HIGH"
        mock_task1.instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_task1.instance.initiator = MagicMock()
        mock_task1.instance.initiator.real_name = "张三"
        mock_task1.node = MagicMock()
        mock_task1.node.node_name = "部门经理审批"

        mock_task2 = MagicMock()
        mock_task2.id = 2
        mock_task2.instance = MagicMock()
        mock_task2.instance.id = 101
        mock_task2.instance.entity_id = 11
        mock_task2.instance.urgency = "NORMAL"
        mock_task2.instance.created_at = datetime(2024, 1, 2, 14, 30, 0)
        mock_task2.instance.initiator = MagicMock()
        mock_task2.instance.initiator.real_name = "李四"
        mock_task2.node = MagicMock()
        mock_task2.node.node_name = "财务审批"

        self.mock_engine.get_pending_tasks.return_value = [mock_task1, mock_task2]

        # Mock采购订单
        mock_order1 = MagicMock()
        mock_order1.order_no = "PO001"
        mock_order1.order_title = "办公用品采购"
        mock_order1.amount_with_tax = 5000.00
        mock_order1.supplier = MagicMock()
        mock_order1.supplier.vendor_name = "供应商A"

        mock_order2 = MagicMock()
        mock_order2.order_no = "PO002"
        mock_order2.order_title = "设备采购"
        mock_order2.amount_with_tax = 15000.00
        mock_order2.supplier = MagicMock()
        mock_order2.supplier.vendor_name = "供应商B"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [mock_order1, mock_order2]

        # 执行
        result = self.service.get_pending_tasks(user_id=999, offset=0, limit=10)

        # 验证
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["items"]), 2)

        item1 = result["items"][0]
        self.assertEqual(item1["task_id"], 1)
        self.assertEqual(item1["order_no"], "PO001")
        self.assertEqual(item1["order_title"], "办公用品采购")
        self.assertEqual(item1["amount_with_tax"], 5000.00)
        self.assertEqual(item1["supplier_name"], "供应商A")
        self.assertEqual(item1["initiator_name"], "张三")
        self.assertEqual(item1["urgency"], "HIGH")
        self.assertEqual(item1["node_name"], "部门经理审批")

    def test_get_pending_tasks_with_pagination(self):
        """测试分页功能"""
        # 创建10个任务
        tasks = []
        for i in range(10):
            mock_task = MagicMock()
            mock_task.id = i + 1
            mock_task.instance = MagicMock()
            mock_task.instance.id = 100 + i
            mock_task.instance.entity_id = 10 + i
            mock_task.instance.urgency = "NORMAL"
            mock_task.instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
            mock_task.instance.initiator = MagicMock()
            mock_task.instance.initiator.real_name = f"用户{i}"
            mock_task.node = MagicMock()
            mock_task.node.node_name = "审批节点"
            tasks.append(mock_task)

        self.mock_engine.get_pending_tasks.return_value = tasks

        # Mock订单查询
        def create_mock_order(idx):
            order = MagicMock()
            order.order_no = f"PO{idx:03d}"
            order.order_title = f"订单{idx}"
            order.amount_with_tax = 1000.00 * idx
            order.supplier = MagicMock()
            order.supplier.vendor_name = f"供应商{idx}"
            return order

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [create_mock_order(i) for i in range(10)]

        # 测试第一页（5条）
        result = self.service.get_pending_tasks(user_id=1, offset=0, limit=5)
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(result["items"]), 5)

        # 重置mock
        mock_filter.first.side_effect = [create_mock_order(i) for i in range(5, 10)]
        
        # 测试第二页（5条）
        result = self.service.get_pending_tasks(user_id=1, offset=5, limit=5)
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(result["items"]), 5)

    def test_get_pending_tasks_empty(self):
        """测试无待审批任务"""
        self.mock_engine.get_pending_tasks.return_value = []

        result = self.service.get_pending_tasks(user_id=1)

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_pending_tasks_order_not_found(self):
        """测试订单已删除的情况"""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.instance = MagicMock()
        mock_task.instance.id = 100
        mock_task.instance.entity_id = 999  # 订单不存在
        mock_task.instance.urgency = "NORMAL"
        mock_task.instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_task.instance.initiator = MagicMock()
        mock_task.instance.initiator.real_name = "张三"
        mock_task.node = MagicMock()
        mock_task.node.node_name = "审批节点"

        self.mock_engine.get_pending_tasks.return_value = [mock_task]

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None  # 订单不存在

        result = self.service.get_pending_tasks(user_id=1)

        # 应该返回任务，但订单相关字段为None
        self.assertEqual(len(result["items"]), 1)
        self.assertIsNone(result["items"][0]["order_no"])
        self.assertIsNone(result["items"][0]["supplier_name"])

    def test_get_pending_tasks_with_none_supplier(self):
        """测试订单没有供应商的情况"""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.instance = MagicMock()
        mock_task.instance.id = 100
        mock_task.instance.entity_id = 10
        mock_task.instance.urgency = "NORMAL"
        mock_task.instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_task.instance.initiator = MagicMock()
        mock_task.instance.initiator.real_name = "张三"
        mock_task.node = MagicMock()
        mock_task.node.node_name = "审批"

        self.mock_engine.get_pending_tasks.return_value = [mock_task]

        mock_order = MagicMock()
        mock_order.order_no = "PO001"
        mock_order.order_title = "测试"
        mock_order.amount_with_tax = 1000.00
        mock_order.supplier = None  # 没有供应商

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        result = self.service.get_pending_tasks(user_id=1)

        self.assertEqual(len(result["items"]), 1)
        self.assertIsNone(result["items"][0]["supplier_name"])


class TestPerformApprovalAction(unittest.TestCase):
    """测试执行审批操作"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_engine = MagicMock()
        with patch("app.services.purchase_workflow.service.ApprovalEngineService", return_value=self.mock_engine):
            self.service = PurchaseWorkflowService(self.mock_db)

    def test_approve_action(self):
        """测试批准操作"""
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        self.mock_engine.approve.return_value = mock_result

        result = self.service.perform_approval_action(
            task_id=1,
            action="approve",
            approver_id=10,
            comment="同意"
        )

        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.mock_engine.approve.assert_called_once_with(
            task_id=1,
            approver_id=10,
            comment="同意"
        )

    def test_reject_action(self):
        """测试驳回操作"""
        mock_result = MagicMock()
        mock_result.status = "REJECTED"
        self.mock_engine.reject.return_value = mock_result

        result = self.service.perform_approval_action(
            task_id=2,
            action="reject",
            approver_id=20,
            comment="不符合要求"
        )

        self.assertEqual(result["task_id"], 2)
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.mock_engine.reject.assert_called_once_with(
            task_id=2,
            approver_id=20,
            comment="不符合要求"
        )

    def test_unsupported_action(self):
        """测试不支持的操作"""
        with self.assertRaises(HTTPException) as context:
            self.service.perform_approval_action(
                task_id=1,
                action="invalid_action",
                approver_id=1
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("不支持的操作类型", context.exception.detail)

    def test_approve_without_comment(self):
        """测试批准操作无备注"""
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        self.mock_engine.approve.return_value = mock_result

        result = self.service.perform_approval_action(
            task_id=1,
            action="approve",
            approver_id=10
        )

        self.assertEqual(result["action"], "approve")
        self.mock_engine.approve.assert_called_once_with(
            task_id=1,
            approver_id=10,
            comment=None
        )


class TestPerformBatchApproval(unittest.TestCase):
    """测试批量审批"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_engine = MagicMock()
        with patch("app.services.purchase_workflow.service.ApprovalEngineService", return_value=self.mock_engine):
            self.service = PurchaseWorkflowService(self.mock_db)

    def test_batch_approve_all_success(self):
        """测试批量批准全部成功"""
        self.mock_engine.approve.return_value = MagicMock()

        result = self.service.perform_batch_approval(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=10,
            comment="批量通过"
        )

        self.assertEqual(len(result["success"]), 3)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.mock_engine.approve.call_count, 3)

    def test_batch_reject_all_success(self):
        """测试批量驳回全部成功"""
        self.mock_engine.reject.return_value = MagicMock()

        result = self.service.perform_batch_approval(
            task_ids=[1, 2],
            action="reject",
            approver_id=10,
            comment="不符合要求"
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.mock_engine.reject.call_count, 2)

    def test_batch_approval_partial_failure(self):
        """测试批量审批部分失败"""
        # 第一个成功，第二个失败，第三个成功
        call_count = [0]
        
        def approve_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("权限不足")
            return MagicMock()

        self.mock_engine.approve.side_effect = approve_side_effect

        result = self.service.perform_batch_approval(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=10
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["task_id"], 2)
        self.assertIn("权限不足", result["errors"][0]["error"])

    def test_batch_approval_unsupported_action(self):
        """测试批量操作不支持的动作"""
        result = self.service.perform_batch_approval(
            task_ids=[1, 2],
            action="cancel",  # 不支持的操作
            approver_id=10
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 2)
        self.assertIn("不支持的操作", result["errors"][0]["error"])


class TestGetApprovalStatus(unittest.TestCase):
    """测试查询审批状态"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_engine = MagicMock()
        with patch("app.services.purchase_workflow.service.ApprovalEngineService", return_value=self.mock_engine):
            self.service = PurchaseWorkflowService(self.mock_db)

    @patch("app.services.purchase_workflow.service.get_or_404")
    def test_get_approval_status_with_instance(self, mock_get_or_404):
        """测试获取有审批实例的状态"""
        # Mock订单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO001"
        mock_order.status = "PENDING_APPROVAL"
        mock_get_or_404.return_value = mock_order

        # Mock审批实例
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.urgency = "HIGH"
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_instance.completed_at = None

        # Mock查询链
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.first.side_effect = [mock_instance]  # 第一次调用返回instance

        # Mock任务历史
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task1.status = "APPROVED"
        mock_task1.action = "approve"
        mock_task1.comment = "同意"
        mock_task1.completed_at = datetime(2024, 1, 1, 11, 0, 0)
        mock_task1.node = MagicMock()
        mock_task1.node.node_name = "部门经理"
        mock_task1.assignee = MagicMock()
        mock_task1.assignee.real_name = "张三"

        # 第二次query是查询任务
        mock_task_query = MagicMock()
        mock_task_filter = mock_task_query.filter.return_value
        mock_task_order = mock_task_filter.order_by.return_value
        mock_task_order.all.return_value = [mock_task1]
        
        # 设置query的side_effect
        self.mock_db.query.side_effect = [mock_query, mock_task_query]

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "PO001")
        self.assertEqual(result["order_status"], "PENDING_APPROVAL")
        self.assertEqual(result["instance_id"], 100)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(result["urgency"], "HIGH")
        self.assertEqual(len(result["task_history"]), 1)
        self.assertEqual(result["task_history"][0]["node_name"], "部门经理")
        self.assertEqual(result["task_history"][0]["assignee_name"], "张三")

    @patch("app.services.purchase_workflow.service.get_or_404")
    def test_get_approval_status_no_instance(self, mock_get_or_404):
        """测试获取无审批实例的状态"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO001"
        mock_order.status = "DRAFT"
        mock_get_or_404.return_value = mock_order

        # 无审批实例
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.first.return_value = None

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "PO001")
        self.assertEqual(result["status"], "DRAFT")
        self.assertIsNone(result["approval_instance"])

    @patch("app.services.purchase_workflow.service.get_or_404")
    def test_get_approval_status_order_not_found(self, mock_get_or_404):
        """测试订单不存在"""
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="采购订单不存在")

        with self.assertRaises(HTTPException) as context:
            self.service.get_approval_status(order_id=999)

        self.assertEqual(context.exception.status_code, 404)


class TestWithdrawApproval(unittest.TestCase):
    """测试撤回审批"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_engine = MagicMock()
        with patch("app.services.purchase_workflow.service.ApprovalEngineService", return_value=self.mock_engine):
            self.service = PurchaseWorkflowService(self.mock_db)

    @patch("app.services.purchase_workflow.service.get_or_404")
    def test_withdraw_approval_success(self, mock_get_or_404):
        """测试撤回审批成功"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO001"
        mock_get_or_404.return_value = mock_order

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.initiator_id = 10  # 提交人ID

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_instance

        result = self.service.withdraw_approval(
            order_id=1,
            user_id=10,  # 相同的用户ID
            reason="信息有误"
        )

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "PO001")
        self.assertEqual(result["status"], "withdrawn")
        self.mock_engine.withdraw.assert_called_once_with(
            instance_id=100,
            user_id=10
        )

    @patch("app.services.purchase_workflow.service.get_or_404")
    def test_withdraw_approval_no_pending_instance(self, mock_get_or_404):
        """测试没有进行中的审批"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_get_or_404.return_value = mock_order

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None  # 无进行中的审批

        with self.assertRaises(HTTPException) as context:
            self.service.withdraw_approval(order_id=1, user_id=10)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("没有进行中的审批", context.exception.detail)

    @patch("app.services.purchase_workflow.service.get_or_404")
    def test_withdraw_approval_not_initiator(self, mock_get_or_404):
        """测试非提交人撤回"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_get_or_404.return_value = mock_order

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.initiator_id = 10  # 提交人ID为10

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_instance

        with self.assertRaises(HTTPException) as context:
            self.service.withdraw_approval(
                order_id=1,
                user_id=20  # 不同的用户ID
            )

        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("只能撤回自己提交的审批", context.exception.detail)


class TestGetApprovalHistory(unittest.TestCase):
    """测试获取审批历史"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_engine = MagicMock()
        with patch("app.services.purchase_workflow.service.ApprovalEngineService", return_value=self.mock_engine):
            self.service = PurchaseWorkflowService(self.mock_db)

    def test_get_approval_history_success(self):
        """测试获取审批历史成功"""
        # Mock任务
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task1.status = "APPROVED"
        mock_task1.action = "approve"
        mock_task1.comment = "同意"
        mock_task1.completed_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_task1.instance = MagicMock()
        mock_task1.instance.entity_id = 10

        mock_task2 = MagicMock()
        mock_task2.id = 2
        mock_task2.status = "REJECTED"
        mock_task2.action = "reject"
        mock_task2.comment = "不符合要求"
        mock_task2.completed_at = datetime(2024, 1, 2, 14, 0, 0)
        mock_task2.instance = MagicMock()
        mock_task2.instance.entity_id = 11

        # Mock查询链
        mock_join = self.mock_db.query.return_value.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_filter.count.return_value = 2
        
        mock_order_by = mock_filter.order_by.return_value
        mock_offset = mock_order_by.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.all.return_value = [mock_task1, mock_task2]

        # Mock订单
        mock_order1 = MagicMock()
        mock_order1.order_no = "PO001"
        mock_order1.order_title = "采购1"
        mock_order1.amount_with_tax = 5000.00

        mock_order2 = MagicMock()
        mock_order2.order_no = "PO002"
        mock_order2.order_title = "采购2"
        mock_order2.amount_with_tax = 3000.00

        # 设置订单查询的side_effect
        order_query = MagicMock()
        order_filter = order_query.filter.return_value
        order_filter.first.side_effect = [mock_order1, mock_order2]
        
        # 注意：第一次query是任务查询，后续的是订单查询
        self.mock_db.query.side_effect = [
            self.mock_db.query.return_value,  # 任务查询
            order_query,  # 第一个订单
            order_query,  # 第二个订单
        ]

        result = self.service.get_approval_history(user_id=1, offset=0, limit=10)

        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["order_no"], "PO001")
        self.assertEqual(result["items"][0]["status"], "APPROVED")

    def test_get_approval_history_with_filter(self):
        """测试带状态筛选的审批历史"""
        mock_join = self.mock_db.query.return_value.join.return_value
        mock_filter1 = mock_join.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value  # 第二次filter（状态筛选）
        mock_filter2.count.return_value = 0
        
        mock_order_by = mock_filter2.order_by.return_value
        mock_offset = mock_order_by.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.all.return_value = []

        result = self.service.get_approval_history(
            user_id=1,
            status_filter="APPROVED"
        )

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_approval_history_pagination(self):
        """测试审批历史分页"""
        # 创建5个任务
        tasks = []
        for i in range(5):
            task = MagicMock()
            task.id = i + 1
            task.status = "APPROVED"
            task.action = "approve"
            task.comment = f"同意{i}"
            task.completed_at = datetime(2024, 1, i + 1, 10, 0, 0)
            task.instance = MagicMock()
            task.instance.entity_id = 10 + i
            tasks.append(task)

        mock_join = self.mock_db.query.return_value.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_filter.count.return_value = 5
        
        mock_order_by = mock_filter.order_by.return_value
        mock_offset = mock_order_by.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.all.return_value = tasks[:3]  # 返回前3个

        # Mock订单
        def create_order(idx):
            order = MagicMock()
            order.order_no = f"PO{idx:03d}"
            order.order_title = f"订单{idx}"
            order.amount_with_tax = 1000.00 * idx
            return order

        order_query = MagicMock()
        order_filter = order_query.filter.return_value
        order_filter.first.side_effect = [create_order(i) for i in range(3)]
        
        self.mock_db.query.side_effect = [
            self.mock_db.query.return_value,
            order_query, order_query, order_query
        ]

        result = self.service.get_approval_history(
            user_id=1,
            offset=0,
            limit=3
        )

        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["items"]), 3)

    def test_get_approval_history_empty(self):
        """测试无审批历史"""
        mock_join = self.mock_db.query.return_value.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_filter.count.return_value = 0
        
        mock_order_by = mock_filter.order_by.return_value
        mock_offset = mock_order_by.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.all.return_value = []

        result = self.service.get_approval_history(user_id=999)

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)


if __name__ == "__main__":
    unittest.main()

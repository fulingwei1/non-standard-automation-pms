# -*- coding: utf-8 -*-
"""
外协工作流服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不mock业务方法）
3. 覆盖主要方法和边界情况
4. 所有测试必须通过

目标：覆盖率 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime

from app.services.outsourcing_workflow.outsourcing_workflow_service import (
    OutsourcingWorkflowService,
)


class TestOutsourcingWorkflowService(unittest.TestCase):
    """测试外协工作流服务"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = OutsourcingWorkflowService(self.db)
        # Mock ApprovalEngineService
        self.service.engine = MagicMock()

    # ========== submit_orders_for_approval 测试 ==========

    def test_submit_orders_for_approval_success(self):
        """测试成功提交订单审批"""
        # Mock数据
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "OUT-2024-001"
        mock_order.order_title = "测试订单"
        mock_order.order_type = "SERVICE"
        mock_order.amount_with_tax = 5000.00
        mock_order.vendor_id = 10
        mock_order.project_id = 20
        mock_order.machine_id = 30
        mock_order.status = "DRAFT"

        # Mock instance
        mock_instance = MagicMock()
        mock_instance.id = 100

        # Mock db.query
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = mock_order

        # Mock engine.submit
        self.service.engine.submit.return_value = mock_instance

        # 执行测试
        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=5, urgency="HIGH", comment="紧急订单"
        )

        # 验证
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["order_id"], 1)
        self.assertEqual(result["success"][0]["order_no"], "OUT-2024-001")
        self.assertEqual(result["success"][0]["instance_id"], 100)
        self.assertEqual(result["success"][0]["status"], "submitted")

        # 验证engine.submit被正确调用
        self.service.engine.submit.assert_called_once()

    def test_submit_orders_order_not_found(self):
        """测试订单不存在的情况"""
        # Mock db.query返回None
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = None

        result = self.service.submit_orders_for_approval(
            order_ids=[999], initiator_id=5
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["order_id"], 999)
        self.assertEqual(result["errors"][0]["error"], "外协订单不存在")

    def test_submit_orders_invalid_status(self):
        """测试订单状态不允许提交"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "APPROVED"  # 已审批状态不允许再提交

        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = mock_order

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=5
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_submit_orders_engine_exception(self):
        """测试引擎提交异常"""
        mock_order = MagicMock()
        mock_order.status = "DRAFT"
        mock_order.amount_with_tax = 1000

        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = mock_order

        # Mock engine抛出异常
        self.service.engine.submit.side_effect = Exception("引擎错误")

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=5
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["error"], "引擎错误")

    def test_submit_orders_multiple_orders(self):
        """测试批量提交多个订单"""
        # Mock第一个订单成功
        mock_order1 = MagicMock()
        mock_order1.id = 1
        mock_order1.order_no = "OUT-001"
        mock_order1.status = "DRAFT"
        mock_order1.amount_with_tax = 1000

        # Mock第二个订单不存在
        # Mock第三个订单成功
        mock_order3 = MagicMock()
        mock_order3.id = 3
        mock_order3.order_no = "OUT-003"
        mock_order3.status = "REJECTED"
        mock_order3.amount_with_tax = 3000

        # 设置db.query的返回值序列
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_order1, None, mock_order3]

        mock_instance1 = MagicMock()
        mock_instance1.id = 101
        mock_instance3 = MagicMock()
        mock_instance3.id = 103

        self.service.engine.submit.side_effect = [mock_instance1, mock_instance3]

        result = self.service.submit_orders_for_approval(
            order_ids=[1, 2, 3], initiator_id=5
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["order_id"], 2)

    # ========== get_pending_tasks 测试 ==========

    def test_get_pending_tasks_success(self):
        """测试获取待审批任务列表"""
        # Mock任务
        mock_task = MagicMock()
        mock_task.id = 1

        # Mock instance
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.entity_id = 10
        mock_instance.urgency = "NORMAL"
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_task.instance = mock_instance

        # Mock initiator
        mock_initiator = MagicMock()
        mock_initiator.real_name = "张三"
        mock_instance.initiator = mock_initiator

        # Mock node
        mock_node = MagicMock()
        mock_node.node_name = "部门审批"
        mock_task.node = mock_node

        # Mock order
        mock_order = MagicMock()
        mock_order.order_no = "OUT-001"
        mock_order.order_title = "测试订单"
        mock_order.order_type = "SERVICE"
        mock_order.amount_with_tax = 5000.00

        # Mock vendor
        mock_vendor = MagicMock()
        mock_vendor.vendor_name = "供应商A"
        mock_order.vendor = mock_vendor

        # Mock project
        mock_project = MagicMock()
        mock_project.project_name = "项目A"
        mock_order.project = mock_project

        # Mock engine返回任务列表
        self.service.engine.get_pending_tasks.return_value = [mock_task]

        # Mock db.query
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = mock_order

        result = self.service.get_pending_tasks(user_id=5, offset=0, limit=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["task_id"], 1)
        self.assertEqual(item["order_no"], "OUT-001")
        self.assertEqual(item["vendor_name"], "供应商A")
        self.assertEqual(item["initiator_name"], "张三")

    def test_get_pending_tasks_pagination(self):
        """测试分页"""
        # 创建3个任务
        mock_tasks = []
        for i in range(3):
            task = MagicMock()
            task.id = i + 1
            instance = MagicMock()
            instance.entity_id = i + 1
            instance.created_at = datetime(2024, 1, 1)
            task.instance = instance
            task.node = MagicMock()
            instance.initiator = MagicMock()
            mock_tasks.append(task)

        self.service.engine.get_pending_tasks.return_value = mock_tasks

        # Mock orders
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [
            MagicMock(order_no=f"OUT-{i+1}", amount_with_tax=1000)
            for i in range(3)
        ]

        # 测试第一页
        result = self.service.get_pending_tasks(user_id=5, offset=0, limit=2)
        self.assertEqual(result["total"], 3)
        self.assertEqual(len(result["items"]), 2)

        # 重置filter的side_effect
        filter_mock.first.side_effect = [
            MagicMock(order_no=f"OUT-{i+1}", amount_with_tax=1000)
            for i in range(3)
        ]

        # 测试第二页
        result = self.service.get_pending_tasks(user_id=5, offset=2, limit=2)
        self.assertEqual(result["total"], 3)
        self.assertEqual(len(result["items"]), 1)

    def test_get_pending_tasks_no_order(self):
        """测试订单不存在的情况"""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_instance = MagicMock()
        mock_instance.entity_id = 999
        mock_instance.created_at = datetime(2024, 1, 1)
        mock_task.instance = mock_instance
        mock_task.node = MagicMock()
        mock_instance.initiator = MagicMock()

        self.service.engine.get_pending_tasks.return_value = [mock_task]

        # Mock db.query返回None
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = None

        result = self.service.get_pending_tasks(user_id=5)

        self.assertEqual(len(result["items"]), 1)
        # 订单不存在时，order_no应为None
        self.assertIsNone(result["items"][0]["order_no"])

    # ========== perform_approval_action 测试 ==========

    def test_perform_approval_action_approve(self):
        """测试审批通过"""
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        mock_result.entity_id = 10

        self.service.engine.approve.return_value = mock_result

        # Mock _trigger_cost_collection
        with patch.object(
            self.service, "_trigger_cost_collection"
        ) as mock_trigger:
            result = self.service.perform_approval_action(
                task_id=1, approver_id=5, action="approve", comment="同意"
            )

            self.assertEqual(result["task_id"], 1)
            self.assertEqual(result["action"], "approve")
            self.assertEqual(result["instance_status"], "APPROVED")
            mock_trigger.assert_called_once_with(10, 5)

    def test_perform_approval_action_approve_not_final(self):
        """测试审批通过但未到最终状态"""
        mock_result = MagicMock()
        mock_result.status = "PENDING"  # 还在审批中
        mock_result.entity_id = 10

        self.service.engine.approve.return_value = mock_result

        with patch.object(
            self.service, "_trigger_cost_collection"
        ) as mock_trigger:
            result = self.service.perform_approval_action(
                task_id=1, approver_id=5, action="approve"
            )

            self.assertEqual(result["instance_status"], "PENDING")
            # 未到最终审批状态，不应触发成本归集
            mock_trigger.assert_not_called()

    def test_perform_approval_action_reject(self):
        """测试审批拒绝"""
        mock_result = MagicMock()
        mock_result.status = "REJECTED"

        self.service.engine.reject.return_value = mock_result

        result = self.service.perform_approval_action(
            task_id=1, approver_id=5, action="reject", comment="不同意"
        )

        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.service.engine.reject.assert_called_once_with(
            task_id=1, approver_id=5, comment="不同意"
        )

    def test_perform_approval_action_invalid_action(self):
        """测试不支持的操作类型"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_approval_action(
                task_id=1, approver_id=5, action="invalid"
            )

        self.assertIn("不支持的操作类型", str(context.exception))

    # ========== perform_batch_approval 测试 ==========

    def test_perform_batch_approval_approve_success(self):
        """测试批量审批通过"""
        mock_result1 = MagicMock()
        mock_result1.status = "APPROVED"
        mock_result1.entity_id = 10

        mock_result2 = MagicMock()
        mock_result2.status = "APPROVED"
        mock_result2.entity_id = 11

        self.service.engine.approve.side_effect = [mock_result1, mock_result2]

        with patch.object(
            self.service, "_trigger_cost_collection"
        ) as mock_trigger:
            result = self.service.perform_batch_approval(
                task_ids=[1, 2], approver_id=5, action="approve"
            )

            self.assertEqual(len(result["success"]), 2)
            self.assertEqual(len(result["errors"]), 0)
            self.assertEqual(mock_trigger.call_count, 2)

    def test_perform_batch_approval_mixed_results(self):
        """测试批量审批混合结果"""
        mock_result1 = MagicMock()
        mock_result1.status = "APPROVED"
        mock_result1.entity_id = 10

        # 第二个任务抛出异常
        self.service.engine.approve.side_effect = [
            mock_result1,
            Exception("审批失败"),
        ]

        with patch.object(self.service, "_trigger_cost_collection"):
            result = self.service.perform_batch_approval(
                task_ids=[1, 2], approver_id=5, action="approve"
            )

            self.assertEqual(len(result["success"]), 1)
            self.assertEqual(len(result["errors"]), 1)
            self.assertEqual(result["errors"][0]["task_id"], 2)
            self.assertEqual(result["errors"][0]["error"], "审批失败")

    def test_perform_batch_approval_invalid_action(self):
        """测试批量审批不支持的操作"""
        result = self.service.perform_batch_approval(
            task_ids=[1], approver_id=5, action="invalid"
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不支持的操作", result["errors"][0]["error"])

    def test_perform_batch_approval_reject(self):
        """测试批量拒绝"""
        self.service.engine.reject.return_value = MagicMock(status="REJECTED")

        result = self.service.perform_batch_approval(
            task_ids=[1, 2], approver_id=5, action="reject", comment="批量拒绝"
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(self.service.engine.reject.call_count, 2)

    # ========== get_approval_status 测试 ==========

    def test_get_approval_status_success(self):
        """测试获取审批状态"""
        # Mock order
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "OUT-001"
        mock_order.status = "PENDING_APPROVAL"

        # Mock instance
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.urgency = "NORMAL"
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_instance.completed_at = None

        # Mock tasks
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "APPROVED"
        mock_task.action = "approve"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 1, 11, 0, 0)

        mock_node = MagicMock()
        mock_node.node_name = "部门审批"
        mock_task.node = mock_node

        mock_assignee = MagicMock()
        mock_assignee.real_name = "李四"
        mock_task.assignee = mock_assignee

        # Mock db.query
        order_query = self.db.query.return_value
        order_filter = order_query.filter.return_value
        order_filter.first.return_value = mock_order

        instance_filter = order_query.filter.return_value
        instance_order_by = instance_filter.order_by.return_value
        instance_order_by.first.return_value = mock_instance

        task_filter = order_query.filter.return_value
        task_order_by = task_filter.order_by.return_value
        task_order_by.all.return_value = [mock_task]

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "OUT-001")
        self.assertEqual(result["instance_id"], 100)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)
        self.assertEqual(result["task_history"][0]["node_name"], "部门审批")

    def test_get_approval_status_order_not_found(self):
        """测试订单不存在"""
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_approval_status(order_id=999)

        self.assertEqual(str(context.exception), "外协订单不存在")

    def test_get_approval_status_no_instance(self):
        """测试没有审批实例"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "OUT-001"
        mock_order.status = "DRAFT"

        # 第一次query返回order
        order_query_mock = MagicMock()
        order_filter_mock = order_query_mock.filter.return_value
        order_filter_mock.first.return_value = mock_order

        # 第二次query返回instance (None)
        instance_query_mock = MagicMock()
        instance_filter_mock = instance_query_mock.filter.return_value
        instance_order_by_mock = instance_filter_mock.order_by.return_value
        instance_order_by_mock.first.return_value = None

        # 设置db.query的side_effect
        self.db.query.side_effect = [order_query_mock, instance_query_mock]

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertIsNone(result["approval_instance"])

    # ========== withdraw_approval 测试 ==========

    def test_withdraw_approval_success(self):
        """测试撤回审批"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "OUT-001"

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.initiator_id = 5
        mock_instance.status = "PENDING"

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value

        # 第一次调用返回order，第二次调用返回instance
        filter_mock.first.side_effect = [mock_order, mock_instance]

        result = self.service.withdraw_approval(order_id=1, user_id=5, reason="撤回")

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.service.engine.withdraw.assert_called_once_with(
            instance_id=100, user_id=5
        )

    def test_withdraw_approval_order_not_found(self):
        """测试订单不存在"""
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=999, user_id=5)

        self.assertEqual(str(context.exception), "外协订单不存在")

    def test_withdraw_approval_no_pending_instance(self):
        """测试没有进行中的审批流程"""
        mock_order = MagicMock()
        mock_order.id = 1

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value

        # 第一次返回order，第二次返回None（没有pending的instance）
        filter_mock.first.side_effect = [mock_order, None]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=5)

        self.assertEqual(str(context.exception), "没有进行中的审批流程可撤回")

    def test_withdraw_approval_not_initiator(self):
        """测试非发起人撤回"""
        mock_order = MagicMock()
        mock_order.id = 1

        mock_instance = MagicMock()
        mock_instance.initiator_id = 5  # 发起人是5
        mock_instance.status = "PENDING"

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_order, mock_instance]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=10)  # 用户10尝试撤回

        self.assertEqual(str(context.exception), "只能撤回自己提交的审批")

    # ========== get_approval_history 测试 ==========

    def test_get_approval_history_success(self):
        """测试获取审批历史"""
        # Mock task
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.action = "approve"
        mock_task.status = "APPROVED"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 1, 10, 0, 0)

        # Mock instance
        mock_instance = MagicMock()
        mock_instance.entity_id = 10
        mock_task.instance = mock_instance

        # Mock order
        mock_order = MagicMock()
        mock_order.order_no = "OUT-001"
        mock_order.order_title = "测试订单"
        mock_order.order_type = "SERVICE"
        mock_order.amount_with_tax = 5000.00

        # Mock query chain
        query_mock = self.db.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.count.return_value = 1

        order_by_mock = filter_mock.order_by.return_value
        offset_mock = order_by_mock.offset.return_value
        limit_mock = offset_mock.limit.return_value
        limit_mock.all.return_value = [mock_task]

        # Mock order query
        order_query = self.db.query.return_value
        order_filter = order_query.filter.return_value
        order_filter.first.return_value = mock_order

        result = self.service.get_approval_history(user_id=5, offset=0, limit=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["task_id"], 1)
        self.assertEqual(item["order_no"], "OUT-001")
        self.assertEqual(item["action"], "approve")

    def test_get_approval_history_with_status_filter(self):
        """测试带状态筛选的审批历史"""
        query_mock = self.db.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock1 = join_mock.filter.return_value
        
        # 设置第二次filter的返回值（status筛选后）
        filter_mock2 = filter_mock1.filter.return_value
        filter_mock2.count.return_value = 0

        order_by_mock = filter_mock2.order_by.return_value
        offset_mock = order_by_mock.offset.return_value
        limit_mock = offset_mock.limit.return_value
        limit_mock.all.return_value = []

        result = self.service.get_approval_history(
            user_id=5, status_filter="REJECTED"
        )

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_approval_history_pagination(self):
        """测试审批历史分页"""
        # 创建多个任务
        mock_tasks = []
        for i in range(3):
            task = MagicMock()
            task.id = i + 1
            task.completed_at = datetime(2024, 1, i + 1)
            instance = MagicMock()
            instance.entity_id = i + 1
            task.instance = instance
            mock_tasks.append(task)

        query_mock = self.db.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.count.return_value = 3

        order_by_mock = filter_mock.order_by.return_value
        offset_mock = order_by_mock.offset.return_value
        limit_mock = offset_mock.limit.return_value
        limit_mock.all.return_value = mock_tasks[:2]  # 第一页返回2条

        # Mock orders
        order_query = self.db.query.return_value
        order_filter = order_query.filter.return_value
        order_filter.first.side_effect = [
            MagicMock(order_no=f"OUT-{i+1}", amount_with_tax=1000)
            for i in range(2)
        ]

        result = self.service.get_approval_history(user_id=5, offset=0, limit=2)

        self.assertEqual(result["total"], 3)
        self.assertEqual(len(result["items"]), 2)

    # ========== _trigger_cost_collection 测试 ==========

    def test_trigger_cost_collection_success(self):
        """测试成功触发成本归集"""
        # Mock动态导入的CostCollectionService
        with patch(
            "app.services.cost_collection_service.CostCollectionService"
        ) as mock_service:
            self.service._trigger_cost_collection(order_id=10, user_id=5)
            mock_service.collect_from_outsourcing_order.assert_called_once_with(
                self.db, 10, created_by=5
            )

    def test_trigger_cost_collection_exception(self):
        """测试成本归集异常（应该被捕获并记录日志）"""
        with patch(
            "app.services.cost_collection_service.CostCollectionService"
        ) as mock_service:
            mock_service.collect_from_outsourcing_order.side_effect = Exception(
                "成本归集失败"
            )

            # 不应该抛出异常
            try:
                self.service._trigger_cost_collection(order_id=10, user_id=5)
            except Exception:
                self.fail("_trigger_cost_collection不应该抛出异常")

    def test_trigger_cost_collection_import_error(self):
        """测试成本归集服务导入失败"""
        # Mock导入失败：将模块导入替换为抛出ImportError
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "app.services.cost_collection_service":
                raise ImportError("模块不存在")
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=mock_import):
            # 不应该抛出异常
            try:
                self.service._trigger_cost_collection(order_id=10, user_id=5)
            except Exception:
                self.fail("_trigger_cost_collection不应该抛出异常")


if __name__ == "__main__":
    unittest.main()

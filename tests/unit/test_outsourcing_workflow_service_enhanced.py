# -*- coding: utf-8 -*-
"""
外协工作流服务增强单元测试

测试覆盖：
- 提交审批（单个、批量、多种状态）
- 待审批任务查询（分页、关联数据）
- 审批操作（通过、驳回、批量）
- 审批状态查询（完整历史）
- 审批撤回（权限验证）
- 审批历史查询（分页、过滤）
- 成本归集触发
- 边界条件和异常处理
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.outsourcing_workflow.outsourcing_workflow_service import (
    OutsourcingWorkflowService,
)


class TestOutsourcingWorkflowService(unittest.TestCase):
    """外协工作流服务测试基类"""

    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.service = OutsourcingWorkflowService(self.db)

    def tearDown(self):
        """测试后置清理"""
        self.db.reset_mock()

    def _create_mock_order(
        self, order_id=1, status="DRAFT", order_no="WX202401001", amount=10000.00
    ):
        """创建模拟订单对象"""
        order = Mock()
        order.id = order_id
        order.order_no = order_no
        order.order_title = f"测试订单-{order_no}"
        order.order_type = "PROCESSING"
        order.status = status
        order.amount_with_tax = Decimal(str(amount))
        order.vendor_id = 100
        order.project_id = 200
        order.machine_id = 300
        # 添加关联对象
        order.vendor = Mock()
        order.vendor.vendor_name = "测试外协商"
        order.project = Mock()
        order.project.project_name = "测试项目"
        return order

    def _create_mock_instance(
        self, instance_id=1, entity_id=1, status="PENDING", initiator_id=1
    ):
        """创建模拟审批实例对象"""
        instance = Mock()
        instance.id = instance_id
        instance.entity_type = "OUTSOURCING_ORDER"
        instance.entity_id = entity_id
        instance.status = status
        instance.urgency = "NORMAL"
        instance.initiator_id = initiator_id
        instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        instance.completed_at = None
        instance.initiator = Mock()
        instance.initiator.real_name = "张三"
        return instance

    def _create_mock_task(self, task_id=1, instance=None, status="PENDING"):
        """创建模拟审批任务对象"""
        task = Mock()
        task.id = task_id
        task.instance_id = instance.id if instance else 1
        task.instance = instance
        task.status = status
        task.action = None
        task.comment = None
        task.created_at = datetime(2024, 1, 1, 10, 0, 0)
        task.completed_at = None
        task.assignee_id = 10
        task.node = Mock()
        task.node.node_name = "部门经理审批"
        task.assignee = Mock()
        task.assignee.real_name = "李四"
        return task


class TestInitialization(TestOutsourcingWorkflowService):
    """测试初始化"""

    def test_init_success(self):
        """测试正常初始化"""
        self.assertIs(self.service.db, self.db)

    def test_init_creates_approval_engine(self):
        """测试初始化创建审批引擎"""
        self.assertIsNotNone(self.service.engine)


class TestSubmitOrdersForApproval(TestOutsourcingWorkflowService):
    """测试提交订单审批"""

    def test_submit_single_order_success(self):
        """测试提交单个订单成功"""
        order = self._create_mock_order(order_id=1, status="DRAFT")
        instance = self._create_mock_instance(instance_id=10, entity_id=1)

        # Mock数据库查询
        self.db.query.return_value.filter.return_value.first.return_value = order

        # Mock审批引擎提交
        self.service.engine.submit = Mock(return_value=instance)

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=100, urgency="HIGH", comment="紧急审批"
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["order_id"], 1)
        self.assertEqual(result["success"][0]["instance_id"], 10)
        self.service.engine.submit.assert_called_once()

    def test_submit_order_with_rejected_status(self):
        """测试提交被驳回的订单"""
        order = self._create_mock_order(order_id=1, status="REJECTED")
        instance = self._create_mock_instance()

        self.db.query.return_value.filter.return_value.first.return_value = order
        self.service.engine.submit = Mock(return_value=instance)

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=100
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)

    def test_submit_order_not_found(self):
        """测试提交不存在的订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.submit_orders_for_approval(
            order_ids=[999], initiator_id=100
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["order_id"], 999)
        self.assertIn("不存在", result["errors"][0]["error"])

    def test_submit_order_invalid_status(self):
        """测试提交状态不允许的订单"""
        order = self._create_mock_order(order_id=1, status="APPROVED")
        self.db.query.return_value.filter.return_value.first.return_value = order

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=100
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_submit_multiple_orders_mixed_results(self):
        """测试批量提交订单（混合成功和失败）"""
        order1 = self._create_mock_order(order_id=1, status="DRAFT")
        order2 = self._create_mock_order(order_id=2, status="APPROVED")
        instance1 = self._create_mock_instance(instance_id=10, entity_id=1)

        # 配置查询链返回不同订单
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order1,
            order2,
        ]
        self.service.engine.submit = Mock(return_value=instance1)

        result = self.service.submit_orders_for_approval(
            order_ids=[1, 2], initiator_id=100
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["success"][0]["order_id"], 1)
        self.assertEqual(result["errors"][0]["order_id"], 2)

    def test_submit_order_engine_exception(self):
        """测试提交时审批引擎异常"""
        order = self._create_mock_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.service.engine.submit = Mock(side_effect=Exception("引擎错误"))

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=100
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("引擎错误", result["errors"][0]["error"])

    def test_submit_order_with_zero_amount(self):
        """测试提交金额为0的订单"""
        order = self._create_mock_order(amount=0)
        order.amount_with_tax = None
        instance = self._create_mock_instance()

        self.db.query.return_value.filter.return_value.first.return_value = order
        self.service.engine.submit = Mock(return_value=instance)

        result = self.service.submit_orders_for_approval(
            order_ids=[1], initiator_id=100
        )

        self.assertEqual(len(result["success"]), 1)
        # 验证form_data中amount_with_tax为0
        call_args = self.service.engine.submit.call_args
        self.assertEqual(call_args[1]["form_data"]["amount_with_tax"], 0)


class TestGetPendingTasks(TestOutsourcingWorkflowService):
    """测试获取待审批任务"""

    def test_get_pending_tasks_success(self):
        """测试获取待审批任务成功"""
        order = self._create_mock_order()
        instance = self._create_mock_instance()
        task = self._create_mock_task(instance=instance)

        # Mock审批引擎返回任务
        self.service.engine.get_pending_tasks = Mock(return_value=[task])
        # Mock订单查询
        self.db.query.return_value.filter.return_value.first.return_value = order

        result = self.service.get_pending_tasks(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["order_no"], "WX202401001")

    def test_get_pending_tasks_with_pagination(self):
        """测试带分页的待审批任务"""
        tasks = []
        for i in range(15):
            instance = self._create_mock_instance(instance_id=i, entity_id=i)
            tasks.append(self._create_mock_task(task_id=i, instance=instance))

        self.service.engine.get_pending_tasks = Mock(return_value=tasks)

        # 构造订单查询的返回值序列
        orders = [self._create_mock_order(order_id=i) for i in range(10)]
        self.db.query.return_value.filter.return_value.first.side_effect = orders

        result = self.service.get_pending_tasks(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 15)
        self.assertEqual(len(result["items"]), 10)

    def test_get_pending_tasks_empty_result(self):
        """测试无待审批任务"""
        self.service.engine.get_pending_tasks = Mock(return_value=[])

        result = self.service.get_pending_tasks(user_id=10)

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_pending_tasks_order_not_found(self):
        """测试订单已删除的待审批任务"""
        instance = self._create_mock_instance()
        task = self._create_mock_task(instance=instance)

        self.service.engine.get_pending_tasks = Mock(return_value=[task])
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_pending_tasks(user_id=10)

        self.assertEqual(len(result["items"]), 1)
        self.assertIsNone(result["items"][0]["order_no"])
        self.assertIsNone(result["items"][0]["order_title"])

    def test_get_pending_tasks_with_missing_vendor(self):
        """测试外协商信息缺失的任务"""
        order = self._create_mock_order()
        order.vendor = None
        instance = self._create_mock_instance()
        task = self._create_mock_task(instance=instance)

        self.service.engine.get_pending_tasks = Mock(return_value=[task])
        self.db.query.return_value.filter.return_value.first.return_value = order

        result = self.service.get_pending_tasks(user_id=10)

        self.assertIsNone(result["items"][0]["vendor_name"])

    def test_get_pending_tasks_with_missing_project(self):
        """测试项目信息缺失的任务"""
        order = self._create_mock_order()
        order.project = None
        instance = self._create_mock_instance()
        task = self._create_mock_task(instance=instance)

        self.service.engine.get_pending_tasks = Mock(return_value=[task])
        self.db.query.return_value.filter.return_value.first.return_value = order

        result = self.service.get_pending_tasks(user_id=10)

        self.assertIsNone(result["items"][0]["project_name"])


class TestPerformApprovalAction(TestOutsourcingWorkflowService):
    """测试执行审批操作"""

    def test_approve_action_success(self):
        """测试审批通过成功"""
        instance = self._create_mock_instance(status="APPROVED")
        instance.entity_id = 1

        self.service.engine.approve = Mock(return_value=instance)
        self.service._trigger_cost_collection = Mock()

        result = self.service.perform_approval_action(
            task_id=1, approver_id=10, action="approve", comment="同意"
        )

        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service.engine.approve.assert_called_once_with(
            task_id=1, approver_id=10, comment="同意"
        )
        self.service._trigger_cost_collection.assert_called_once_with(1, 10)

    def test_approve_action_without_triggering_cost(self):
        """测试审批通过但未完成（不触发成本归集）"""
        instance = self._create_mock_instance(status="PENDING")
        self.service.engine.approve = Mock(return_value=instance)
        self.service._trigger_cost_collection = Mock()

        result = self.service.perform_approval_action(
            task_id=1, approver_id=10, action="approve"
        )

        self.assertEqual(result["instance_status"], "PENDING")
        self.service._trigger_cost_collection.assert_not_called()

    def test_reject_action_success(self):
        """测试审批驳回成功"""
        instance = self._create_mock_instance(status="REJECTED")
        self.service.engine.reject = Mock(return_value=instance)

        result = self.service.perform_approval_action(
            task_id=1, approver_id=10, action="reject", comment="不符合要求"
        )

        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.service.engine.reject.assert_called_once_with(
            task_id=1, approver_id=10, comment="不符合要求"
        )

    def test_perform_action_invalid_action(self):
        """测试无效的审批操作"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_approval_action(
                task_id=1, approver_id=10, action="invalid_action"
            )
        self.assertIn("不支持的操作类型", str(context.exception))

    def test_approve_without_comment(self):
        """测试无备注的审批"""
        instance = self._create_mock_instance()
        self.service.engine.approve = Mock(return_value=instance)

        result = self.service.perform_approval_action(
            task_id=1, approver_id=10, action="approve"
        )

        call_args = self.service.engine.approve.call_args
        self.assertIsNone(call_args[1]["comment"])


class TestPerformBatchApproval(TestOutsourcingWorkflowService):
    """测试批量审批操作"""

    def test_batch_approve_all_success(self):
        """测试批量审批全部成功"""
        instance = self._create_mock_instance(status="APPROVED")
        instance.entity_id = 1
        self.service.engine.approve = Mock(return_value=instance)
        self.service._trigger_cost_collection = Mock()

        result = self.service.perform_batch_approval(
            task_ids=[1, 2, 3], approver_id=10, action="approve"
        )

        self.assertEqual(len(result["success"]), 3)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.engine.approve.call_count, 3)
        self.assertEqual(self.service._trigger_cost_collection.call_count, 3)

    def test_batch_reject_all_success(self):
        """测试批量驳回全部成功"""
        instance = self._create_mock_instance()
        self.service.engine.reject = Mock(return_value=instance)

        result = self.service.perform_batch_approval(
            task_ids=[1, 2], approver_id=10, action="reject", comment="批量驳回"
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 0)

    def test_batch_approval_mixed_results(self):
        """测试批量审批混合结果"""
        instance = self._create_mock_instance()
        self.service.engine.approve = Mock(
            side_effect=[instance, Exception("审批失败"), instance]
        )

        result = self.service.perform_batch_approval(
            task_ids=[1, 2, 3], approver_id=10, action="approve"
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["task_id"], 2)

    def test_batch_approval_invalid_action(self):
        """测试批量审批无效操作"""
        result = self.service.perform_batch_approval(
            task_ids=[1, 2], approver_id=10, action="invalid"
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 2)

    def test_batch_approval_empty_list(self):
        """测试批量审批空列表"""
        result = self.service.perform_batch_approval(
            task_ids=[], approver_id=10, action="approve"
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 0)


class TestGetApprovalStatus(TestOutsourcingWorkflowService):
    """测试查询审批状态"""

    def test_get_approval_status_with_instance(self):
        """测试查询有审批实例的订单状态"""
        order = self._create_mock_order()
        instance = self._create_mock_instance()
        task1 = self._create_mock_task(task_id=1, instance=instance, status="APPROVED")
        task1.action = "approve"
        task1.completed_at = datetime(2024, 1, 1, 12, 0, 0)

        # 配置查询链
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            instance
        )
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            task1
        ]

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["instance_id"], 1)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)

    def test_get_approval_status_without_instance(self):
        """测试查询无审批实例的订单状态"""
        order = self._create_mock_order()

        # 第一次查询返回订单，第二次查询返回None（无实例）
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = order
        filter_mock.order_by.return_value.first.return_value = None

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(result["order_id"], 1)
        self.assertIsNone(result["approval_instance"])

    def test_get_approval_status_order_not_found(self):
        """测试查询不存在的订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_approval_status(order_id=999)
        self.assertIn("不存在", str(context.exception))

    def test_get_approval_status_with_multiple_tasks(self):
        """测试查询有多个审批任务的状态"""
        order = self._create_mock_order()
        instance = self._create_mock_instance()
        task1 = self._create_mock_task(task_id=1, instance=instance, status="APPROVED")
        task2 = self._create_mock_task(task_id=2, instance=instance, status="PENDING")

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = order
        filter_mock.order_by.return_value.first.return_value = instance
        filter_mock.order_by.return_value.all.return_value = [task1, task2]

        result = self.service.get_approval_status(order_id=1)

        self.assertEqual(len(result["task_history"]), 2)


class TestWithdrawApproval(TestOutsourcingWorkflowService):
    """测试撤回审批"""

    def test_withdraw_approval_success(self):
        """测试撤回审批成功"""
        order = self._create_mock_order()
        instance = self._create_mock_instance(initiator_id=100)

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [order, instance]

        self.service.engine.withdraw = Mock()

        result = self.service.withdraw_approval(
            order_id=1, user_id=100, reason="材料有误"
        )

        self.assertEqual(result["status"], "withdrawn")
        self.service.engine.withdraw.assert_called_once_with(
            instance_id=1, user_id=100
        )

    def test_withdraw_approval_order_not_found(self):
        """测试撤回不存在的订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=999, user_id=100)
        self.assertIn("不存在", str(context.exception))

    def test_withdraw_approval_no_pending_instance(self):
        """测试撤回无进行中审批的订单"""
        order = self._create_mock_order()

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [order, None]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=100)
        self.assertIn("没有进行中的审批", str(context.exception))

    def test_withdraw_approval_permission_denied(self):
        """测试撤回他人提交的审批"""
        order = self._create_mock_order()
        instance = self._create_mock_instance(initiator_id=100)

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [order, instance]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=200)
        self.assertIn("只能撤回自己提交", str(context.exception))


class TestGetApprovalHistory(TestOutsourcingWorkflowService):
    """测试获取审批历史"""

    def test_get_approval_history_success(self):
        """测试获取审批历史成功"""
        order = self._create_mock_order()
        instance = self._create_mock_instance()
        task = self._create_mock_task(instance=instance, status="APPROVED")
        task.action = "approve"
        task.completed_at = datetime(2024, 1, 1, 12, 0, 0)

        # Mock查询链
        query_mock = self.db.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.count.return_value = 1
        order_by_mock = filter_mock.order_by.return_value
        offset_mock = order_by_mock.offset.return_value
        limit_mock = offset_mock.limit.return_value
        limit_mock.all.return_value = [task]

        # Mock订单查询
        self.db.query.return_value.filter.return_value.first.return_value = order

        result = self.service.get_approval_history(user_id=10, offset=0, limit=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)

    def test_get_approval_history_with_status_filter(self):
        """测试带状态过滤的审批历史"""
        query_mock = self.db.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        
        # 当有status_filter时，会再次调用filter
        filter_mock2 = filter_mock.filter.return_value

        # 设置count和all返回空
        filter_mock2.count.return_value = 0
        filter_mock2.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        result = self.service.get_approval_history(
            user_id=10, status_filter="APPROVED"
        )

        # 验证过滤条件被调用
        self.assertEqual(result["total"], 0)

    def test_get_approval_history_empty(self):
        """测试无审批历史"""
        query_mock = self.db.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.count.return_value = 0
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        result = self.service.get_approval_history(user_id=10)

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_approval_history_with_pagination(self):
        """测试分页的审批历史"""
        tasks = []
        for i in range(5):
            instance = self._create_mock_instance(instance_id=i)
            task = self._create_mock_task(
                task_id=i, instance=instance, status="APPROVED"
            )
            tasks.append(task)

        query_mock = self.db.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.count.return_value = 15
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            tasks
        )

        # Mock订单查询
        orders = [self._create_mock_order(order_id=i) for i in range(5)]
        self.db.query.return_value.filter.return_value.first.side_effect = orders

        result = self.service.get_approval_history(user_id=10, offset=0, limit=5)

        self.assertEqual(result["total"], 15)
        self.assertEqual(len(result["items"]), 5)


class TestTriggerCostCollection(TestOutsourcingWorkflowService):
    """测试触发成本归集"""

    def test_approve_triggers_cost_collection(self):
        """测试审批通过后触发成本归集"""
        instance = self._create_mock_instance(status="APPROVED")
        instance.entity_id = 1

        # Mock引擎的approve方法
        self.service.engine.approve = Mock(return_value=instance)
        
        # Mock成本归集方法
        self.service._trigger_cost_collection = Mock()

        # 执行审批操作
        self.service.perform_approval_action(
            task_id=1, approver_id=10, action="approve", comment="同意"
        )

        # 验证成本归集被触发
        self.service._trigger_cost_collection.assert_called_once_with(1, 10)

    def test_approve_pending_not_trigger_cost_collection(self):
        """测试审批未完成不触发成本归集"""
        instance = self._create_mock_instance(status="PENDING")
        
        self.service.engine.approve = Mock(return_value=instance)
        self.service._trigger_cost_collection = Mock()

        self.service.perform_approval_action(
            task_id=1, approver_id=10, action="approve"
        )

        # 验证成本归集未被触发
        self.service._trigger_cost_collection.assert_not_called()

    def test_batch_approve_triggers_multiple_cost_collections(self):
        """测试批量审批触发多次成本归集"""
        instance = self._create_mock_instance(status="APPROVED")
        instance.entity_id = 1
        
        self.service.engine.approve = Mock(return_value=instance)
        self.service._trigger_cost_collection = Mock()

        # 批量审批3个任务
        self.service.perform_batch_approval(
            task_ids=[1, 2, 3], approver_id=10, action="approve"
        )

        # 验证成本归集被触发3次
        self.assertEqual(self.service._trigger_cost_collection.call_count, 3)


if __name__ == "__main__":
    unittest.main()

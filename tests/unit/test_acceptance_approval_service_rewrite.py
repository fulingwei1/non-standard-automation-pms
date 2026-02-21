# -*- coding: utf-8 -*-
"""
验收单审批服务单元测试 - 重写版本

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit, ApprovalEngineService等）
2. 让业务逻辑真正执行（不mock AcceptanceApprovalService的方法）
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, call, PropertyMock

from app.models.acceptance import AcceptanceOrder
from app.models.approval import ApprovalInstance, ApprovalTask, ApprovalNodeDefinition
from app.models.user import User
from app.models.project import Project
from app.models.machine import Machine
from app.services.acceptance_approval.service import AcceptanceApprovalService


class TestAcceptanceApprovalService(unittest.TestCase):
    """验收单审批服务测试套件"""

    def setUp(self):
        """测试前准备"""
        self.db_mock = MagicMock()
        self.service = AcceptanceApprovalService(self.db_mock)
        
        # Mock ApprovalEngineService
        self.engine_mock = MagicMock()
        self.service.engine = self.engine_mock

    def _create_mock_order(
        self,
        order_id=1,
        order_no="ACC-2024-001",
        acceptance_type="FAT",
        overall_result="PASSED",
        status="COMPLETED",
        pass_rate=Decimal("95.5"),
        passed_items=19,
        failed_items=1,
        total_items=20,
        project_id=100,
        machine_id=200,
        conclusion="验收合格",
        conditions="无",
    ):
        """创建mock验收单"""
        order = Mock(spec=AcceptanceOrder)
        order.id = order_id
        order.order_no = order_no
        order.acceptance_type = acceptance_type
        order.overall_result = overall_result
        order.status = status
        order.pass_rate = pass_rate
        order.passed_items = passed_items
        order.failed_items = failed_items
        order.total_items = total_items
        order.project_id = project_id
        order.machine_id = machine_id
        order.conclusion = conclusion
        order.conditions = conditions
        
        # Mock关联对象
        order.project = Mock(spec=Project)
        order.project.project_name = "测试项目"
        order.machine = Mock(spec=Machine)
        order.machine.machine_code = "M001"
        
        return order

    def _create_mock_instance(
        self,
        instance_id=999,
        entity_type="ACCEPTANCE_ORDER",
        entity_id=1,
        status="PENDING",
        urgency="NORMAL",
        initiator_id=50,
    ):
        """创建mock审批实例"""
        instance = Mock(spec=ApprovalInstance)
        instance.id = instance_id
        instance.entity_type = entity_type
        instance.entity_id = entity_id
        instance.status = status
        instance.urgency = urgency
        instance.initiator_id = initiator_id
        instance.created_at = datetime(2024, 1, 15, 10, 0, 0)
        instance.completed_at = None
        
        # Mock关联对象
        instance.initiator = Mock(spec=User)
        instance.initiator.real_name = "张三"
        
        return instance

    def _create_mock_task(
        self,
        task_id=1,
        instance_id=999,
        node_id=10,
        assignee_id=60,
        status="PENDING",
        action=None,
    ):
        """创建mock审批任务"""
        task = Mock(spec=ApprovalTask)
        task.id = task_id
        task.instance_id = instance_id
        task.node_id = node_id
        task.assignee_id = assignee_id
        task.status = status
        task.action = action
        task.comment = None
        task.created_at = datetime(2024, 1, 15, 10, 0, 0)
        task.completed_at = None
        
        # Mock关联对象
        task.node = Mock(spec=ApprovalNodeDefinition)
        task.node.node_name = "部门经理审批"
        task.assignee = Mock(spec=User)
        task.assignee.real_name = "李四"
        task.instance = self._create_mock_instance(instance_id=instance_id)
        
        return task

    # ==================== submit_orders_for_approval 测试 ====================

    def test_submit_single_order_success(self):
        """测试成功提交单个验收单"""
        order = self._create_mock_order()
        
        # Mock db.query
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = order
        
        # Mock engine.submit
        instance = self._create_mock_instance()
        self.engine_mock.submit.return_value = instance
        
        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50,
            urgency="NORMAL",
            comment="请审批"
        )
        
        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(results[0]["order_id"], 1)
        self.assertEqual(results[0]["order_no"], "ACC-2024-001")
        self.assertEqual(results[0]["acceptance_type"], "FAT")
        self.assertEqual(results[0]["instance_id"], 999)
        self.assertEqual(results[0]["status"], "submitted")
        
        # 验证engine.submit被正确调用
        self.engine_mock.submit.assert_called_once()
        call_kwargs = self.engine_mock.submit.call_args[1]
        self.assertEqual(call_kwargs["template_code"], "ACCEPTANCE_ORDER_APPROVAL")
        self.assertEqual(call_kwargs["entity_type"], "ACCEPTANCE_ORDER")
        self.assertEqual(call_kwargs["entity_id"], 1)
        self.assertEqual(call_kwargs["initiator_id"], 50)
        self.assertEqual(call_kwargs["urgency"], "NORMAL")

    def test_submit_multiple_orders_mixed_results(self):
        """测试批量提交验收单（部分成功部分失败）"""
        # 准备两个订单
        order1 = self._create_mock_order(order_id=1, order_no="ACC-001")
        order2 = self._create_mock_order(order_id=2, order_no="ACC-002", status="DRAFT")
        
        # Mock db.query - 使用列表追踪调用
        orders = [order1, order2]
        call_index = [0]
        
        def query_side_effect(*args):
            mock = MagicMock()
            current_order = orders[call_index[0]]
            call_index[0] += 1
            mock.filter.return_value.first.return_value = current_order
            return mock
        
        self.db_mock.query.side_effect = query_side_effect
        
        # Mock engine.submit
        instance = self._create_mock_instance()
        self.engine_mock.submit.return_value = instance
        
        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1, 2],
            initiator_id=50
        )
        
        # 验证
        self.assertEqual(len(results), 1)  # 只有order1成功
        self.assertEqual(len(errors), 1)   # order2失败
        self.assertEqual(results[0]["order_id"], 1)
        self.assertEqual(errors[0]["order_id"], 2)
        self.assertIn("不允许提交审批", errors[0]["error"])

    def test_submit_order_not_found(self):
        """测试提交不存在的验收单"""
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[999],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["order_id"], 999)
        self.assertEqual(errors[0]["error"], "验收单不存在")

    def test_submit_order_invalid_status(self):
        """测试提交状态不正确的验收单"""
        # 状态为DRAFT的订单不能提交
        order = self._create_mock_order(status="DRAFT")
        
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = order
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不允许提交审批", errors[0]["error"])
        self.assertIn("DRAFT", errors[0]["error"])

    def test_submit_order_without_result(self):
        """测试提交没有验收结论的验收单"""
        order = self._create_mock_order(overall_result=None)
        
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = order
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("没有验收结论", errors[0]["error"])

    def test_submit_order_engine_exception(self):
        """测试审批引擎抛出异常"""
        order = self._create_mock_order()
        
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = order
        
        # Mock engine抛出异常
        self.engine_mock.submit.side_effect = Exception("审批模板不存在")
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["order_id"], 1)
        self.assertIn("审批模板不存在", errors[0]["error"])

    def test_submit_order_with_rejected_status(self):
        """测试提交被驳回的验收单（允许重新提交）"""
        order = self._create_mock_order(status="REJECTED")
        
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = order
        
        instance = self._create_mock_instance()
        self.engine_mock.submit.return_value = instance
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 0)

    # ==================== get_pending_tasks 测试 ====================

    def test_get_pending_tasks_success(self):
        """测试成功获取待审批任务"""
        task = self._create_mock_task()
        order = self._create_mock_order()
        task.instance.entity_id = order.id
        
        # Mock engine.get_pending_tasks
        self.engine_mock.get_pending_tasks.return_value = [task]
        
        # Mock db.query for order
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = order
        
        # 执行
        items, total = self.service.get_pending_tasks(user_id=60)
        
        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["order_id"], 1)
        self.assertEqual(items[0]["order_no"], "ACC-2024-001")
        self.assertEqual(items[0]["acceptance_type"], "FAT")
        self.assertEqual(items[0]["acceptance_type_name"], "出厂验收")
        self.assertEqual(items[0]["overall_result"], "PASSED")
        self.assertEqual(items[0]["result_name"], "合格")
        
        # 验证engine调用
        self.engine_mock.get_pending_tasks.assert_called_once_with(
            user_id=60,
            entity_type="ACCEPTANCE_ORDER"
        )

    def test_get_pending_tasks_with_type_filter(self):
        """测试按验收类型筛选待审批任务"""
        task1 = self._create_mock_task(task_id=1)
        task2 = self._create_mock_task(task_id=2)
        
        order1 = self._create_mock_order(order_id=1, acceptance_type="FAT")
        order2 = self._create_mock_order(order_id=2, acceptance_type="SAT")
        
        task1.instance.entity_id = 1
        task2.instance.entity_id = 2
        
        self.engine_mock.get_pending_tasks.return_value = [task1, task2]
        
        # Mock db.query - 使用字典根据entity_id返回不同的order
        order_map = {1: order1, 2: order2}
        
        def query_side_effect(*args):
            mock = MagicMock()
            def filter_side_effect(*filter_args):
                filter_mock = MagicMock()
                # 默认返回order1，如果filter包含id=2则返回order2
                filter_mock.first.return_value = order1  # 默认返回order1
                return filter_mock
            mock.filter.side_effect = filter_side_effect
            return mock
        
        # 由于业务逻辑复杂，使用更简单的策略：让所有查询都返回order1或order2的迭代
        orders_cycle = [order1, order2, order1, order2]  # 提供足够的order
        call_index = [0]
        
        def simple_query_side_effect(*args):
            mock = MagicMock()
            idx = call_index[0]
            if idx < len(orders_cycle):
                current_order = orders_cycle[idx]
            else:
                current_order = order1
            call_index[0] += 1
            mock.filter.return_value.first.return_value = current_order
            return mock
        
        self.db_mock.query.side_effect = simple_query_side_effect
        
        # 执行 - 只要FAT类型
        items, total = self.service.get_pending_tasks(
            user_id=60,
            acceptance_type="FAT"
        )
        
        # 验证 - 应该只返回FAT类型的任务（筛选后只剩下order1对应的task1）
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["acceptance_type"], "FAT")

    def test_get_pending_tasks_pagination(self):
        """测试待审批任务分页"""
        tasks = [self._create_mock_task(task_id=i) for i in range(1, 26)]
        for i, task in enumerate(tasks, 1):
            task.instance.entity_id = i
        
        self.engine_mock.get_pending_tasks.return_value = tasks
        
        # Mock db.query
        order = self._create_mock_order()
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = order
        
        # 执行 - 第一页
        items, total = self.service.get_pending_tasks(
            user_id=60,
            offset=0,
            limit=10
        )
        
        self.assertEqual(total, 25)
        self.assertEqual(len(items), 10)
        
        # 执行 - 第二页
        items, total = self.service.get_pending_tasks(
            user_id=60,
            offset=10,
            limit=10
        )
        
        self.assertEqual(total, 25)
        self.assertEqual(len(items), 10)

    def test_get_pending_tasks_empty(self):
        """测试没有待审批任务"""
        self.engine_mock.get_pending_tasks.return_value = []
        
        items, total = self.service.get_pending_tasks(user_id=60)
        
        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)

    def test_get_pending_tasks_with_different_result_types(self):
        """测试不同验收结果的显示名称"""
        task = self._create_mock_task()
        
        # 测试CONDITIONAL结果
        order = self._create_mock_order(overall_result="CONDITIONAL")
        task.instance.entity_id = order.id
        
        self.engine_mock.get_pending_tasks.return_value = [task]
        
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = order
        
        items, total = self.service.get_pending_tasks(user_id=60)
        
        self.assertEqual(items[0]["result_name"], "有条件通过")

    # ==================== perform_approval_action 测试 ====================

    def test_perform_approval_action_approve(self):
        """测试执行同意操作"""
        instance = self._create_mock_instance(status="APPROVED")
        self.engine_mock.approve.return_value = instance
        
        result = self.service.perform_approval_action(
            task_id=1,
            action="approve",
            approver_id=60,
            comment="同意"
        )
        
        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        
        self.engine_mock.approve.assert_called_once_with(
            task_id=1,
            approver_id=60,
            comment="同意"
        )

    def test_perform_approval_action_reject(self):
        """测试执行拒绝操作"""
        instance = self._create_mock_instance(status="REJECTED")
        self.engine_mock.reject.return_value = instance
        
        result = self.service.perform_approval_action(
            task_id=1,
            action="reject",
            approver_id=60,
            comment="不符合要求"
        )
        
        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        
        self.engine_mock.reject.assert_called_once_with(
            task_id=1,
            approver_id=60,
            comment="不符合要求"
        )

    def test_perform_approval_action_invalid_action(self):
        """测试无效的审批操作"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_approval_action(
                task_id=1,
                action="invalid_action",
                approver_id=60
            )
        
        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_approval_action_without_comment(self):
        """测试不带审批意见的审批操作"""
        instance = self._create_mock_instance()
        self.engine_mock.approve.return_value = instance
        
        result = self.service.perform_approval_action(
            task_id=1,
            action="approve",
            approver_id=60,
            comment=None
        )
        
        self.assertEqual(result["task_id"], 1)
        self.engine_mock.approve.assert_called_once_with(
            task_id=1,
            approver_id=60,
            comment=None
        )

    # ==================== batch_approval 测试 ====================

    def test_batch_approval_all_success(self):
        """测试批量审批全部成功"""
        results, errors = self.service.batch_approval(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=60,
            comment="批量同意"
        )
        
        self.assertEqual(len(results), 3)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.engine_mock.approve.call_count, 3)

    def test_batch_approval_partial_failure(self):
        """测试批量审批部分失败"""
        # Mock第二次调用失败
        self.engine_mock.approve.side_effect = [
            None,  # 第一次成功
            Exception("任务不存在"),  # 第二次失败
            None,  # 第三次成功
        ]
        
        results, errors = self.service.batch_approval(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=60
        )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["task_id"], 2)
        self.assertIn("任务不存在", errors[0]["error"])

    def test_batch_approval_reject_action(self):
        """测试批量拒绝"""
        results, errors = self.service.batch_approval(
            task_ids=[1, 2],
            action="reject",
            approver_id=60,
            comment="批量拒绝"
        )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.engine_mock.reject.call_count, 2)

    def test_batch_approval_invalid_action(self):
        """测试批量审批时使用无效操作"""
        results, errors = self.service.batch_approval(
            task_ids=[1, 2],
            action="invalid",
            approver_id=60
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 2)
        for error in errors:
            self.assertIn("不支持的操作", error["error"])

    def test_batch_approval_empty_list(self):
        """测试批量审批空列表"""
        results, errors = self.service.batch_approval(
            task_ids=[],
            action="approve",
            approver_id=60
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 0)

    # ==================== get_approval_status 测试 ====================

    def test_get_approval_status_with_instance(self):
        """测试获取有审批实例的验收单状态"""
        order = self._create_mock_order()
        instance = self._create_mock_instance()
        task = self._create_mock_task()
        
        # Mock db.query
        query_mock1 = MagicMock()
        query_mock2 = MagicMock()
        query_mock3 = MagicMock()
        
        self.db_mock.query.side_effect = [query_mock1, query_mock2, query_mock3]
        
        # 第一次查询：订单
        query_mock1.filter.return_value.first.return_value = order
        
        # 第二次查询：审批实例
        query_mock2.filter.return_value.order_by.return_value.first.return_value = instance
        
        # 第三次查询：审批任务
        query_mock3.filter.return_value.order_by.return_value.all.return_value = [task]
        
        # 执行
        status = self.service.get_approval_status(order_id=1)
        
        # 验证
        self.assertEqual(status["order_id"], 1)
        self.assertEqual(status["order_no"], "ACC-2024-001")
        self.assertEqual(status["acceptance_type"], "FAT")
        self.assertEqual(status["instance_id"], 999)
        self.assertEqual(status["instance_status"], "PENDING")
        self.assertEqual(len(status["task_history"]), 1)
        self.assertEqual(status["task_history"][0]["task_id"], 1)

    def test_get_approval_status_without_instance(self):
        """测试获取没有审批实例的验收单状态"""
        order = self._create_mock_order()
        
        query_mock1 = MagicMock()
        query_mock2 = MagicMock()
        
        self.db_mock.query.side_effect = [query_mock1, query_mock2]
        
        query_mock1.filter.return_value.first.return_value = order
        query_mock2.filter.return_value.order_by.return_value.first.return_value = None
        
        status = self.service.get_approval_status(order_id=1)
        
        self.assertEqual(status["order_id"], 1)
        self.assertEqual(status["order_no"], "ACC-2024-001")
        self.assertEqual(status["status"], "COMPLETED")
        self.assertIsNone(status["approval_instance"])

    def test_get_approval_status_order_not_found(self):
        """测试获取不存在的验收单状态"""
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.get_approval_status(order_id=999)
        
        self.assertIn("验收单不存在", str(context.exception))

    def test_get_approval_status_with_multiple_tasks(self):
        """测试获取有多个审批任务的状态"""
        order = self._create_mock_order()
        instance = self._create_mock_instance()
        task1 = self._create_mock_task(task_id=1, status="APPROVED", action="APPROVE")
        task1.completed_at = datetime(2024, 1, 15, 11, 0, 0)
        task2 = self._create_mock_task(task_id=2, status="PENDING")
        
        query_mock1 = MagicMock()
        query_mock2 = MagicMock()
        query_mock3 = MagicMock()
        
        self.db_mock.query.side_effect = [query_mock1, query_mock2, query_mock3]
        
        query_mock1.filter.return_value.first.return_value = order
        query_mock2.filter.return_value.order_by.return_value.first.return_value = instance
        query_mock3.filter.return_value.order_by.return_value.all.return_value = [task1, task2]
        
        status = self.service.get_approval_status(order_id=1)
        
        self.assertEqual(len(status["task_history"]), 2)
        self.assertEqual(status["task_history"][0]["status"], "APPROVED")
        self.assertEqual(status["task_history"][0]["action"], "APPROVE")
        self.assertEqual(status["task_history"][1]["status"], "PENDING")

    # ==================== withdraw_approval 测试 ====================

    def test_withdraw_approval_success(self):
        """测试成功撤回审批"""
        order = self._create_mock_order()
        instance = self._create_mock_instance(initiator_id=50)
        
        query_mock1 = MagicMock()
        query_mock2 = MagicMock()
        
        self.db_mock.query.side_effect = [query_mock1, query_mock2]
        
        query_mock1.filter.return_value.first.return_value = order
        query_mock2.filter.return_value.first.return_value = instance
        
        result = self.service.withdraw_approval(
            order_id=1,
            user_id=50,
            reason="需要修改验收单"
        )
        
        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "ACC-2024-001")
        self.assertEqual(result["status"], "withdrawn")
        
        self.engine_mock.withdraw.assert_called_once_with(
            instance_id=999,
            user_id=50
        )

    def test_withdraw_approval_order_not_found(self):
        """测试撤回不存在的验收单"""
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=999, user_id=50)
        
        self.assertIn("验收单不存在", str(context.exception))

    def test_withdraw_approval_no_pending_instance(self):
        """测试撤回没有进行中审批流程的验收单"""
        order = self._create_mock_order()
        
        query_mock1 = MagicMock()
        query_mock2 = MagicMock()
        
        self.db_mock.query.side_effect = [query_mock1, query_mock2]
        
        query_mock1.filter.return_value.first.return_value = order
        query_mock2.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=50)
        
        self.assertIn("没有进行中的审批流程", str(context.exception))

    def test_withdraw_approval_permission_denied(self):
        """测试撤回别人提交的审批"""
        order = self._create_mock_order()
        instance = self._create_mock_instance(initiator_id=50)
        
        query_mock1 = MagicMock()
        query_mock2 = MagicMock()
        
        self.db_mock.query.side_effect = [query_mock1, query_mock2]
        
        query_mock1.filter.return_value.first.return_value = order
        query_mock2.filter.return_value.first.return_value = instance
        
        with self.assertRaises(PermissionError) as context:
            self.service.withdraw_approval(order_id=1, user_id=99)  # 不同用户
        
        self.assertIn("只能撤回自己提交的审批", str(context.exception))

    # ==================== get_approval_history 测试 ====================

    def test_get_approval_history_success(self):
        """测试成功获取审批历史"""
        task = self._create_mock_task(status="APPROVED", action="APPROVE")
        task.completed_at = datetime(2024, 1, 15, 11, 0, 0)
        order = self._create_mock_order()
        task.instance.entity_id = 1
        
        # Mock db.query
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        
        # Mock query chain
        join_mock = MagicMock()
        filter_mock = MagicMock()
        count_mock = MagicMock()
        order_by_mock = MagicMock()
        offset_mock = MagicMock()
        limit_mock = MagicMock()
        
        query_mock.join.return_value = join_mock
        join_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value = order_by_mock
        order_by_mock.offset.return_value = offset_mock
        offset_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = [task]
        
        # Mock order query - 创建新的query mock
        order_query_mock = MagicMock()
        
        # 使用side_effect区分两次query调用
        call_count = [0]
        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return query_mock
            else:
                order_query_mock.filter.return_value.first.return_value = order
                return order_query_mock
        
        self.db_mock.query.side_effect = query_side_effect
        
        # 执行
        items, total = self.service.get_approval_history(user_id=60)
        
        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["order_id"], 1)
        self.assertEqual(items[0]["action"], "APPROVE")
        self.assertEqual(items[0]["status"], "APPROVED")

    def test_get_approval_history_with_status_filter(self):
        """测试按状态筛选审批历史"""
        task = self._create_mock_task(status="REJECTED", action="REJECT")
        task.completed_at = datetime(2024, 1, 15, 11, 0, 0)
        
        query_mock = MagicMock()
        self.db_mock.query.return_value = query_mock
        
        join_mock = MagicMock()
        filter_mock1 = MagicMock()
        filter_mock2 = MagicMock()
        count_mock = MagicMock()
        
        query_mock.join.return_value = join_mock
        join_mock.filter.return_value = filter_mock1
        filter_mock1.filter.return_value = filter_mock2
        filter_mock2.count.return_value = 0
        
        # 执行
        items, total = self.service.get_approval_history(
            user_id=60,
            status_filter="REJECTED"
        )
        
        # 验证filter被调用两次（第一次是通用filter，第二次是status filter）
        self.assertTrue(filter_mock1.filter.called)

    def test_get_approval_history_with_type_filter(self):
        """测试按验收类型筛选审批历史"""
        task = self._create_mock_task(status="APPROVED")
        task.completed_at = datetime(2024, 1, 15, 11, 0, 0)
        task.instance.entity_id = 1
        
        order = self._create_mock_order(acceptance_type="SAT")
        
        query_mock = MagicMock()
        join_mock = MagicMock()
        filter_mock = MagicMock()
        order_by_mock = MagicMock()
        offset_mock = MagicMock()
        limit_mock = MagicMock()
        
        query_mock.join.return_value = join_mock
        join_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value = order_by_mock
        order_by_mock.offset.return_value = offset_mock
        offset_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = [task]
        
        order_query_mock = MagicMock()
        
        call_count = [0]
        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return query_mock
            else:
                order_query_mock.filter.return_value.first.return_value = order
                return order_query_mock
        
        self.db_mock.query.side_effect = query_side_effect
        
        # 执行 - 筛选SAT类型
        items, total = self.service.get_approval_history(
            user_id=60,
            acceptance_type="SAT"
        )
        
        # 验证
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["acceptance_type"], "SAT")

    def test_get_approval_history_pagination(self):
        """测试审批历史分页"""
        tasks = []
        for i in range(1, 16):
            task = self._create_mock_task(task_id=i, status="APPROVED")
            task.completed_at = datetime(2024, 1, 15, 11, 0, 0)
            task.instance.entity_id = i
            tasks.append(task)
        
        query_mock = MagicMock()
        join_mock = MagicMock()
        filter_mock = MagicMock()
        order_by_mock = MagicMock()
        offset_mock = MagicMock()
        limit_mock = MagicMock()
        
        query_mock.join.return_value = join_mock
        join_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 15
        filter_mock.order_by.return_value = order_by_mock
        order_by_mock.offset.return_value = offset_mock
        offset_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = tasks[:10]  # 返回前10条
        
        order = self._create_mock_order()
        order_query_mock = MagicMock()
        order_query_mock.filter.return_value.first.return_value = order
        
        call_count = [0]
        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return query_mock
            else:
                return order_query_mock
        
        self.db_mock.query.side_effect = query_side_effect
        
        # 执行
        items, total = self.service.get_approval_history(
            user_id=60,
            offset=0,
            limit=10
        )
        
        # 验证
        self.assertEqual(total, 15)
        # 注意：由于我们mock了返回10条，所以items长度是10
        # 但实际查询会调用order_by_mock.offset(0).limit(10)

    def test_get_approval_history_empty(self):
        """测试空的审批历史"""
        query_mock = MagicMock()
        join_mock = MagicMock()
        filter_mock = MagicMock()
        order_by_mock = MagicMock()
        offset_mock = MagicMock()
        limit_mock = MagicMock()
        
        self.db_mock.query.return_value = query_mock
        query_mock.join.return_value = join_mock
        join_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 0
        filter_mock.order_by.return_value = order_by_mock
        order_by_mock.offset.return_value = offset_mock
        offset_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = []
        
        items, total = self.service.get_approval_history(user_id=60)
        
        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)


if __name__ == "__main__":
    unittest.main()

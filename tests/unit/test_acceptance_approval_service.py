# -*- coding: utf-8 -*-
"""
验收单审批服务单元测试

目标:
1. 参考test_condition_parser_rewrite.py的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 所有测试必须通过
6. 目标覆盖率: 70%+
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, PropertyMock

from app.services.acceptance_approval.service import AcceptanceApprovalService


class TestAcceptanceApprovalServiceSubmit(unittest.TestCase):
    """测试提交审批相关方法"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = AcceptanceApprovalService(self.mock_db)

    def test_submit_orders_for_approval_success(self):
        """测试批量提交审批 - 成功场景"""
        # Mock验收单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "ACC-2024-001"
        mock_order.status = "COMPLETED"
        mock_order.overall_result = "PASSED"
        mock_order.acceptance_type = "FAT"
        mock_order.pass_rate = Decimal("95.50")
        mock_order.passed_items = 19
        mock_order.failed_items = 1
        mock_order.total_items = 20
        mock_order.project_id = 1
        mock_order.machine_id = 1
        mock_order.conclusion = "验收通过"
        mock_order.conditions = None

        # Mock查询结果
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        # Mock审批引擎
        mock_instance = MagicMock()
        mock_instance.id = 101
        self.service.engine.submit = MagicMock(return_value=mock_instance)

        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=1,
            urgency="NORMAL",
            comment="请审批"
        )

        # 验证
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(results[0]["order_id"], 1)
        self.assertEqual(results[0]["order_no"], "ACC-2024-001")
        self.assertEqual(results[0]["instance_id"], 101)
        self.assertEqual(results[0]["status"], "submitted")

        # 验证engine.submit被正确调用
        self.service.engine.submit.assert_called_once()
        call_args = self.service.engine.submit.call_args
        self.assertEqual(call_args[1]["template_code"], "ACCEPTANCE_ORDER_APPROVAL")
        self.assertEqual(call_args[1]["entity_type"], "ACCEPTANCE_ORDER")
        self.assertEqual(call_args[1]["entity_id"], 1)
        self.assertEqual(call_args[1]["initiator_id"], 1)

    def test_submit_orders_order_not_found(self):
        """测试提交审批 - 验收单不存在"""
        # Mock查询返回None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[999],
            initiator_id=1
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["order_id"], 999)
        self.assertEqual(errors[0]["error"], "验收单不存在")

    def test_submit_orders_invalid_status(self):
        """测试提交审批 - 状态不允许"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "DRAFT"  # 草稿状态不允许提交

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=1
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不允许提交审批", errors[0]["error"])

    def test_submit_orders_no_conclusion(self):
        """测试提交审批 - 没有验收结论"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "COMPLETED"
        mock_order.overall_result = None  # 没有结论

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=1
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("没有验收结论", errors[0]["error"])

    def test_submit_orders_batch_mixed_results(self):
        """测试批量提交 - 部分成功部分失败"""
        # Mock第一个订单成功
        mock_order1 = MagicMock()
        mock_order1.id = 1
        mock_order1.order_no = "ACC-001"
        mock_order1.status = "COMPLETED"
        mock_order1.overall_result = "PASSED"
        mock_order1.acceptance_type = "FAT"
        mock_order1.pass_rate = Decimal("95.00")
        mock_order1.passed_items = 19
        mock_order1.failed_items = 1
        mock_order1.total_items = 20
        mock_order1.project_id = 1
        mock_order1.machine_id = 1
        mock_order1.conclusion = "通过"
        mock_order1.conditions = None

        # 创建简单的调用计数器
        call_count = [0]
        
        def first_side_effect():
            call_count[0] += 1
            # 第一次调用返回订单1，第二次调用返回None
            if call_count[0] == 1:
                return mock_order1
            else:
                return None

        # Mock查询
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = first_side_effect

        # Mock审批引擎
        mock_instance = MagicMock()
        mock_instance.id = 101
        self.service.engine.submit = MagicMock(return_value=mock_instance)

        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1, 999],
            initiator_id=1
        )

        # 验证
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(results[0]["order_id"], 1)
        self.assertEqual(errors[0]["order_id"], 999)

    def test_submit_orders_engine_exception(self):
        """测试提交审批 - 审批引擎抛出异常"""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "COMPLETED"
        mock_order.overall_result = "PASSED"
        mock_order.acceptance_type = "FAT"
        mock_order.pass_rate = Decimal("95.00")
        mock_order.passed_items = 19
        mock_order.failed_items = 1
        mock_order.total_items = 20
        mock_order.project_id = 1
        mock_order.machine_id = 1
        mock_order.conclusion = "通过"
        mock_order.conditions = None

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        # Mock引擎抛出异常
        self.service.engine.submit = MagicMock(side_effect=Exception("审批流程配置错误"))

        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=1
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("审批流程配置错误", errors[0]["error"])


class TestAcceptanceApprovalServicePendingTasks(unittest.TestCase):
    """测试获取待审批任务相关方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = AcceptanceApprovalService(self.mock_db)

    def test_get_pending_tasks_success(self):
        """测试获取待审批任务 - 成功"""
        # Mock任务
        mock_task = MagicMock()
        mock_task.id = 1

        # Mock实例
        mock_instance = MagicMock()
        mock_instance.id = 101
        mock_instance.entity_id = 1
        mock_instance.urgency = "NORMAL"
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        
        # Mock发起人
        mock_initiator = MagicMock()
        mock_initiator.real_name = "张三"
        mock_instance.initiator = mock_initiator
        
        # Mock节点
        mock_node = MagicMock()
        mock_node.node_name = "部门经理审批"
        
        mock_task.instance = mock_instance
        mock_task.node = mock_node

        # Mock验收单
        mock_order = MagicMock()
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"
        mock_order.pass_rate = Decimal("95.50")
        
        # Mock项目和设备
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        mock_order.project = mock_project
        
        mock_machine = MagicMock()
        mock_machine.machine_code = "M001"
        mock_order.machine = mock_machine

        # Mock引擎返回任务列表
        self.service.engine.get_pending_tasks = MagicMock(return_value=[mock_task])

        # Mock查询验收单
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_order

        # 执行
        items, total = self.service.get_pending_tasks(user_id=1, offset=0, limit=20)

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["order_no"], "ACC-001")
        self.assertEqual(items[0]["acceptance_type"], "FAT")
        self.assertEqual(items[0]["acceptance_type_name"], "出厂验收")
        self.assertEqual(items[0]["result_name"], "合格")

    def test_get_pending_tasks_with_type_filter(self):
        """测试获取待审批任务 - 按类型过滤"""
        # Mock任务1 - FAT
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_instance1 = MagicMock()
        mock_instance1.entity_id = 1
        mock_instance1.urgency = "NORMAL"
        mock_instance1.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_instance1.initiator = MagicMock(real_name="张三")
        mock_task1.instance = mock_instance1
        mock_task1.node = MagicMock(node_name="审批")

        # Mock任务2 - SAT
        mock_task2 = MagicMock()
        mock_task2.id = 2
        mock_instance2 = MagicMock()
        mock_instance2.entity_id = 2
        mock_instance2.urgency = "NORMAL"
        mock_instance2.created_at = datetime(2024, 1, 2, 10, 0, 0)
        mock_instance2.initiator = MagicMock(real_name="李四")
        mock_task2.instance = mock_instance2
        mock_task2.node = MagicMock(node_name="审批")

        # Mock引擎返回两个任务
        self.service.engine.get_pending_tasks = MagicMock(return_value=[mock_task1, mock_task2])

        # Mock验收单
        mock_order1 = MagicMock()
        mock_order1.acceptance_type = "FAT"
        mock_order1.order_no = "ACC-001"
        mock_order1.overall_result = "PASSED"
        mock_order1.pass_rate = Decimal("95.00")
        mock_order1.project = MagicMock(project_name="项目1")
        mock_order1.machine = MagicMock(machine_code="M001")

        mock_order2 = MagicMock()
        mock_order2.acceptance_type = "SAT"
        mock_order2.order_no = "ACC-002"
        mock_order2.overall_result = "PASSED"
        mock_order2.pass_rate = Decimal("90.00")
        mock_order2.project = MagicMock(project_name="项目2")
        mock_order2.machine = MagicMock(machine_code="M002")

        # Mock查询 - 使用调用计数器交替返回不同的订单
        call_count = [0]
        
        def first_side_effect():
            call_count[0] += 1
            # 奇数次返回order1，偶数次返回order2
            if call_count[0] % 2 == 1:
                return mock_order1
            else:
                return mock_order2

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = first_side_effect

        # 执行 - 只要FAT类型
        items, total = self.service.get_pending_tasks(
            user_id=1,
            acceptance_type="FAT",
            offset=0,
            limit=20
        )

        # 验证 - 只应返回FAT类型的任务
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["acceptance_type"], "FAT")

    def test_get_pending_tasks_pagination(self):
        """测试获取待审批任务 - 分页"""
        # Mock 3个任务
        tasks = []
        for i in range(1, 4):
            mock_task = MagicMock()
            mock_task.id = i
            mock_instance = MagicMock()
            mock_instance.entity_id = i
            mock_instance.urgency = "NORMAL"
            mock_instance.created_at = datetime(2024, 1, i, 10, 0, 0)
            mock_instance.initiator = MagicMock(real_name=f"用户{i}")
            mock_task.instance = mock_instance
            mock_task.node = MagicMock(node_name="审批")
            tasks.append(mock_task)

        self.service.engine.get_pending_tasks = MagicMock(return_value=tasks)

        # Mock验收单
        def query_side_effect(*args):
            mock = MagicMock()
            def filter_side_effect(*filter_args):
                mock_filter = MagicMock()
                filter_str = str(filter_args)
                for i in range(1, 4):
                    if f"entity_id == {i}" in filter_str or f"id == {i}" in filter_str:
                        mock_order = MagicMock()
                        mock_order.order_no = f"ACC-00{i}"
                        mock_order.acceptance_type = "FAT"
                        mock_order.overall_result = "PASSED"
                        mock_order.pass_rate = Decimal("95.00")
                        mock_order.project = MagicMock(project_name=f"项目{i}")
                        mock_order.machine = MagicMock(machine_code=f"M00{i}")
                        mock_filter.first.return_value = mock_order
                        break
                return mock_filter
            mock.filter.side_effect = filter_side_effect
            return mock

        self.mock_db.query.side_effect = query_side_effect

        # 执行 - 第一页，每页2条
        items, total = self.service.get_pending_tasks(
            user_id=1,
            offset=0,
            limit=2
        )

        # 验证
        self.assertEqual(total, 3)
        self.assertEqual(len(items), 2)

        # 执行 - 第二页
        items, total = self.service.get_pending_tasks(
            user_id=1,
            offset=2,
            limit=2
        )

        # 验证
        self.assertEqual(total, 3)
        self.assertEqual(len(items), 1)

    def test_get_pending_tasks_empty(self):
        """测试获取待审批任务 - 空列表"""
        self.service.engine.get_pending_tasks = MagicMock(return_value=[])

        items, total = self.service.get_pending_tasks(user_id=1)

        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)


class TestAcceptanceApprovalServiceActions(unittest.TestCase):
    """测试审批操作相关方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = AcceptanceApprovalService(self.mock_db)

    def test_perform_approval_action_approve(self):
        """测试执行审批操作 - 通过"""
        # Mock返回结果
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        self.service.engine.approve = MagicMock(return_value=mock_result)

        # 执行
        result = self.service.perform_approval_action(
            task_id=1,
            action="approve",
            approver_id=1,
            comment="同意"
        )

        # 验证
        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service.engine.approve.assert_called_once_with(
            task_id=1,
            approver_id=1,
            comment="同意"
        )

    def test_perform_approval_action_reject(self):
        """测试执行审批操作 - 驳回"""
        mock_result = MagicMock()
        mock_result.status = "REJECTED"
        self.service.engine.reject = MagicMock(return_value=mock_result)

        # 执行
        result = self.service.perform_approval_action(
            task_id=1,
            action="reject",
            approver_id=1,
            comment="不同意"
        )

        # 验证
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.service.engine.reject.assert_called_once()

    def test_perform_approval_action_invalid(self):
        """测试执行审批操作 - 无效操作"""
        # 执行 - 应该抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.perform_approval_action(
                task_id=1,
                action="invalid_action",
                approver_id=1
            )

        self.assertIn("不支持的操作类型", str(context.exception))

    def test_batch_approval_success(self):
        """测试批量审批 - 全部成功"""
        self.service.engine.approve = MagicMock()

        # 执行
        results, errors = self.service.batch_approval(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=1,
            comment="批量同意"
        )

        # 验证
        self.assertEqual(len(results), 3)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.service.engine.approve.call_count, 3)

    def test_batch_approval_mixed_results(self):
        """测试批量审批 - 部分失败"""
        # Mock第2个失败
        def approve_side_effect(task_id, approver_id, comment):
            if task_id == 2:
                raise Exception("任务不存在")
            return MagicMock()

        self.service.engine.approve = MagicMock(side_effect=approve_side_effect)

        # 执行
        results, errors = self.service.batch_approval(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=1
        )

        # 验证
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["task_id"], 2)
        self.assertIn("任务不存在", errors[0]["error"])

    def test_batch_approval_invalid_action(self):
        """测试批量审批 - 无效操作"""
        results, errors = self.service.batch_approval(
            task_ids=[1],
            action="invalid",
            approver_id=1
        )

        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不支持的操作", errors[0]["error"])


class TestAcceptanceApprovalServiceStatus(unittest.TestCase):
    """测试获取审批状态相关方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = AcceptanceApprovalService(self.mock_db)

    def test_get_approval_status_with_instance(self):
        """测试获取审批状态 - 有审批实例"""
        # Mock验收单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"
        mock_order.status = "PENDING_APPROVAL"

        # Mock审批实例
        mock_instance = MagicMock()
        mock_instance.id = 101
        mock_instance.status = "PENDING"
        mock_instance.urgency = "NORMAL"
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_instance.completed_at = None

        # Mock审批任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "PENDING"
        mock_task.action = None
        mock_task.comment = None
        mock_task.completed_at = None
        
        mock_node = MagicMock()
        mock_node.node_name = "部门经理审批"
        mock_task.node = mock_node
        
        mock_assignee = MagicMock()
        mock_assignee.real_name = "张三"
        mock_task.assignee = mock_assignee

        # Mock查询链
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "AcceptanceOrder" in str(model):
                mock_query.filter.return_value.first.return_value = mock_order
            elif "ApprovalInstance" in str(model):
                mock_query.filter.return_value.order_by.return_value.first.return_value = mock_instance
            elif "ApprovalTask" in str(model):
                mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_task]
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.get_approval_status(order_id=1)

        # 验证
        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "ACC-001")
        self.assertEqual(result["instance_id"], 101)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)
        self.assertEqual(result["task_history"][0]["node_name"], "部门经理审批")

    def test_get_approval_status_no_instance(self):
        """测试获取审批状态 - 没有审批实例"""
        # Mock验收单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.status = "COMPLETED"

        # Mock查询链
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "AcceptanceOrder" in str(model):
                mock_query.filter.return_value.first.return_value = mock_order
            elif "ApprovalInstance" in str(model):
                mock_query.filter.return_value.order_by.return_value.first.return_value = None
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.get_approval_status(order_id=1)

        # 验证
        self.assertEqual(result["order_id"], 1)
        self.assertIsNone(result["approval_instance"])

    def test_get_approval_status_order_not_found(self):
        """测试获取审批状态 - 验收单不存在"""
        # Mock查询返回None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        # 执行 - 应该抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.get_approval_status(order_id=999)

        self.assertIn("验收单不存在", str(context.exception))


class TestAcceptanceApprovalServiceWithdraw(unittest.TestCase):
    """测试撤回审批相关方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = AcceptanceApprovalService(self.mock_db)

    def test_withdraw_approval_success(self):
        """测试撤回审批 - 成功"""
        # Mock验收单
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "ACC-001"

        # Mock审批实例
        mock_instance = MagicMock()
        mock_instance.id = 101
        mock_instance.status = "PENDING"
        mock_instance.initiator_id = 1  # 发起人是用户1

        # Mock查询链
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "AcceptanceOrder" in str(model):
                mock_query.filter.return_value.first.return_value = mock_order
            elif "ApprovalInstance" in str(model):
                mock_query.filter.return_value.first.return_value = mock_instance
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # Mock引擎撤回方法
        self.service.engine.withdraw = MagicMock()

        # 执行
        result = self.service.withdraw_approval(
            order_id=1,
            user_id=1,
            reason="需要修改"
        )

        # 验证
        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "ACC-001")
        self.assertEqual(result["status"], "withdrawn")
        self.service.engine.withdraw.assert_called_once_with(
            instance_id=101,
            user_id=1
        )

    def test_withdraw_approval_order_not_found(self):
        """测试撤回审批 - 验收单不存在"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        # 执行 - 应该抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=999, user_id=1)

        self.assertIn("验收单不存在", str(context.exception))

    def test_withdraw_approval_no_pending_instance(self):
        """测试撤回审批 - 没有进行中的审批"""
        # Mock验收单
        mock_order = MagicMock()
        mock_order.id = 1

        # Mock查询链
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "AcceptanceOrder" in str(model):
                mock_query.filter.return_value.first.return_value = mock_order
            elif "ApprovalInstance" in str(model):
                mock_query.filter.return_value.first.return_value = None  # 没有进行中的实例
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行 - 应该抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=1)

        self.assertIn("没有进行中的审批流程可撤回", str(context.exception))

    def test_withdraw_approval_permission_denied(self):
        """测试撤回审批 - 权限不足"""
        # Mock验收单
        mock_order = MagicMock()
        mock_order.id = 1

        # Mock审批实例
        mock_instance = MagicMock()
        mock_instance.id = 101
        mock_instance.status = "PENDING"
        mock_instance.initiator_id = 1  # 发起人是用户1

        # Mock查询链
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "AcceptanceOrder" in str(model):
                mock_query.filter.return_value.first.return_value = mock_order
            elif "ApprovalInstance" in str(model):
                mock_query.filter.return_value.first.return_value = mock_instance
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行 - 用户2尝试撤回用户1的审批
        with self.assertRaises(PermissionError) as context:
            self.service.withdraw_approval(order_id=1, user_id=2)

        self.assertIn("只能撤回自己提交的审批", str(context.exception))


class TestAcceptanceApprovalServiceHistory(unittest.TestCase):
    """测试获取审批历史相关方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = AcceptanceApprovalService(self.mock_db)

    def test_get_approval_history_success(self):
        """测试获取审批历史 - 成功"""
        # Mock审批任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "APPROVED"
        mock_task.action = "APPROVE"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 1, 15, 0, 0)

        # Mock实例
        mock_instance = MagicMock()
        mock_instance.entity_id = 1
        mock_task.instance = mock_instance

        # Mock验收单
        mock_order = MagicMock()
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"

        # Mock查询链
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "ApprovalTask" in str(model):
                mock_join = MagicMock()
                mock_filter = MagicMock()
                mock_filter.count.return_value = 1
                mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_task]
                mock_join.filter.return_value = mock_filter
                mock_query.join.return_value = mock_join
            elif "AcceptanceOrder" in str(model):
                mock_query.filter.return_value.first.return_value = mock_order
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行
        items, total = self.service.get_approval_history(
            user_id=1,
            offset=0,
            limit=20
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 1)
        self.assertEqual(items[0]["order_no"], "ACC-001")
        self.assertEqual(items[0]["action"], "APPROVE")
        self.assertEqual(items[0]["status"], "APPROVED")

    def test_get_approval_history_with_type_filter(self):
        """测试获取审批历史 - 按类型过滤"""
        # Mock任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "APPROVED"
        mock_task.action = "APPROVE"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 1, 15, 0, 0)

        mock_instance = MagicMock()
        mock_instance.entity_id = 1
        mock_task.instance = mock_instance

        # Mock验收单 - FAT类型
        mock_order = MagicMock()
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"

        # Mock查询链
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "ApprovalTask" in str(model):
                mock_join = MagicMock()
                mock_filter = MagicMock()
                mock_filter.count.return_value = 1
                mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_task]
                mock_join.filter.return_value = mock_filter
                mock_query.join.return_value = mock_join
            elif "AcceptanceOrder" in str(model):
                mock_query.filter.return_value.first.return_value = mock_order
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行 - 指定FAT类型
        items, total = self.service.get_approval_history(
            user_id=1,
            acceptance_type="FAT",
            offset=0,
            limit=20
        )

        # 验证
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["acceptance_type"], "FAT")

    def test_get_approval_history_with_status_filter(self):
        """测试获取审批历史 - 按状态过滤"""
        # Mock任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "APPROVED"
        mock_task.action = "APPROVE"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 1, 15, 0, 0)

        mock_instance = MagicMock()
        mock_instance.entity_id = 1
        mock_task.instance = mock_instance

        mock_order = MagicMock()
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"

        # Mock查询链 - 注意状态过滤会在query中体现
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "ApprovalTask" in str(model):
                mock_join = MagicMock()
                
                # 创建一个可链式调用的filter mock
                def create_filter_chain():
                    mock_filter = MagicMock()
                    mock_filter.filter.return_value = mock_filter  # 支持链式filter
                    mock_filter.count.return_value = 1
                    mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_task]
                    return mock_filter
                
                mock_join.filter.return_value = create_filter_chain()
                mock_query.join.return_value = mock_join
            elif "AcceptanceOrder" in str(model):
                mock_query.filter.return_value.first.return_value = mock_order
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行
        items, total = self.service.get_approval_history(
            user_id=1,
            status_filter="APPROVED",
            offset=0,
            limit=20
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["status"], "APPROVED")

    def test_get_approval_history_empty(self):
        """测试获取审批历史 - 空列表"""
        # Mock查询链返回空
        def query_side_effect(model):
            mock_query = MagicMock()
            
            if "ApprovalTask" in str(model):
                mock_join = MagicMock()
                mock_filter = MagicMock()
                mock_filter.count.return_value = 0
                mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
                mock_join.filter.return_value = mock_filter
                mock_query.join.return_value = mock_join
            
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行
        items, total = self.service.get_approval_history(user_id=1)

        # 验证
        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
验收单审批服务增强单元测试
目标覆盖率: 70%+
测试用例数: 25-35个
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.models.acceptance import AcceptanceOrder
from app.models.approval import ApprovalInstance, ApprovalTask
from app.services.acceptance_approval.service import AcceptanceApprovalService


class TestAcceptanceApprovalServiceEnhanced(unittest.TestCase):
    """验收单审批服务增强测试套件"""

    def setUp(self):
        """测试前准备"""
        self.db_mock = MagicMock()
        self.service = AcceptanceApprovalService(self.db_mock)
        
        # Mock ApprovalEngineService
        self.engine_mock = MagicMock()
        self.service.engine = self.engine_mock

    def tearDown(self):
        """测试后清理"""
        self.db_mock.reset_mock()
        self.engine_mock.reset_mock()

    # ==================== submit_orders_for_approval 测试 ====================

    def test_submit_single_order_success(self):
        """测试成功提交单个验收单"""
        # 准备数据
        order = AcceptanceOrder(
            id=1,
            order_no="ACC-2024-001",
            acceptance_type="FAT",
            overall_result="PASSED",
            pass_rate=Decimal("95.5"),
            passed_items=19,
            failed_items=1,
            total_items=20,
            project_id=100,
            machine_id=200,
            conclusion="验收合格",
            conditions="无",
            status="COMPLETED"
        )
        
        # Mock数据库查询
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        
        # Mock审批引擎提交
        instance_mock = MagicMock()
        instance_mock.id = 999
        self.engine_mock.submit.return_value = instance_mock
        
        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50,
            urgency="NORMAL",
            comment="请审批"
        )
        
        # 验证
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(results[0]["order_id"], 1)
        self.assertEqual(results[0]["order_no"], "ACC-2024-001")
        self.assertEqual(results[0]["instance_id"], 999)
        self.assertEqual(results[0]["status"], "submitted")
        
        # 验证调用
        self.engine_mock.submit.assert_called_once()
        call_kwargs = self.engine_mock.submit.call_args[1]
        self.assertEqual(call_kwargs["template_code"], "ACCEPTANCE_ORDER_APPROVAL")
        self.assertEqual(call_kwargs["entity_type"], "ACCEPTANCE_ORDER")
        self.assertEqual(call_kwargs["entity_id"], 1)
        self.assertEqual(call_kwargs["initiator_id"], 50)
        self.assertEqual(call_kwargs["urgency"], "NORMAL")

    def test_submit_order_not_found(self):
        """测试提交不存在的验收单"""
        # Mock数据库查询返回None
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[999],
            initiator_id=50
        )
        
        # 验证
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["order_id"], 999)
        self.assertEqual(errors[0]["error"], "验收单不存在")

    def test_submit_order_invalid_status(self):
        """测试提交状态不允许的验收单"""
        order = AcceptanceOrder(
            id=1,
            order_no="ACC-2024-001",
            status="DRAFT"  # 草稿状态不允许提交
        )
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("不允许提交审批", errors[0]["error"])

    def test_submit_order_no_result(self):
        """测试提交没有验收结论的验收单"""
        order = AcceptanceOrder(
            id=1,
            order_no="ACC-2024-001",
            status="COMPLETED",
            overall_result=None  # 没有验收结论
        )
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("没有验收结论", errors[0]["error"])

    def test_submit_multiple_orders_mixed(self):
        """测试批量提交（部分成功部分失败）"""
        # 准备多个订单
        order1 = AcceptanceOrder(
            id=1, order_no="ACC-001", status="COMPLETED",
            overall_result="PASSED", acceptance_type="FAT",
            pass_rate=Decimal("90"), passed_items=9, failed_items=1, total_items=10,
            project_id=100, machine_id=200
        )
        order2 = AcceptanceOrder(
            id=2, order_no="ACC-002", status="DRAFT"  # 状态不对
        )
        order3 = AcceptanceOrder(
            id=3, order_no="ACC-003", status="COMPLETED",
            overall_result="FAILED", acceptance_type="SAT",
            pass_rate=Decimal("60"), passed_items=6, failed_items=4, total_items=10,
            project_id=101, machine_id=201
        )
        
        # Mock数据库查询 - 用side_effect返回不同的订单
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [order1, order2, order3]
        
        # Mock审批引擎 - order1成功，order3成功（order2因状态问题不会调用引擎）
        instance_mock1 = MagicMock(id=1001)
        instance_mock3 = MagicMock(id=1003)
        self.engine_mock.submit.side_effect = [instance_mock1, instance_mock3]
        
        # 执行
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1, 2, 3],
            initiator_id=50
        )
        
        # 验证
        self.assertEqual(len(results), 2)  # 1和3成功
        self.assertEqual(len(errors), 1)   # 2失败
        self.assertEqual(errors[0]["order_id"], 2)

    def test_submit_order_engine_exception(self):
        """测试审批引擎抛出异常"""
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", status="COMPLETED",
            overall_result="PASSED", acceptance_type="FAT",
            pass_rate=Decimal("90"), passed_items=9, failed_items=1, total_items=10,
            project_id=100, machine_id=200
        )
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        self.engine_mock.submit.side_effect = Exception("审批引擎错误")
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error"], "审批引擎错误")

    def test_submit_order_with_rejected_status(self):
        """测试提交被驳回状态的验收单（允许）"""
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", status="REJECTED",
            overall_result="FAILED", acceptance_type="FAT",
            pass_rate=Decimal("50"), passed_items=5, failed_items=5, total_items=10,
            project_id=100, machine_id=200
        )
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        instance_mock = MagicMock(id=888)
        self.engine_mock.submit.return_value = instance_mock
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 0)

    def test_submit_order_with_urgency_high(self):
        """测试提交紧急审批"""
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", status="COMPLETED",
            overall_result="PASSED", acceptance_type="FINAL",
            pass_rate=Decimal("100"), passed_items=10, failed_items=0, total_items=10,
            project_id=100, machine_id=200
        )
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        instance_mock = MagicMock(id=777)
        self.engine_mock.submit.return_value = instance_mock
        
        results, errors = self.service.submit_orders_for_approval(
            order_ids=[1],
            initiator_id=50,
            urgency="HIGH",
            comment="紧急审批"
        )
        
        self.assertEqual(len(results), 1)
        call_kwargs = self.engine_mock.submit.call_args[1]
        self.assertEqual(call_kwargs["urgency"], "HIGH")

    # ==================== get_pending_tasks 测试 ====================

    def test_get_pending_tasks_basic(self):
        """测试获取待审批任务基本功能"""
        # 创建Mock任务
        task1 = MagicMock()
        task1.id = 101
        task1.instance = MagicMock()
        task1.instance.id = 201
        task1.instance.entity_id = 1
        task1.instance.created_at = datetime(2024, 1, 15, 10, 0, 0)
        task1.instance.urgency = "NORMAL"
        task1.instance.initiator = MagicMock(real_name="张三")
        task1.node = MagicMock(node_name="部门审批")
        
        # 创建Mock验收单
        order1 = AcceptanceOrder(
            id=1, order_no="ACC-001", acceptance_type="FAT",
            overall_result="PASSED", pass_rate=Decimal("95")
        )
        order1.project = MagicMock(project_name="项目A")
        order1.machine = MagicMock(machine_code="M001")
        
        # Mock引擎返回任务列表
        self.engine_mock.get_pending_tasks.return_value = [task1]
        
        # Mock数据库查询订单
        self.db_mock.query.return_value.filter.return_value.first.return_value = order1
        
        # 执行
        items, total = self.service.get_pending_tasks(user_id=50)
        
        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 101)
        self.assertEqual(items[0]["order_no"], "ACC-001")
        self.assertEqual(items[0]["acceptance_type"], "FAT")
        self.assertEqual(items[0]["acceptance_type_name"], "出厂验收")

    def test_get_pending_tasks_with_type_filter(self):
        """测试按验收类型筛选待审批任务"""
        # 创建两个不同类型的任务
        task1 = MagicMock()
        task1.instance = MagicMock(entity_id=1)
        order1 = AcceptanceOrder(id=1, order_no="ACC-001", acceptance_type="FAT")
        
        task2 = MagicMock()
        task2.instance = MagicMock(entity_id=2)
        order2 = AcceptanceOrder(id=2, order_no="ACC-002", acceptance_type="SAT")
        
        self.engine_mock.get_pending_tasks.return_value = [task1, task2]
        
        # Mock数据库查询，根据entity_id返回不同order
        def mock_query_first():
            call_count = [0]
            def get_first():
                call_count[0] += 1
                return order1 if call_count[0] == 1 else order2
            return get_first
        
        self.db_mock.query.return_value.filter.return_value.first = mock_query_first()
        
        # 执行 - 只筛选FAT类型
        items, total = self.service.get_pending_tasks(
            user_id=50,
            acceptance_type="FAT"
        )
        
        # 验证 - 应该只返回1个FAT类型的任务
        self.assertEqual(total, 1)

    def test_get_pending_tasks_pagination(self):
        """测试分页功能"""
        # 创建10个任务
        tasks = []
        for i in range(10):
            task = MagicMock()
            task.id = 100 + i
            task.instance = MagicMock(entity_id=i, created_at=datetime.now(), urgency="NORMAL")
            task.instance.initiator = MagicMock(real_name=f"User{i}")
            task.node = MagicMock(node_name=f"Node{i}")
            tasks.append(task)
            
        self.engine_mock.get_pending_tasks.return_value = tasks
        
        # Mock订单查询
        def create_order(i):
            order = AcceptanceOrder(
                id=i, order_no=f"ACC-{i:03d}",
                acceptance_type="FAT", overall_result="PASSED",
                pass_rate=Decimal("90")
            )
            order.project = MagicMock(project_name=f"Project{i}")
            order.machine = MagicMock(machine_code=f"M{i:03d}")
            return order
        
        order_list = [create_order(i) for i in range(10)]
        self.db_mock.query.return_value.filter.return_value.first.side_effect = order_list
        
        # 执行 - 获取第2页，每页3条
        items, total = self.service.get_pending_tasks(
            user_id=50,
            offset=3,
            limit=3
        )
        
        # 验证
        self.assertEqual(total, 10)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["task_id"], 103)  # 第4个任务

    def test_get_pending_tasks_empty(self):
        """测试无待审批任务"""
        self.engine_mock.get_pending_tasks.return_value = []
        
        items, total = self.service.get_pending_tasks(user_id=50)
        
        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)

    def test_get_pending_tasks_result_name_mapping(self):
        """测试验收结果名称映射"""
        task = MagicMock()
        task.id = 101
        task.instance = MagicMock(entity_id=1, created_at=datetime.now(), urgency="NORMAL")
        task.instance.initiator = MagicMock(real_name="张三")
        task.node = MagicMock(node_name="审批")
        
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", acceptance_type="SAT",
            overall_result="CONDITIONAL", pass_rate=Decimal("85")
        )
        order.project = MagicMock(project_name="Project")
        order.machine = MagicMock(machine_code="M001")
        
        self.engine_mock.get_pending_tasks.return_value = [task]
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        
        items, total = self.service.get_pending_tasks(user_id=50)
        
        self.assertEqual(items[0]["result_name"], "有条件通过")
        self.assertEqual(items[0]["acceptance_type_name"], "现场验收")

    # ==================== perform_approval_action 测试 ====================

    def test_perform_approval_action_approve(self):
        """测试审批通过操作"""
        result_mock = MagicMock(status="APPROVED")
        self.engine_mock.approve.return_value = result_mock
        
        result = self.service.perform_approval_action(
            task_id=101,
            action="approve",
            approver_id=50,
            comment="同意"
        )
        
        self.assertEqual(result["task_id"], 101)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.engine_mock.approve.assert_called_once_with(
            task_id=101, approver_id=50, comment="同意"
        )

    def test_perform_approval_action_reject(self):
        """测试审批拒绝操作"""
        result_mock = MagicMock(status="REJECTED")
        self.engine_mock.reject.return_value = result_mock
        
        result = self.service.perform_approval_action(
            task_id=101,
            action="reject",
            approver_id=50,
            comment="不符合要求"
        )
        
        self.assertEqual(result["task_id"], 101)
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.engine_mock.reject.assert_called_once_with(
            task_id=101, approver_id=50, comment="不符合要求"
        )

    def test_perform_approval_action_invalid_action(self):
        """测试无效的审批操作"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_approval_action(
                task_id=101,
                action="invalid_action",
                approver_id=50
            )
        
        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_approval_action_no_comment(self):
        """测试无审批意见的审批"""
        result_mock = MagicMock(status="APPROVED")
        self.engine_mock.approve.return_value = result_mock
        
        result = self.service.perform_approval_action(
            task_id=101,
            action="approve",
            approver_id=50
        )
        
        self.assertEqual(result["task_id"], 101)
        self.engine_mock.approve.assert_called_once_with(
            task_id=101, approver_id=50, comment=None
        )

    # ==================== batch_approval 测试 ====================

    def test_batch_approval_all_success(self):
        """测试批量审批全部成功"""
        self.engine_mock.approve.return_value = MagicMock()
        
        results, errors = self.service.batch_approval(
            task_ids=[101, 102, 103],
            action="approve",
            approver_id=50,
            comment="批量同意"
        )
        
        self.assertEqual(len(results), 3)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.engine_mock.approve.call_count, 3)

    def test_batch_approval_partial_failure(self):
        """测试批量审批部分失败"""
        # 第二次调用抛出异常
        self.engine_mock.approve.side_effect = [
            MagicMock(),
            Exception("审批失败"),
            MagicMock()
        ]
        
        results, errors = self.service.batch_approval(
            task_ids=[101, 102, 103],
            action="approve",
            approver_id=50
        )
        
        self.assertEqual(len(results), 2)  # 101和103成功
        self.assertEqual(len(errors), 1)   # 102失败
        self.assertEqual(errors[0]["task_id"], 102)

    def test_batch_approval_reject(self):
        """测试批量拒绝"""
        self.engine_mock.reject.return_value = MagicMock()
        
        results, errors = self.service.batch_approval(
            task_ids=[101, 102],
            action="reject",
            approver_id=50,
            comment="批量拒绝"
        )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.engine_mock.reject.call_count, 2)

    def test_batch_approval_invalid_action(self):
        """测试批量审批使用无效操作"""
        results, errors = self.service.batch_approval(
            task_ids=[101, 102],
            action="invalid",
            approver_id=50
        )
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 2)
        self.assertIn("不支持的操作", errors[0]["error"])

    # ==================== get_approval_status 测试 ====================

    def test_get_approval_status_with_instance(self):
        """测试获取有审批实例的状态"""
        # 准备订单
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", acceptance_type="FAT",
            overall_result="PASSED", status="PENDING_APPROVAL"
        )
        
        # 准备审批实例
        instance = ApprovalInstance(
            id=201,
            entity_type="ACCEPTANCE_ORDER",
            entity_id=1,
            status="PENDING",
            urgency="NORMAL",
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            completed_at=None
        )
        
        # 准备审批任务
        task1 = ApprovalTask(
            id=301,
            instance_id=201,
            status="APPROVED",
            action="approve",
            comment="同意",
            completed_at=datetime(2024, 1, 15, 11, 0, 0)
        )
        task1.node = MagicMock(node_name="部门审批")
        task1.assignee = MagicMock(real_name="李四")
        
        # Mock数据库查询 - 需要分别Mock不同的查询链
        # 第一次query().filter().first() 返回 order
        # 第二次query().filter().order_by().first() 返回 instance
        # 第三次query().filter().order_by().all() 返回 tasks
        order_query_mock = MagicMock()
        order_query_mock.filter.return_value.first.return_value = order
        
        instance_query_mock = MagicMock()
        instance_query_mock.filter.return_value.order_by.return_value.first.return_value = instance
        
        task_query_mock = MagicMock()
        task_query_mock.filter.return_value.order_by.return_value.all.return_value = [task1]
        
        self.db_mock.query.side_effect = [order_query_mock, instance_query_mock, task_query_mock]
        
        # 执行
        result = self.service.get_approval_status(order_id=1)
        
        # 验证
        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["order_no"], "ACC-001")
        self.assertEqual(result["instance_id"], 201)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)
        self.assertEqual(result["task_history"][0]["task_id"], 301)

    def test_get_approval_status_without_instance(self):
        """测试获取无审批实例的状态"""
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", acceptance_type="SAT",
            status="COMPLETED"
        )
        
        # Mock - 第一次查order，第二次查instance返回None
        order_query_mock = MagicMock()
        order_query_mock.filter.return_value.first.return_value = order
        
        instance_query_mock = MagicMock()
        instance_query_mock.filter.return_value.order_by.return_value.first.return_value = None
        
        self.db_mock.query.side_effect = [order_query_mock, instance_query_mock]
        
        result = self.service.get_approval_status(order_id=1)
        
        self.assertEqual(result["order_id"], 1)
        self.assertIsNone(result["approval_instance"])

    def test_get_approval_status_order_not_found(self):
        """测试查询不存在的订单状态"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.get_approval_status(order_id=999)
        
        self.assertEqual(str(context.exception), "验收单不存在")

    def test_get_approval_status_multiple_tasks(self):
        """测试获取包含多个审批任务的状态"""
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", acceptance_type="FINAL",
            overall_result="CONDITIONAL", status="APPROVED"
        )
        
        instance = ApprovalInstance(
            id=201,
            entity_type="ACCEPTANCE_ORDER",
            entity_id=1,
            status="COMPLETED",
            urgency="HIGH",
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            completed_at=datetime(2024, 1, 15, 12, 0, 0)
        )
        
        # 多个任务
        task1 = ApprovalTask(id=301, status="APPROVED", action="approve", comment="部门同意")
        task1.node = MagicMock(node_name="部门审批")
        task1.assignee = MagicMock(real_name="张三")
        task1.completed_at = datetime(2024, 1, 15, 11, 0, 0)
        
        task2 = ApprovalTask(id=302, status="APPROVED", action="approve", comment="总经理同意")
        task2.node = MagicMock(node_name="总经理审批")
        task2.assignee = MagicMock(real_name="王五")
        task2.completed_at = datetime(2024, 1, 15, 12, 0, 0)
        
        # Mock查询
        order_query_mock = MagicMock()
        order_query_mock.filter.return_value.first.return_value = order
        
        instance_query_mock = MagicMock()
        instance_query_mock.filter.return_value.order_by.return_value.first.return_value = instance
        
        task_query_mock = MagicMock()
        task_query_mock.filter.return_value.order_by.return_value.all.return_value = [task1, task2]
        
        self.db_mock.query.side_effect = [order_query_mock, instance_query_mock, task_query_mock]
        
        result = self.service.get_approval_status(order_id=1)
        
        self.assertEqual(len(result["task_history"]), 2)
        self.assertEqual(result["task_history"][0]["node_name"], "部门审批")
        self.assertEqual(result["task_history"][1]["node_name"], "总经理审批")

    # ==================== withdraw_approval 测试 ====================

    def test_withdraw_approval_success(self):
        """测试成功撤回审批"""
        order = AcceptanceOrder(id=1, order_no="ACC-001")
        
        instance = ApprovalInstance(
            id=201,
            entity_type="ACCEPTANCE_ORDER",
            entity_id=1,
            status="PENDING",
            initiator_id=50
        )
        
        # Mock两次查询
        order_query_mock = MagicMock()
        order_query_mock.filter.return_value.first.return_value = order
        
        instance_query_mock = MagicMock()
        instance_query_mock.filter.return_value.first.return_value = instance
        
        self.db_mock.query.side_effect = [order_query_mock, instance_query_mock]
        self.engine_mock.withdraw.return_value = None
        
        result = self.service.withdraw_approval(
            order_id=1,
            user_id=50,
            reason="需要修改"
        )
        
        self.assertEqual(result["order_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.engine_mock.withdraw.assert_called_once_with(
            instance_id=201, user_id=50
        )

    def test_withdraw_approval_order_not_found(self):
        """测试撤回不存在的订单"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=999, user_id=50)
        
        self.assertEqual(str(context.exception), "验收单不存在")

    def test_withdraw_approval_no_pending_instance(self):
        """测试撤回没有进行中的审批"""
        order = AcceptanceOrder(id=1, order_no="ACC-001")
        
        # Mock两次查询
        order_query_mock = MagicMock()
        order_query_mock.filter.return_value.first.return_value = order
        
        instance_query_mock = MagicMock()
        instance_query_mock.filter.return_value.first.return_value = None
        
        self.db_mock.query.side_effect = [order_query_mock, instance_query_mock]
        
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(order_id=1, user_id=50)
        
        self.assertEqual(str(context.exception), "没有进行中的审批流程可撤回")

    def test_withdraw_approval_permission_denied(self):
        """测试撤回他人的审批（无权限）"""
        order = AcceptanceOrder(id=1, order_no="ACC-001")
        
        instance = ApprovalInstance(
            id=201,
            entity_type="ACCEPTANCE_ORDER",
            entity_id=1,
            status="PENDING",
            initiator_id=50  # 发起人是50
        )
        
        # Mock两次查询
        order_query_mock = MagicMock()
        order_query_mock.filter.return_value.first.return_value = order
        
        instance_query_mock = MagicMock()
        instance_query_mock.filter.return_value.first.return_value = instance
        
        self.db_mock.query.side_effect = [order_query_mock, instance_query_mock]
        
        with self.assertRaises(PermissionError) as context:
            self.service.withdraw_approval(order_id=1, user_id=99)  # 用户99尝试撤回
        
        self.assertEqual(str(context.exception), "只能撤回自己提交的审批")

    # ==================== get_approval_history 测试 ====================

    def test_get_approval_history_basic(self):
        """测试获取审批历史基本功能"""
        # 创建审批任务
        task = ApprovalTask(
            id=301,
            assignee_id=50,
            status="APPROVED",
            action="approve",
            comment="同意",
            completed_at=datetime(2024, 1, 15, 11, 0, 0)
        )
        task.instance = ApprovalInstance(entity_type="ACCEPTANCE_ORDER", entity_id=1)
        
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", acceptance_type="FAT",
            overall_result="PASSED"
        )
        
        # Mock查询
        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 1
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [task]
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        
        items, total = self.service.get_approval_history(user_id=50)
        
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], 301)
        self.assertEqual(items[0]["order_no"], "ACC-001")

    def test_get_approval_history_with_status_filter(self):
        """测试按状态筛选审批历史"""
        query_mock = self.db_mock.query.return_value.join.return_value.filter.return_value
        
        self.service.get_approval_history(
            user_id=50,
            status_filter="APPROVED"
        )
        
        # 验证调用了filter（虽然不能直接验证filter参数，但可以确认被调用）
        self.assertTrue(query_mock.filter.called)

    def test_get_approval_history_with_type_filter(self):
        """测试按验收类型筛选审批历史"""
        task1 = ApprovalTask(id=301, status="APPROVED", action="approve")
        task1.instance = ApprovalInstance(entity_type="ACCEPTANCE_ORDER", entity_id=1)
        task1.completed_at = datetime.now()
        
        task2 = ApprovalTask(id=302, status="APPROVED", action="approve")
        task2.instance = ApprovalInstance(entity_type="ACCEPTANCE_ORDER", entity_id=2)
        task2.completed_at = datetime.now()
        
        order1 = AcceptanceOrder(id=1, order_no="ACC-001", acceptance_type="FAT", overall_result="PASSED")
        order2 = AcceptanceOrder(id=2, order_no="ACC-002", acceptance_type="SAT", overall_result="PASSED")
        
        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 2
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [task1, task2]
        
        # Mock订单查询
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [order1, order2]
        
        items, total = self.service.get_approval_history(
            user_id=50,
            acceptance_type="FAT"
        )
        
        # 因为类型筛选是在获取订单后进行的，所以items可能少于total
        # 这里只有order1符合FAT类型
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["acceptance_type"], "FAT")

    def test_get_approval_history_pagination(self):
        """测试审批历史分页"""
        tasks = []
        for i in range(5):
            task = ApprovalTask(
                id=300 + i,
                status="APPROVED",
                action="approve",
                completed_at=datetime.now()
            )
            task.instance = ApprovalInstance(entity_type="ACCEPTANCE_ORDER", entity_id=i)
            tasks.append(task)
        
        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 5
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = tasks[2:4]
        
        # Mock订单
        orders = [
            AcceptanceOrder(id=i, order_no=f"ACC-{i:03d}", acceptance_type="FAT", overall_result="PASSED")
            for i in range(2, 4)
        ]
        self.db_mock.query.return_value.filter.return_value.first.side_effect = orders
        
        items, total = self.service.get_approval_history(
            user_id=50,
            offset=2,
            limit=2
        )
        
        self.assertEqual(total, 5)
        self.assertEqual(len(items), 2)

    def test_get_approval_history_empty(self):
        """测试无审批历史"""
        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 0
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        items, total = self.service.get_approval_history(user_id=50)
        
        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)

    def test_get_approval_history_result_name_mapping(self):
        """测试审批历史结果名称映射"""
        task = ApprovalTask(id=301, status="REJECTED", action="reject", comment="不合格")
        task.instance = ApprovalInstance(entity_type="ACCEPTANCE_ORDER", entity_id=1)
        task.completed_at = datetime(2024, 1, 15, 11, 0, 0)
        
        order = AcceptanceOrder(
            id=1, order_no="ACC-001", acceptance_type="FINAL",
            overall_result="FAILED"
        )
        
        query_mock = self.db_mock.query.return_value
        query_mock.join.return_value.filter.return_value.count.return_value = 1
        query_mock.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [task]
        self.db_mock.query.return_value.filter.return_value.first.return_value = order
        
        items, total = self.service.get_approval_history(user_id=50)
        
        self.assertEqual(items[0]["acceptance_type_name"], "终验收")
        self.assertEqual(items[0]["result_name"], "不合格")


if __name__ == "__main__":
    unittest.main()

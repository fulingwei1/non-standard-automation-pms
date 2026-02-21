# -*- coding: utf-8 -*-
"""
报价审批服务增强单元测试

测试 QuoteApprovalService 的所有核心业务逻辑，目标覆盖率70%+。
使用真实的数据对象，只mock外部依赖（数据库、审批引擎）。
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.quote_approval import QuoteApprovalService


class TestQuoteApprovalService(unittest.TestCase):
    """报价审批服务增强测试类"""

    def setUp(self):
        """测试前准备"""
        self.db_mock = MagicMock()
        self.service = QuoteApprovalService(self.db_mock)

    def tearDown(self):
        """测试后清理"""
        self.db_mock.reset_mock()

    # ==================== 辅助方法 ====================

    def _create_quote_mock(
        self,
        quote_id=1,
        quote_code="Q2024001",
        status="DRAFT",
        customer_id=100,
        customer_name="测试客户",
    ):
        """创建报价Mock对象"""
        quote_mock = MagicMock()
        quote_mock.id = quote_id
        quote_mock.quote_code = quote_code
        quote_mock.status = status
        quote_mock.customer_id = customer_id

        customer_mock = MagicMock()
        customer_mock.name = customer_name
        quote_mock.customer = customer_mock

        return quote_mock

    def _create_version_mock(
        self,
        version_id=1,
        quote_id=1,
        version_no="V1.0",
        total_price=10000.0,
        cost_total=8000.0,
        gross_margin=0.2,
        lead_time_days=30,
    ):
        """创建报价版本Mock对象"""
        version_mock = MagicMock()
        version_mock.id = version_id
        version_mock.quote_id = quote_id
        version_mock.version_no = version_no
        version_mock.total_price = Decimal(str(total_price))
        version_mock.cost_total = Decimal(str(cost_total))
        version_mock.gross_margin = Decimal(str(gross_margin))
        version_mock.lead_time_days = lead_time_days
        return version_mock

    def _create_approval_instance_mock(
        self, instance_id=10, entity_id=1, status="PENDING", urgency="NORMAL"
    ):
        """创建审批实例Mock对象"""
        instance_mock = MagicMock()
        instance_mock.id = instance_id
        instance_mock.entity_type = "QUOTE"
        instance_mock.entity_id = entity_id
        instance_mock.status = status
        instance_mock.urgency = urgency
        instance_mock.created_at = datetime(2024, 1, 1, 10, 0, 0)
        instance_mock.completed_at = None

        initiator_mock = MagicMock()
        initiator_mock.real_name = "张三"
        instance_mock.initiator = initiator_mock
        instance_mock.initiator_id = 1

        return instance_mock

    def _create_approval_task_mock(self, task_id=1, instance_id=10, status="PENDING"):
        """创建审批任务Mock对象"""
        task_mock = MagicMock()
        task_mock.id = task_id
        task_mock.instance_id = instance_id
        task_mock.status = status
        task_mock.action = None
        task_mock.comment = None
        task_mock.completed_at = None
        task_mock.created_at = datetime(2024, 1, 1, 10, 0, 0)

        node_mock = MagicMock()
        node_mock.node_name = "审批节点1"
        task_mock.node = node_mock

        assignee_mock = MagicMock()
        assignee_mock.real_name = "李四"
        task_mock.assignee = assignee_mock
        task_mock.assignee_id = 2

        instance_mock = self._create_approval_instance_mock(instance_id)
        task_mock.instance = instance_mock

        return task_mock

    # ==================== submit_quotes_for_approval 测试用例 ====================

    def test_submit_single_quote_success(self):
        """测试成功提交单个报价审批"""
        # 准备数据
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        # 模拟数据库查询
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        # 模拟审批引擎
        instance_mock = self._create_approval_instance_mock()
        self.service.approval_engine.submit = MagicMock(return_value=instance_mock)

        # 执行测试
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1, urgency="NORMAL"
        )

        # 验证结果
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["quote_id"], 1)
        self.assertEqual(result["success"][0]["quote_code"], "Q2024001")
        self.assertEqual(result["success"][0]["instance_id"], 10)
        self.assertEqual(result["success"][0]["status"], "submitted")

        # 验证审批引擎被正确调用
        self.service.approval_engine.submit.assert_called_once()
        call_args = self.service.approval_engine.submit.call_args
        self.assertEqual(call_args[1]["template_code"], "SALES_QUOTE_APPROVAL")
        self.assertEqual(call_args[1]["entity_type"], "QUOTE")
        self.assertEqual(call_args[1]["entity_id"], 1)

    def test_submit_multiple_quotes_success(self):
        """测试成功提交多个报价审批"""
        # 准备数据 - 两个报价
        quote1 = self._create_quote_mock(1, "Q2024001", "DRAFT")
        quote2 = self._create_quote_mock(2, "Q2024002", "DRAFT")
        version1 = self._create_version_mock(1, 1)
        version2 = self._create_version_mock(2, 2)
        quote1.current_version = version1
        quote2.current_version = version2

        # 模拟数据库查询返回不同的报价
        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [quote1, quote2]

        # 模拟审批引擎
        instance1 = self._create_approval_instance_mock(10, 1)
        instance2 = self._create_approval_instance_mock(11, 2)
        self.service.approval_engine.submit = MagicMock(
            side_effect=[instance1, instance2]
        )

        # 执行测试
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1, 2], initiator_id=1
        )

        # 验证结果
        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["quote_id"], 1)
        self.assertEqual(result["success"][1]["quote_id"], 2)

    def test_submit_quote_not_found(self):
        """测试提交审批时报价不存在"""
        # 模拟报价不存在
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = self.service.submit_quotes_for_approval(
            quote_ids=[999], initiator_id=1
        )

        # 验证结果
        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["quote_id"], 999)
        self.assertEqual(result["errors"][0]["error"], "报价不存在")

    def test_submit_quote_invalid_status_approved(self):
        """测试提交审批时状态为已审批"""
        quote_mock = self._create_quote_mock(status="APPROVED")
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_submit_quote_invalid_status_pending(self):
        """测试提交审批时状态为审批中"""
        quote_mock = self._create_quote_mock(status="PENDING")
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_submit_quote_with_rejected_status(self):
        """测试提交被驳回的报价审批"""
        quote_mock = self._create_quote_mock(status="REJECTED")
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        instance_mock = self._create_approval_instance_mock()
        self.service.approval_engine.submit = MagicMock(return_value=instance_mock)

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1
        )

        # REJECTED状态允许提交
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)

    def test_submit_quote_no_version(self):
        """测试提交审批时报价没有版本"""
        quote_mock = self._create_quote_mock()
        quote_mock.current_version = None

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )
        # 模拟查询版本也返回None
        self.db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["error"], "报价没有版本，无法提交审批")

    def test_submit_quote_with_specific_version_ids(self):
        """测试使用指定版本ID提交审批"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock(version_id=5, version_no="V2.0")

        # 模拟查询报价
        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value

        # 第一次调用返回报价，第二次返回版本
        filter_mock.first.side_effect = [quote_mock, version_mock]

        instance_mock = self._create_approval_instance_mock()
        self.service.approval_engine.submit = MagicMock(return_value=instance_mock)

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1, version_ids=[5]
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(result["success"][0]["version_no"], "V2.0")

    def test_submit_quote_with_urgency_urgent(self):
        """测试提交紧急审批"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        instance_mock = self._create_approval_instance_mock(urgency="URGENT")
        self.service.approval_engine.submit = MagicMock(return_value=instance_mock)

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1, urgency="URGENT"
        )

        # 验证紧急程度被正确传递
        call_args = self.service.approval_engine.submit.call_args
        self.assertEqual(call_args[1]["urgency"], "URGENT")

    def test_submit_quote_with_comment(self):
        """测试提交审批时附加备注"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        instance_mock = self._create_approval_instance_mock()
        self.service.approval_engine.submit = MagicMock(return_value=instance_mock)

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1, comment="请尽快审批"
        )

        self.assertEqual(len(result["success"]), 1)

    def test_submit_quote_approval_engine_exception(self):
        """测试审批引擎提交时发生异常"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        # 模拟审批引擎抛出异常
        self.service.approval_engine.submit = MagicMock(
            side_effect=Exception("审批引擎错误")
        )

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1], initiator_id=1
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("审批引擎错误", result["errors"][0]["error"])

    # ==================== get_pending_tasks 测试用例 ====================

    def test_get_pending_tasks_success(self):
        """测试成功获取待审批任务"""
        task_mock = self._create_approval_task_mock()
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        # 模拟审批引擎返回任务
        self.service.approval_engine.get_pending_tasks = MagicMock(
            return_value=[task_mock]
        )
        # 模拟数据库查询返回报价
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        result = self.service.get_pending_tasks(user_id=1)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["quote_code"], "Q2024001")

    def test_get_pending_tasks_empty(self):
        """测试获取待审批任务为空"""
        self.service.approval_engine.get_pending_tasks = MagicMock(return_value=[])

        result = self.service.get_pending_tasks(user_id=1)

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_pending_tasks_with_customer_filter(self):
        """测试按客户ID筛选待审批任务"""
        task1 = self._create_approval_task_mock(1, 10)
        task2 = self._create_approval_task_mock(2, 11)

        quote1 = self._create_quote_mock(1, "Q2024001", customer_id=100)
        quote2 = self._create_quote_mock(2, "Q2024002", customer_id=200)

        version1 = self._create_version_mock(1, 1)
        quote1.current_version = version1
        quote2.current_version = version1

        self.service.approval_engine.get_pending_tasks = MagicMock(
            return_value=[task1, task2]
        )

        # 模拟数据库查询返回不同的报价
        # 需要返回3次：第一次筛选时2次，最后展示时1次
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            quote1,
            quote2,
            quote1,  # 展示时再次查询quote1
        ]

        # 按客户ID 100筛选
        result = self.service.get_pending_tasks(user_id=1, customer_id=100)

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["quote_id"], 1)

    def test_get_pending_tasks_pagination(self):
        """测试待审批任务分页"""
        tasks = [self._create_approval_task_mock(i, 10 + i) for i in range(1, 6)]
        quotes = [self._create_quote_mock(i, f"Q202400{i}") for i in range(1, 6)]
        version = self._create_version_mock()

        for quote in quotes:
            quote.current_version = version

        self.service.approval_engine.get_pending_tasks = MagicMock(return_value=tasks)
        self.db_mock.query.return_value.filter.return_value.first.side_effect = quotes

        # 第一页，每页2条
        result = self.service.get_pending_tasks(user_id=1, offset=0, limit=2)

        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][1]["task_id"], 2)

    def test_get_pending_tasks_without_version(self):
        """测试获取没有版本的待审批任务"""
        task_mock = self._create_approval_task_mock()
        quote_mock = self._create_quote_mock()
        quote_mock.current_version = None

        self.service.approval_engine.get_pending_tasks = MagicMock(
            return_value=[task_mock]
        )
        # 第一次返回报价
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )
        # 模拟查询最新版本时也返回None
        self.db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        result = self.service.get_pending_tasks(user_id=1)

        self.assertEqual(result["total"], 1)
        self.assertIsNone(result["items"][0]["version_no"])
        self.assertEqual(result["items"][0]["total_price"], 0)

    # ==================== perform_action 测试用例 ====================

    def test_perform_action_approve(self):
        """测试执行审批通过操作"""
        result_mock = MagicMock()
        result_mock.status = "APPROVED"
        self.service.approval_engine.approve = MagicMock(return_value=result_mock)

        result = self.service.perform_action(
            task_id=1, action="approve", approver_id=2, comment="同意"
        )

        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service.approval_engine.approve.assert_called_once_with(
            task_id=1, approver_id=2, comment="同意"
        )

    def test_perform_action_reject(self):
        """测试执行审批驳回操作"""
        result_mock = MagicMock()
        result_mock.status = "REJECTED"
        self.service.approval_engine.reject = MagicMock(return_value=result_mock)

        result = self.service.perform_action(
            task_id=1, action="reject", approver_id=2, comment="价格太高"
        )

        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.service.approval_engine.reject.assert_called_once_with(
            task_id=1, approver_id=2, comment="价格太高"
        )

    def test_perform_action_invalid_action(self):
        """测试执行不支持的操作类型"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_action(
                task_id=1, action="cancel", approver_id=2
            )

        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_action_without_comment(self):
        """测试执行审批操作时不附加意见"""
        result_mock = MagicMock()
        result_mock.status = "APPROVED"
        self.service.approval_engine.approve = MagicMock(return_value=result_mock)

        result = self.service.perform_action(
            task_id=1, action="approve", approver_id=2
        )

        self.assertEqual(result["action"], "approve")
        call_args = self.service.approval_engine.approve.call_args
        self.assertIsNone(call_args[1]["comment"])

    # ==================== perform_batch_actions 测试用例 ====================

    def test_perform_batch_actions_approve_success(self):
        """测试批量审批通过成功"""
        self.service.approval_engine.approve = MagicMock()

        result = self.service.perform_batch_actions(
            task_ids=[1, 2, 3], action="approve", approver_id=2
        )

        self.assertEqual(len(result["success"]), 3)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.approval_engine.approve.call_count, 3)

    def test_perform_batch_actions_reject_success(self):
        """测试批量驳回成功"""
        self.service.approval_engine.reject = MagicMock()

        result = self.service.perform_batch_actions(
            task_ids=[1, 2], action="reject", approver_id=2, comment="批量驳回"
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 0)

    def test_perform_batch_actions_partial_failure(self):
        """测试批量审批部分失败"""
        # 第一个成功，第二个失败
        self.service.approval_engine.approve = MagicMock(
            side_effect=[None, Exception("任务不存在"), None]
        )

        result = self.service.perform_batch_actions(
            task_ids=[1, 2, 3], action="approve", approver_id=2
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["task_id"], 2)

    def test_perform_batch_actions_invalid_action(self):
        """测试批量执行不支持的操作"""
        result = self.service.perform_batch_actions(
            task_ids=[1, 2], action="invalid", approver_id=2
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 2)
        self.assertIn("不支持的操作", result["errors"][0]["error"])

    # ==================== get_quote_approval_status 测试用例 ====================

    def test_get_quote_approval_status_with_instance(self):
        """测试获取有审批实例的报价审批状态"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        instance_mock = self._create_approval_instance_mock()
        task_mock = self._create_approval_task_mock()
        task_mock.status = "APPROVED"
        task_mock.action = "approve"
        task_mock.comment = "同意"
        task_mock.completed_at = datetime(2024, 1, 1, 11, 0, 0)

        # 模拟数据库查询
        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value

        # 第一次返回报价，第二次返回实例
        filter_mock.first.side_effect = [quote_mock, instance_mock]
        filter_mock.order_by.return_value.first.return_value = instance_mock
        filter_mock.order_by.return_value.all.return_value = [task_mock]

        result = self.service.get_quote_approval_status(quote_id=1)

        self.assertIsNotNone(result)
        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["instance_id"], 10)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)
        self.assertIsNotNone(result["version_info"])

    def test_get_quote_approval_status_without_instance(self):
        """测试获取没有审批实例的报价审批状态"""
        quote_mock = self._create_quote_mock()

        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value

        # 第一次返回报价，第二次返回None（没有实例）
        filter_mock.first.side_effect = [quote_mock, None]
        filter_mock.order_by.return_value.first.return_value = None

        result = self.service.get_quote_approval_status(quote_id=1)

        self.assertIsNotNone(result)
        self.assertEqual(result["quote_id"], 1)
        self.assertIsNone(result["approval_instance"])
        self.assertEqual(result["status"], "DRAFT")

    def test_get_quote_approval_status_quote_not_found(self):
        """测试获取不存在报价的审批状态"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_quote_approval_status(quote_id=999)

        self.assertIsNone(result)

    def test_get_quote_approval_status_without_version(self):
        """测试获取没有版本的报价审批状态"""
        quote_mock = self._create_quote_mock()
        quote_mock.current_version = None

        instance_mock = self._create_approval_instance_mock()

        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [quote_mock, instance_mock]
        filter_mock.order_by.return_value.first.return_value = instance_mock
        filter_mock.order_by.return_value.all.return_value = []

        result = self.service.get_quote_approval_status(quote_id=1)

        self.assertIsNone(result["version_info"])

    # ==================== withdraw_approval 测试用例 ====================

    def test_withdraw_approval_success(self):
        """测试成功撤回审批"""
        quote_mock = self._create_quote_mock()
        instance_mock = self._create_approval_instance_mock()

        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value

        # 第一次返回报价，第二次返回实例
        filter_mock.first.side_effect = [quote_mock, instance_mock]

        self.service.approval_engine.withdraw = MagicMock()

        result = self.service.withdraw_approval(quote_id=1, user_id=1)

        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.service.approval_engine.withdraw.assert_called_once_with(
            instance_id=10, user_id=1
        )

    def test_withdraw_approval_quote_not_found(self):
        """测试撤回审批时报价不存在"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=999, user_id=1)

        self.assertIn("报价不存在", str(context.exception))

    def test_withdraw_approval_no_pending_instance(self):
        """测试撤回审批时没有进行中的审批"""
        quote_mock = self._create_quote_mock()

        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [quote_mock, None]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=1, user_id=1)

        self.assertIn("没有进行中的审批流程可撤回", str(context.exception))

    def test_withdraw_approval_not_initiator(self):
        """测试撤回审批时不是发起人"""
        quote_mock = self._create_quote_mock()
        instance_mock = self._create_approval_instance_mock()
        instance_mock.initiator_id = 1

        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [quote_mock, instance_mock]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=1, user_id=2)  # 不同的用户ID

        self.assertIn("只能撤回自己提交的审批", str(context.exception))

    # ==================== get_approval_history 测试用例 ====================

    def test_get_approval_history_success(self):
        """测试成功获取审批历史"""
        task1 = self._create_approval_task_mock(1, 10, "APPROVED")
        task1.action = "approve"
        task1.comment = "同意"
        task1.completed_at = datetime(2024, 1, 1, 11, 0, 0)

        quote_mock = self._create_quote_mock()

        # 模拟数据库查询
        query_mock = self.db_mock.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            task1
        ]

        # 模拟查询报价
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        result = self.service.get_approval_history(user_id=2)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["action"], "approve")

    def test_get_approval_history_with_status_filter(self):
        """测试按状态筛选审批历史"""
        query_mock = self.db_mock.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        # 当有 status_filter 时，会再次调用 filter()
        filter_mock_2 = filter_mock.filter.return_value
        filter_mock_2.count.return_value = 0
        filter_mock_2.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        result = self.service.get_approval_history(
            user_id=2, status_filter="APPROVED"
        )

        self.assertEqual(result["total"], 0)

    def test_get_approval_history_pagination(self):
        """测试审批历史分页"""
        tasks = [
            self._create_approval_task_mock(i, 10 + i, "APPROVED") for i in range(1, 6)
        ]
        for task in tasks:
            task.completed_at = datetime(2024, 1, 1, 11, 0, 0)

        quote_mock = self._create_quote_mock()

        query_mock = self.db_mock.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.count.return_value = 5
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            tasks[0:2]
        )

        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            quote_mock,
            quote_mock,
        ]

        result = self.service.get_approval_history(user_id=2, offset=0, limit=2)

        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["items"]), 2)

    # ==================== 私有方法测试用例 ====================

    def test_get_quote_version_from_version_ids(self):
        """测试从版本ID列表获取版本"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock(5, 1, "V2.0")

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            version_mock
        )

        version = self.service._get_quote_version(quote_mock, version_ids=[5], index=0)

        self.assertIsNotNone(version)
        self.assertEqual(version.id, 5)

    def test_get_quote_version_from_current_version(self):
        """测试从当前版本获取"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        # 模拟查询返回None（版本ID列表中找不到）
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        version = self.service._get_quote_version(quote_mock, version_ids=[999], index=0)

        self.assertIsNotNone(version)
        self.assertEqual(version.id, 1)

    def test_get_quote_version_from_latest(self):
        """测试从最新版本获取"""
        quote_mock = self._create_quote_mock()
        quote_mock.current_version = None
        version_mock = self._create_version_mock()

        # 第一次查询返回None，第二次查询最新版本返回版本
        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = None
        filter_mock.order_by.return_value.first.return_value = version_mock

        version = self.service._get_quote_version(quote_mock, version_ids=None, index=0)

        self.assertIsNotNone(version)
        self.assertEqual(version.id, 1)

    def test_get_current_version_from_current(self):
        """测试获取当前版本 - 从current_version"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()
        quote_mock.current_version = version_mock

        version = self.service._get_current_version(quote_mock)

        self.assertIsNotNone(version)
        self.assertEqual(version.id, 1)

    def test_get_current_version_from_latest(self):
        """测试获取当前版本 - 从最新版本"""
        quote_mock = self._create_quote_mock()
        quote_mock.current_version = None
        version_mock = self._create_version_mock()

        self.db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            version_mock
        )

        version = self.service._get_current_version(quote_mock)

        self.assertIsNotNone(version)
        self.assertEqual(version.id, 1)

    def test_get_current_version_quote_none(self):
        """测试获取当前版本 - 报价为None"""
        version = self.service._get_current_version(None)

        self.assertIsNone(version)

    def test_build_form_data(self):
        """测试构建审批表单数据"""
        quote_mock = self._create_quote_mock()
        version_mock = self._create_version_mock()

        form_data = self.service._build_form_data(quote_mock, version_mock)

        self.assertEqual(form_data["quote_id"], 1)
        self.assertEqual(form_data["quote_code"], "Q2024001")
        self.assertEqual(form_data["version_id"], 1)
        self.assertEqual(form_data["version_no"], "V1.0")
        self.assertEqual(form_data["total_price"], 10000.0)
        self.assertEqual(form_data["cost_total"], 8000.0)
        self.assertEqual(form_data["gross_margin"], 0.2)
        self.assertEqual(form_data["customer_id"], 100)
        self.assertEqual(form_data["customer_name"], "测试客户")
        self.assertEqual(form_data["lead_time_days"], 30)

    def test_build_form_data_with_none_values(self):
        """测试构建审批表单数据 - 包含None值"""
        quote_mock = self._create_quote_mock()
        quote_mock.customer = None

        version_mock = self._create_version_mock()
        version_mock.total_price = None
        version_mock.cost_total = None
        version_mock.gross_margin = None

        form_data = self.service._build_form_data(quote_mock, version_mock)

        self.assertEqual(form_data["total_price"], 0)
        self.assertEqual(form_data["cost_total"], 0)
        self.assertEqual(form_data["gross_margin"], 0)
        self.assertIsNone(form_data["customer_name"])


if __name__ == "__main__":
    unittest.main()

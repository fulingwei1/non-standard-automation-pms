# -*- coding: utf-8 -*-
"""
报价审批服务单元测试

测试 QuoteApprovalService 的核心业务逻辑。
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.quote_approval import QuoteApprovalService


class TestQuoteApprovalService(unittest.TestCase):
    """报价审批服务测试类"""

    def setUp(self):
        """测试前准备"""
        self.db_mock = MagicMock()
        self.service = QuoteApprovalService(self.db_mock)

    def tearDown(self):
        """测试后清理"""
        self.db_mock.reset_mock()

    def test_submit_quotes_for_approval_success(self):
        """测试成功提交报价审批"""
        # 准备测试数据
        quote_mock = MagicMock()
        quote_mock.id = 1
        quote_mock.quote_code = "Q2024001"
        quote_mock.status = "DRAFT"
        quote_mock.customer_id = 100
        quote_mock.customer.name = "测试客户"

        version_mock = MagicMock()
        version_mock.id = 1
        version_mock.version_no = "V1.0"
        version_mock.total_price = 10000.0
        version_mock.cost_total = 8000.0
        version_mock.gross_margin = 0.2
        version_mock.lead_time_days = 30

        quote_mock.current_version = version_mock

        # 模拟数据库查询
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        # 模拟审批引擎
        instance_mock = MagicMock()
        instance_mock.id = 10
        self.service.approval_engine.submit = MagicMock(return_value=instance_mock)

        # 执行测试
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=1,
            urgency="NORMAL",
        )

        # 验证结果
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["quote_id"], 1)
        self.assertEqual(result["success"][0]["instance_id"], 10)

    def test_submit_quotes_for_approval_invalid_status(self):
        """测试提交审批时状态不允许"""
        # 准备测试数据 - 状态为已审批
        quote_mock = MagicMock()
        quote_mock.id = 1
        quote_mock.status = "APPROVED"

        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        # 执行测试
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=1,
        )

        # 验证结果
        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_submit_quotes_for_approval_quote_not_found(self):
        """测试提交审批时报价不存在"""
        # 模拟报价不存在
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = self.service.submit_quotes_for_approval(
            quote_ids=[999],
            initiator_id=1,
        )

        # 验证结果
        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["error"], "报价不存在")

    def test_get_pending_tasks_success(self):
        """测试获取待审批任务成功"""
        # 准备测试数据
        task_mock = MagicMock()
        task_mock.id = 1
        task_mock.node.node_name = "审批节点1"

        instance_mock = MagicMock()
        instance_mock.id = 10
        instance_mock.entity_id = 1
        instance_mock.created_at = datetime(2024, 1, 1, 10, 0, 0)
        instance_mock.urgency = "NORMAL"
        instance_mock.initiator.real_name = "张三"

        task_mock.instance = instance_mock

        quote_mock = MagicMock()
        quote_mock.id = 1
        quote_mock.quote_code = "Q2024001"
        quote_mock.customer.name = "测试客户"

        version_mock = MagicMock()
        version_mock.version_no = "V1.0"
        version_mock.total_price = 10000.0
        version_mock.gross_margin = 0.2
        version_mock.lead_time_days = 30

        quote_mock.current_version = version_mock

        # 模拟审批引擎和数据库查询
        self.service.approval_engine.get_pending_tasks = MagicMock(
            return_value=[task_mock]
        )
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        # 执行测试
        result = self.service.get_pending_tasks(user_id=1, offset=0, limit=20)

        # 验证结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["quote_code"], "Q2024001")

    def test_perform_action_approve_success(self):
        """测试审批通过操作成功"""
        # 准备测试数据
        result_mock = MagicMock()
        result_mock.status = "APPROVED"

        self.service.approval_engine.approve = MagicMock(return_value=result_mock)

        # 执行测试
        result = self.service.perform_action(
            task_id=1,
            action="approve",
            approver_id=1,
            comment="同意",
        )

        # 验证结果
        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service.approval_engine.approve.assert_called_once()

    def test_perform_action_reject_success(self):
        """测试审批驳回操作成功"""
        # 准备测试数据
        result_mock = MagicMock()
        result_mock.status = "REJECTED"

        self.service.approval_engine.reject = MagicMock(return_value=result_mock)

        # 执行测试
        result = self.service.perform_action(
            task_id=1,
            action="reject",
            approver_id=1,
            comment="不同意",
        )

        # 验证结果
        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.service.approval_engine.reject.assert_called_once()

    def test_perform_action_invalid_action(self):
        """测试不支持的审批操作"""
        # 执行测试并验证异常
        with self.assertRaises(ValueError) as context:
            self.service.perform_action(
                task_id=1,
                action="invalid_action",
                approver_id=1,
            )

        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_batch_actions_success(self):
        """测试批量审批操作成功"""
        # 模拟审批引擎
        self.service.approval_engine.approve = MagicMock()

        # 执行测试
        result = self.service.perform_batch_actions(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=1,
            comment="批量同意",
        )

        # 验证结果
        self.assertEqual(len(result["success"]), 3)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.approval_engine.approve.call_count, 3)

    def test_get_quote_approval_status_not_found(self):
        """测试查询不存在的报价审批状态"""
        # 模拟报价不存在
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = self.service.get_quote_approval_status(quote_id=999)

        # 验证结果
        self.assertIsNone(result)

    def test_get_quote_approval_status_no_instance(self):
        """测试查询无审批实例的报价状态"""
        # 准备测试数据
        quote_mock = MagicMock()
        quote_mock.id = 1
        quote_mock.quote_code = "Q2024001"
        quote_mock.status = "DRAFT"

        # 第一次查询返回报价，第二次查询返回None（无审批实例）
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            quote_mock,
            None,
        ]

        # 执行测试
        result = self.service.get_quote_approval_status(quote_id=1)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result["quote_id"], 1)
        self.assertIsNone(result["approval_instance"])

    def test_withdraw_approval_success(self):
        """测试撤回审批成功"""
        # 准备测试数据
        quote_mock = MagicMock()
        quote_mock.id = 1
        quote_mock.quote_code = "Q2024001"

        instance_mock = MagicMock()
        instance_mock.id = 10
        instance_mock.initiator_id = 1
        instance_mock.status = "PENDING"

        # 第一次查询返回报价，第二次查询返回审批实例
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            quote_mock,
            instance_mock,
        ]

        self.service.approval_engine.withdraw = MagicMock()

        # 执行测试
        result = self.service.withdraw_approval(quote_id=1, user_id=1)

        # 验证结果
        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["status"], "withdrawn")
        self.service.approval_engine.withdraw.assert_called_once()

    def test_withdraw_approval_permission_denied(self):
        """测试撤回审批权限不足"""
        # 准备测试数据
        quote_mock = MagicMock()
        quote_mock.id = 1

        instance_mock = MagicMock()
        instance_mock.initiator_id = 2  # 不同的发起人
        instance_mock.status = "PENDING"

        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            quote_mock,
            instance_mock,
        ]

        # 执行测试并验证异常
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=1, user_id=1)

        self.assertIn("只能撤回自己提交的审批", str(context.exception))

    def test_get_approval_history_success(self):
        """测试获取审批历史成功"""
        # 准备测试数据
        task_mock = MagicMock()
        task_mock.id = 1
        task_mock.action = "approve"
        task_mock.status = "APPROVED"
        task_mock.comment = "同意"
        task_mock.completed_at = datetime(2024, 1, 1, 12, 0, 0)

        instance_mock = MagicMock()
        instance_mock.entity_id = 1

        task_mock.instance = instance_mock

        quote_mock = MagicMock()
        quote_mock.quote_code = "Q2024001"
        quote_mock.customer.name = "测试客户"

        # 模拟查询
        query_mock = MagicMock()
        query_mock.count.return_value = 1
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            task_mock
        ]

        self.db_mock.query.return_value.join.return_value.filter.return_value = (
            query_mock
        )
        self.db_mock.query.return_value.filter.return_value.first.return_value = (
            quote_mock
        )

        # 执行测试
        result = self.service.get_approval_history(
            user_id=1, offset=0, limit=20
        )

        # 验证结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 1)
        self.assertEqual(result["items"][0]["status"], "APPROVED")

    def test_build_form_data(self):
        """测试构建审批表单数据"""
        # 准备测试数据
        quote_mock = MagicMock()
        quote_mock.id = 1
        quote_mock.quote_code = "Q2024001"
        quote_mock.customer_id = 100
        quote_mock.customer.name = "测试客户"

        version_mock = MagicMock()
        version_mock.id = 1
        version_mock.version_no = "V1.0"
        version_mock.total_price = 10000.0
        version_mock.cost_total = 8000.0
        version_mock.gross_margin = 0.2
        version_mock.lead_time_days = 30

        # 执行测试
        result = self.service._build_form_data(quote_mock, version_mock)

        # 验证结果
        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["quote_code"], "Q2024001")
        self.assertEqual(result["version_id"], 1)
        self.assertEqual(result["total_price"], 10000.0)
        self.assertEqual(result["customer_name"], "测试客户")


if __name__ == "__main__":
    unittest.main()

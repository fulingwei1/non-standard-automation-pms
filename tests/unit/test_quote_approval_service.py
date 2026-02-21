# -*- coding: utf-8 -*-
"""
报价审批服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime
from decimal import Decimal

from app.services.quote_approval.quote_approval_service import QuoteApprovalService


class TestQuoteApprovalServiceCore(unittest.TestCase):
    """测试核心审批服务方法"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(db=self.mock_db)

        # Mock approval_engine
        self.service.approval_engine = MagicMock()

    # ========== submit_quotes_for_approval() 测试 ==========

    def test_submit_quotes_success(self):
        """测试成功提交单个报价审批"""
        # 准备数据
        quote = self._create_mock_quote(
            id=1,
            quote_code="Q-2024-001",
            status="DRAFT",
            customer_id=100
        )
        version = self._create_mock_version(
            id=10,
            version_no="V1",
            quote_id=1,
            total_price=Decimal("10000.00"),
            cost_total=Decimal("7000.00"),
            gross_margin=Decimal("0.30"),
            lead_time_days=7
        )
        quote.current_version = version
        quote.customer = MagicMock()
        quote.customer.name = "测试客户"

        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = quote
        self.mock_db.query.return_value = mock_query

        # Mock approval engine submit
        mock_instance = MagicMock()
        mock_instance.id = 1001
        self.service.approval_engine.submit.return_value = mock_instance

        # 执行
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=50,
            urgency="HIGH",
        )

        # 验证
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["quote_id"], 1)
        self.assertEqual(result["success"][0]["quote_code"], "Q-2024-001")
        self.assertEqual(result["success"][0]["instance_id"], 1001)

        # 验证调用
        self.service.approval_engine.submit.assert_called_once()
        call_args = self.service.approval_engine.submit.call_args
        self.assertEqual(call_args[1]["template_code"], "SALES_QUOTE_APPROVAL")
        self.assertEqual(call_args[1]["entity_type"], "QUOTE")
        self.assertEqual(call_args[1]["entity_id"], 1)
        self.assertEqual(call_args[1]["initiator_id"], 50)
        self.assertEqual(call_args[1]["urgency"], "HIGH")

    def test_submit_quotes_not_found(self):
        """测试提交不存在的报价"""
        # Mock query返回None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        result = self.service.submit_quotes_for_approval(
            quote_ids=[999],
            initiator_id=50
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["quote_id"], 999)
        self.assertEqual(result["errors"][0]["error"], "报价不存在")

    def test_submit_quotes_invalid_status(self):
        """测试提交状态不允许的报价"""
        quote = self._create_mock_quote(id=1, status="APPROVED")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = quote
        self.mock_db.query.return_value = mock_query

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=50
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_submit_quotes_no_version(self):
        """测试提交没有版本的报价"""
        quote = self._create_mock_quote(id=1, status="DRAFT")
        quote.current_version = None

        # Mock Quote查询
        mock_quote_query = MagicMock()
        mock_quote_query.filter.return_value.first.return_value = quote

        # Mock QuoteVersion查询（返回None，表示没有版本）
        mock_version_query = MagicMock()
        mock_version_query.filter.return_value.order_by.return_value.first.return_value = None

        self.mock_db.query.side_effect = [mock_quote_query, mock_version_query]

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=50
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("没有版本", result["errors"][0]["error"])

    def test_submit_quotes_batch_mixed(self):
        """测试批量提交混合结果（部分成功部分失败）"""
        # Quote 1: 成功
        quote1 = self._create_mock_quote(id=1, quote_code="Q-001", status="DRAFT")
        version1 = self._create_mock_version(id=10, version_no="V1", quote_id=1)
        quote1.current_version = version1
        quote1.customer = MagicMock()
        quote1.customer.name = "客户A"

        # Quote 2: 不存在
        # Quote 3: 状态错误
        quote3 = self._create_mock_quote(id=3, status="APPROVED")

        # Mock每个quote的查询
        mock_query1 = MagicMock()
        mock_query1.filter.return_value.first.return_value = quote1

        mock_query2 = MagicMock()
        mock_query2.filter.return_value.first.return_value = None

        mock_query3 = MagicMock()
        mock_query3.filter.return_value.first.return_value = quote3

        self.mock_db.query.side_effect = [mock_query1, mock_query2, mock_query3]

        mock_instance = MagicMock(id=1001)
        self.service.approval_engine.submit.return_value = mock_instance

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1, 2, 3],
            initiator_id=50
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 2)
        self.assertEqual(result["success"][0]["quote_id"], 1)

    def test_submit_quotes_with_version_ids(self):
        """测试使用指定版本ID提交"""
        quote = self._create_mock_quote(id=1, status="DRAFT")
        specified_version = self._create_mock_version(id=15, version_no="V2", quote_id=1)
        quote.current_version = MagicMock(id=10, version_no="V1")
        quote.customer = MagicMock(name="客户")

        # Mock两次query调用: Quote + QuoteVersion
        def query_side_effect(model_class):
            mock_query = MagicMock()
            if model_class.__name__ == "Quote":
                mock_query.filter.return_value.first.return_value = quote
            elif model_class.__name__ == "QuoteVersion":
                mock_query.filter.return_value.first.return_value = specified_version
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        mock_instance = MagicMock(id=1001)
        self.service.approval_engine.submit.return_value = mock_instance

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=50,
            version_ids=[15]
        )

        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(result["success"][0]["version_no"], "V2")

    def test_submit_quotes_engine_exception(self):
        """测试审批引擎抛出异常"""
        quote = self._create_mock_quote(id=1, status="DRAFT")
        version = self._create_mock_version(id=10, quote_id=1)
        quote.current_version = version
        quote.customer = MagicMock(name="客户")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = quote
        self.mock_db.query.return_value = mock_query

        # Mock引擎抛出异常
        self.service.approval_engine.submit.side_effect = Exception("审批模板不存在")

        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=50
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("审批模板不存在", result["errors"][0]["error"])

    # ========== get_pending_tasks() 测试 ==========

    def test_get_pending_tasks_success(self):
        """测试获取待审批任务成功"""
        # 准备mock任务
        task1 = self._create_mock_task(
            task_id=201,
            quote_id=1,
            quote_code="Q-001",
            customer_name="客户A",
            version_no="V1",
            total_price=Decimal("10000"),
            gross_margin=Decimal("0.30")
        )
        task2 = self._create_mock_task(
            task_id=202,
            quote_id=2,
            quote_code="Q-002",
            customer_name="客户B"
        )

        self.service.approval_engine.get_pending_tasks.return_value = [task1, task2]

        # Mock quote查询
        def query_side_effect(model_class):
            mock_query = MagicMock()
            if task1.instance.entity_id == 1:
                quote1 = self._create_mock_quote(id=1, quote_code="Q-001")
                quote1.customer = MagicMock(name="客户A")
                quote1.current_version = self._create_mock_version(
                    version_no="V1",
                    total_price=Decimal("10000"),
                    gross_margin=Decimal("0.30"),
                    lead_time_days=7
                )
                mock_query.filter.return_value.first.side_effect = [quote1,
                    self._create_mock_quote(id=2, quote_code="Q-002")]
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_pending_tasks(user_id=50)

        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["task_id"], 201)
        self.assertEqual(result["items"][0]["quote_code"], "Q-001")

    def test_get_pending_tasks_with_customer_filter(self):
        """测试按客户筛选待审批任务"""
        task1 = self._create_mock_task(task_id=201, quote_id=1)
        task2 = self._create_mock_task(task_id=202, quote_id=2)

        self.service.approval_engine.get_pending_tasks.return_value = [task1, task2]

        # Quote 1: customer_id=100, Quote 2: customer_id=200
        quote1 = self._create_mock_quote(id=1, customer_id=100)
        quote1.customer = MagicMock()
        quote1.customer.name = "客户A"
        quote1.current_version = self._create_mock_version()
        
        quote2 = self._create_mock_quote(id=2, customer_id=200)
        quote2.customer = MagicMock()
        quote2.customer.name = "客户B"
        quote2.current_version = self._create_mock_version()

        # Mock quote查询：筛选时查2次，构建items时查1次
        mock_query = MagicMock()
        mock_query.filter.return_value.first.side_effect = [quote1, quote2, quote1]
        self.mock_db.query.return_value = mock_query

        result = self.service.get_pending_tasks(user_id=50, customer_id=100)

        # 应该只有quote1被筛选出来
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)

    def test_get_pending_tasks_pagination(self):
        """测试待审批任务分页"""
        tasks = [self._create_mock_task(task_id=i, quote_id=i) for i in range(1, 26)]
        self.service.approval_engine.get_pending_tasks.return_value = tasks

        # Mock所有quote查询
        def create_quote_mock(qid):
            quote = self._create_mock_quote(id=qid)
            quote.customer = MagicMock(name=f"客户{qid}")
            quote.current_version = self._create_mock_version()
            return quote

        mock_query = MagicMock()
        mock_query.filter.return_value.first.side_effect = [
            create_quote_mock(i) for i in range(1, 26)
        ]
        self.mock_db.query.return_value = mock_query

        # 测试第二页
        result = self.service.get_pending_tasks(user_id=50, offset=20, limit=10)

        self.assertEqual(result["total"], 25)
        self.assertEqual(len(result["items"]), 5)  # 只剩5条

    def test_get_pending_tasks_empty(self):
        """测试没有待审批任务"""
        self.service.approval_engine.get_pending_tasks.return_value = []

        result = self.service.get_pending_tasks(user_id=50)

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    # ========== perform_action() 测试 ==========

    def test_perform_action_approve(self):
        """测试批准操作"""
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        self.service.approval_engine.approve.return_value = mock_result

        result = self.service.perform_action(
            task_id=201,
            action="approve",
            approver_id=50,
            comment="同意"
        )

        self.assertEqual(result["task_id"], 201)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")

        self.service.approval_engine.approve.assert_called_once_with(
            task_id=201,
            approver_id=50,
            comment="同意"
        )

    def test_perform_action_reject(self):
        """测试拒绝操作"""
        mock_result = MagicMock()
        mock_result.status = "REJECTED"
        self.service.approval_engine.reject.return_value = mock_result

        result = self.service.perform_action(
            task_id=202,
            action="reject",
            approver_id=50,
            comment="不符合要求"
        )

        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")

        self.service.approval_engine.reject.assert_called_once_with(
            task_id=202,
            approver_id=50,
            comment="不符合要求"
        )

    def test_perform_action_invalid_action(self):
        """测试无效操作类型"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_action(
                task_id=201,
                action="invalid_action",
                approver_id=50
            )

        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_action_no_status_attr(self):
        """测试返回对象没有status属性"""
        mock_result = MagicMock(spec=[])  # 空spec，没有任何属性
        self.service.approval_engine.approve.return_value = mock_result

        result = self.service.perform_action(
            task_id=201,
            action="approve",
            approver_id=50
        )

        self.assertIsNone(result["instance_status"])

    # ========== perform_batch_actions() 测试 ==========

    def test_perform_batch_actions_approve(self):
        """测试批量批准"""
        self.service.approval_engine.approve.return_value = MagicMock()

        result = self.service.perform_batch_actions(
            task_ids=[201, 202, 203],
            action="approve",
            approver_id=50,
            comment="批量同意"
        )

        self.assertEqual(len(result["success"]), 3)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.approval_engine.approve.call_count, 3)

    def test_perform_batch_actions_reject(self):
        """测试批量拒绝"""
        self.service.approval_engine.reject.return_value = MagicMock()

        result = self.service.perform_batch_actions(
            task_ids=[201, 202],
            action="reject",
            approver_id=50
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(self.service.approval_engine.reject.call_count, 2)

    def test_perform_batch_actions_invalid_action(self):
        """测试批量执行无效操作"""
        result = self.service.perform_batch_actions(
            task_ids=[201, 202],
            action="invalid",
            approver_id=50
        )

        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 2)
        self.assertIn("不支持的操作", result["errors"][0]["error"])

    def test_perform_batch_actions_partial_failure(self):
        """测试批量操作部分失败"""
        # 第一个成功，第二个失败，第三个成功
        self.service.approval_engine.approve.side_effect = [
            MagicMock(),
            Exception("任务已完成"),
            MagicMock()
        ]

        result = self.service.perform_batch_actions(
            task_ids=[201, 202, 203],
            action="approve",
            approver_id=50
        )

        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["task_id"], 202)

    # ========== get_quote_approval_status() 测试 ==========

    def test_get_quote_approval_status_success(self):
        """测试查询审批状态成功"""
        quote = self._create_mock_quote(id=1, quote_code="Q-001", status="PENDING")
        quote.customer = MagicMock(name="客户A")
        version = self._create_mock_version(
            version_no="V1",
            total_price=Decimal("10000"),
            gross_margin=Decimal("0.30")
        )
        quote.current_version = version

        instance = MagicMock()
        instance.id = 1001
        instance.status = "PENDING"
        instance.urgency = "NORMAL"
        instance.created_at = datetime(2024, 1, 15, 10, 0, 0)
        instance.completed_at = None

        task1 = MagicMock()
        task1.id = 2001
        task1.node = MagicMock(node_name="销售主管审批")
        task1.assignee = MagicMock(real_name="张三")
        task1.status = "APPROVED"
        task1.action = "approve"
        task1.comment = "同意"
        task1.completed_at = datetime(2024, 1, 15, 11, 0, 0)

        # Mock query chain
        mock_quote_query = MagicMock()
        mock_quote_query.filter.return_value.first.return_value = quote

        mock_instance_query = MagicMock()
        mock_instance_query.filter.return_value.order_by.return_value.first.return_value = instance

        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.order_by.return_value.all.return_value = [task1]

        self.mock_db.query.side_effect = [
            mock_quote_query,
            mock_instance_query,
            mock_task_query
        ]

        result = self.service.get_quote_approval_status(quote_id=1)

        self.assertIsNotNone(result)
        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["quote_code"], "Q-001")
        self.assertEqual(result["instance_id"], 1001)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)
        self.assertEqual(result["task_history"][0]["node_name"], "销售主管审批")

    def test_get_quote_approval_status_not_found(self):
        """测试查询不存在的报价"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        result = self.service.get_quote_approval_status(quote_id=999)

        self.assertIsNone(result)

    def test_get_quote_approval_status_no_instance(self):
        """测试报价没有审批实例"""
        quote = self._create_mock_quote(id=1, quote_code="Q-001", status="DRAFT")

        mock_quote_query = MagicMock()
        mock_quote_query.filter.return_value.first.return_value = quote

        mock_instance_query = MagicMock()
        mock_instance_query.filter.return_value.order_by.return_value.first.return_value = None

        self.mock_db.query.side_effect = [mock_quote_query, mock_instance_query]

        result = self.service.get_quote_approval_status(quote_id=1)

        self.assertIsNotNone(result)
        self.assertEqual(result["quote_id"], 1)
        self.assertIsNone(result["approval_instance"])

    # ========== withdraw_approval() 测试 ==========

    def test_withdraw_approval_success(self):
        """测试成功撤回审批"""
        quote = self._create_mock_quote(id=1, quote_code="Q-001")

        instance = MagicMock()
        instance.id = 1001
        instance.initiator_id = 50
        instance.status = "PENDING"

        mock_quote_query = MagicMock()
        mock_quote_query.filter.return_value.first.return_value = quote

        mock_instance_query = MagicMock()
        mock_instance_query.filter.return_value.first.return_value = instance

        self.mock_db.query.side_effect = [mock_quote_query, mock_instance_query]

        result = self.service.withdraw_approval(quote_id=1, user_id=50, reason="需要修改")

        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["status"], "withdrawn")

        self.service.approval_engine.withdraw.assert_called_once_with(
            instance_id=1001,
            user_id=50
        )

    def test_withdraw_approval_quote_not_found(self):
        """测试撤回不存在的报价"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=999, user_id=50)

        self.assertIn("报价不存在", str(context.exception))

    def test_withdraw_approval_no_pending_instance(self):
        """测试撤回时没有进行中的审批"""
        quote = self._create_mock_quote(id=1)

        mock_quote_query = MagicMock()
        mock_quote_query.filter.return_value.first.return_value = quote

        mock_instance_query = MagicMock()
        mock_instance_query.filter.return_value.first.return_value = None

        self.mock_db.query.side_effect = [mock_quote_query, mock_instance_query]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=1, user_id=50)

        self.assertIn("没有进行中的审批流程", str(context.exception))

    def test_withdraw_approval_not_initiator(self):
        """测试非发起人尝试撤回"""
        quote = self._create_mock_quote(id=1)

        instance = MagicMock()
        instance.initiator_id = 50  # 发起人是50
        instance.status = "PENDING"

        mock_quote_query = MagicMock()
        mock_quote_query.filter.return_value.first.return_value = quote

        mock_instance_query = MagicMock()
        mock_instance_query.filter.return_value.first.return_value = instance

        self.mock_db.query.side_effect = [mock_quote_query, mock_instance_query]

        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=1, user_id=99)  # 用户99尝试撤回

        self.assertIn("只能撤回自己提交的审批", str(context.exception))

    # ========== get_approval_history() 测试 ==========

    def test_get_approval_history_success(self):
        """测试获取审批历史成功"""
        task1 = MagicMock()
        task1.id = 301
        task1.instance = MagicMock(entity_id=1)
        task1.status = "APPROVED"
        task1.action = "approve"
        task1.comment = "同意"
        task1.completed_at = datetime(2024, 1, 15, 10, 0, 0)

        quote1 = self._create_mock_quote(id=1, quote_code="Q-001")
        quote1.customer = MagicMock(name="客户A")

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [task1]

        # Mock quote查询
        mock_quote_query = MagicMock()
        mock_quote_query.filter.return_value.first.return_value = quote1

        self.mock_db.query.side_effect = [mock_query, mock_quote_query]

        result = self.service.get_approval_history(user_id=50)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["task_id"], 301)
        self.assertEqual(result["items"][0]["quote_code"], "Q-001")

    def test_get_approval_history_with_status_filter(self):
        """测试带状态筛选的审批历史"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        self.mock_db.query.return_value = mock_query

        result = self.service.get_approval_history(
            user_id=50,
            status_filter="REJECTED"
        )

        self.assertEqual(result["total"], 0)
        # 验证filter被调用了两次（一次基础筛选，一次状态筛选）
        self.assertGreaterEqual(mock_query.filter.call_count, 2)

    def test_get_approval_history_pagination(self):
        """测试审批历史分页"""
        tasks = [MagicMock(
            id=300+i,
            instance=MagicMock(entity_id=i),
            status="APPROVED",
            action="approve",
            comment=None,
            completed_at=datetime(2024, 1, i, 10, 0, 0)
        ) for i in range(1, 26)]

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 25
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = tasks[20:25]

        # Mock quote查询
        quotes = [self._create_mock_quote(id=i, quote_code=f"Q-{i:03d}") for i in range(21, 26)]
        for q in quotes:
            q.customer = MagicMock(name=f"客户{q.id}")

        mock_quote_query = MagicMock()
        mock_quote_query.filter.return_value.first.side_effect = quotes

        self.mock_db.query.side_effect = [mock_query] + [mock_quote_query] * 5

        result = self.service.get_approval_history(
            user_id=50,
            offset=20,
            limit=10
        )

        self.assertEqual(result["total"], 25)
        self.assertEqual(len(result["items"]), 5)

    # ========== 私有方法测试 ==========

    def test_get_quote_version_with_version_ids(self):
        """测试使用指定版本ID获取版本"""
        quote = self._create_mock_quote(id=1)
        specified_version = self._create_mock_version(id=15, version_no="V2")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = specified_version
        self.mock_db.query.return_value = mock_query

        result = self.service._get_quote_version(
            quote=quote,
            version_ids=[15],
            index=0
        )

        self.assertEqual(result.id, 15)
        self.assertEqual(result.version_no, "V2")

    def test_get_quote_version_use_current(self):
        """测试使用当前版本"""
        quote = self._create_mock_quote(id=1)
        current_version = self._create_mock_version(id=10, version_no="V1")
        quote.current_version = current_version

        result = self.service._get_quote_version(
            quote=quote,
            version_ids=None,
            index=0
        )

        self.assertEqual(result.id, 10)

    def test_get_quote_version_fallback_to_latest(self):
        """测试回退到最新版本"""
        quote = self._create_mock_quote(id=1)
        quote.current_version = None

        latest_version = self._create_mock_version(id=20, version_no="V3")

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = latest_version
        self.mock_db.query.return_value = mock_query

        result = self.service._get_quote_version(
            quote=quote,
            version_ids=None,
            index=0
        )

        self.assertEqual(result.id, 20)

    def test_get_current_version_from_quote(self):
        """测试从报价获取当前版本"""
        quote = self._create_mock_quote(id=1)
        version = self._create_mock_version(id=10)
        quote.current_version = version

        result = self.service._get_current_version(quote)

        self.assertEqual(result.id, 10)

    def test_get_current_version_from_db(self):
        """测试从数据库获取最新版本"""
        quote = self._create_mock_quote(id=1)
        quote.current_version = None

        latest_version = self._create_mock_version(id=20)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = latest_version
        self.mock_db.query.return_value = mock_query

        result = self.service._get_current_version(quote)

        self.assertEqual(result.id, 20)

    def test_get_current_version_none_quote(self):
        """测试传入None报价"""
        result = self.service._get_current_version(None)
        self.assertIsNone(result)

    def test_build_form_data(self):
        """测试构建表单数据"""
        quote = self._create_mock_quote(
            id=1,
            quote_code="Q-2024-001",
            customer_id=100
        )
        quote.customer = MagicMock()
        quote.customer.name = "测试客户"

        version = self._create_mock_version(
            id=10,
            version_no="V1",
            total_price=Decimal("10000.50"),
            cost_total=Decimal("7000.30"),
            gross_margin=Decimal("0.3002"),
            lead_time_days=7
        )

        result = self.service._build_form_data(quote, version)

        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["quote_code"], "Q-2024-001")
        self.assertEqual(result["version_id"], 10)
        self.assertEqual(result["version_no"], "V1")
        self.assertEqual(result["total_price"], 10000.50)
        self.assertEqual(result["cost_total"], 7000.30)
        self.assertEqual(result["gross_margin"], 0.3002)
        self.assertEqual(result["customer_id"], 100)
        self.assertEqual(result["customer_name"], "测试客户")
        self.assertEqual(result["lead_time_days"], 7)

    def test_build_form_data_with_none_values(self):
        """测试构建表单数据（包含None值）"""
        quote = self._create_mock_quote(id=1, quote_code="Q-001", customer_id=100)
        quote.customer = None

        version = self._create_mock_version(
            id=10,
            version_no="V1",
            total_price=None,
            cost_total=None,
            gross_margin=None,
            lead_time_days=None
        )

        result = self.service._build_form_data(quote, version)

        self.assertEqual(result["total_price"], 0)
        self.assertEqual(result["cost_total"], 0)
        self.assertEqual(result["gross_margin"], 0)
        self.assertIsNone(result["customer_name"])
        self.assertIsNone(result["lead_time_days"])

    # ========== 辅助方法 ==========

    def _create_mock_quote(
        self,
        id: int,
        quote_code: str = "Q-TEST",
        status: str = "DRAFT",
        customer_id: int = 100
    ):
        """创建mock报价对象"""
        quote = MagicMock()
        quote.id = id
        quote.quote_code = quote_code
        quote.status = status
        quote.customer_id = customer_id
        quote.customer = None
        quote.current_version = None
        return quote

    def _create_mock_version(
        self,
        id: int = 1,
        version_no: str = "V1",
        quote_id: int = 1,
        total_price: Decimal = Decimal("10000"),
        cost_total: Decimal = Decimal("7000"),
        gross_margin: Decimal = Decimal("0.30"),
        lead_time_days: int = 7
    ):
        """创建mock版本对象"""
        version = MagicMock()
        version.id = id
        version.version_no = version_no
        version.quote_id = quote_id
        version.total_price = total_price
        version.cost_total = cost_total
        version.gross_margin = gross_margin
        version.lead_time_days = lead_time_days
        return version

    def _create_mock_task(
        self,
        task_id: int,
        quote_id: int,
        quote_code: str = "Q-TEST",
        customer_name: str = "测试客户",
        version_no: str = "V1",
        total_price: Decimal = Decimal("10000"),
        gross_margin: Decimal = Decimal("0.30")
    ):
        """创建mock审批任务"""
        task = MagicMock()
        task.id = task_id
        task.instance = MagicMock()
        task.instance.id = 1000 + task_id
        task.instance.entity_id = quote_id
        task.instance.urgency = "NORMAL"
        task.instance.created_at = datetime(2024, 1, 15, 10, 0, 0)
        task.instance.initiator = MagicMock(real_name="发起人")
        task.node = MagicMock(node_name="审批节点")

        # 关联的报价
        quote = self._create_mock_quote(id=quote_id, quote_code=quote_code)
        quote.customer = MagicMock(name=customer_name)
        quote.current_version = self._create_mock_version(
            version_no=version_no,
            total_price=total_price,
            gross_margin=gross_margin
        )

        return task


if __name__ == "__main__":
    unittest.main()

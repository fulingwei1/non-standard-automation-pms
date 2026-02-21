# -*- coding: utf-8 -*-
"""
报价审批服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率

参考: tests/unit/test_condition_parser_rewrite.py的mock策略
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from decimal import Decimal

from app.services.quote_approval.quote_approval_service import QuoteApprovalService


class TestQuoteApprovalServiceSubmit(unittest.TestCase):
    """测试提交审批功能"""

    def setUp(self):
        """初始化测试环境"""
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(self.mock_db)
        # Mock approval engine
        self.service.approval_engine = MagicMock()

    def test_submit_quotes_success_single(self):
        """测试单个报价提交成功"""
        # Mock数据
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q2024001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = 100
        mock_quote.customer.name = "测试客户"
        
        mock_version = MagicMock()
        mock_version.id = 10
        mock_version.version_no = "V1.0"
        mock_version.total_price = Decimal("10000.00")
        mock_version.cost_total = Decimal("8000.00")
        mock_version.gross_margin = Decimal("0.2")
        mock_version.lead_time_days = 30
        mock_quote.current_version = mock_version
        
        # Mock db.query
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        # Mock approval engine submit
        mock_instance = MagicMock()
        mock_instance.id = 999
        self.service.approval_engine.submit.return_value = mock_instance
        
        # 执行
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=200,
            urgency="NORMAL"
        )
        
        # 验证
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["success"][0]["quote_id"], 1)
        self.assertEqual(result["success"][0]["quote_code"], "Q2024001")
        self.assertEqual(result["success"][0]["instance_id"], 999)
        self.assertEqual(result["success"][0]["status"], "submitted")
        
        # 验证调用了approval_engine.submit
        self.service.approval_engine.submit.assert_called_once()

    def test_submit_quotes_not_found(self):
        """测试报价不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.submit_quotes_for_approval(
            quote_ids=[999],
            initiator_id=200
        )
        
        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["quote_id"], 999)
        self.assertEqual(result["errors"][0]["error"], "报价不存在")

    def test_submit_quotes_invalid_status(self):
        """测试无效状态（不允许提交）"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.status = "APPROVED"  # 已审批状态不能重复提交
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=200
        )
        
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不允许提交审批", result["errors"][0]["error"])

    def test_submit_quotes_no_version(self):
        """测试没有版本信息"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.status = "DRAFT"
        mock_quote.current_version = None
        
        # Mock QueryVersion返回None
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_quote,  # 第一次返回quote
        ]
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=200
        )
        
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("没有版本", result["errors"][0]["error"])

    def test_submit_quotes_batch_mixed(self):
        """测试批量提交（部分成功、部分失败）"""
        # Mock第一个报价（成功）
        mock_quote1 = MagicMock()
        mock_quote1.id = 1
        mock_quote1.status = "DRAFT"
        mock_quote1.quote_code = "Q001"
        mock_version1 = MagicMock()
        mock_version1.id = 10
        mock_version1.version_no = "V1.0"
        mock_version1.total_price = Decimal("1000")
        mock_quote1.current_version = mock_version1
        mock_quote1.customer_id = 100
        mock_quote1.customer.name = "客户A"
        
        # Mock第二个报价（不存在）
        
        # Mock第三个报价（状态错误）
        mock_quote3 = MagicMock()
        mock_quote3.id = 3
        mock_quote3.status = "APPROVED"
        
        # 配置db.query的返回值
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_quote1,  # quote_id=1
            None,         # quote_id=2 不存在
            mock_quote3,  # quote_id=3
        ]
        
        # Mock approval engine
        mock_instance = MagicMock()
        mock_instance.id = 888
        self.service.approval_engine.submit.return_value = mock_instance
        
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1, 2, 3],
            initiator_id=200
        )
        
        # 验证
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(len(result["errors"]), 2)
        self.assertEqual(result["success"][0]["quote_id"], 1)
        self.assertEqual(result["errors"][0]["quote_id"], 2)
        self.assertEqual(result["errors"][1]["quote_id"], 3)

    def test_submit_quotes_with_version_ids(self):
        """测试指定版本ID提交"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = 100
        mock_quote.customer.name = "客户"
        
        mock_version = MagicMock()
        mock_version.id = 99
        mock_version.version_no = "V2.0"
        mock_version.total_price = Decimal("2000")
        mock_version.cost_total = Decimal("1500")
        mock_version.gross_margin = Decimal("0.25")
        mock_version.lead_time_days = 20
        
        # Mock查询
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_quote,   # quote查询
            mock_version  # version查询
        ]
        
        mock_instance = MagicMock()
        mock_instance.id = 777
        self.service.approval_engine.submit.return_value = mock_instance
        
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=200,
            version_ids=[99]
        )
        
        self.assertEqual(len(result["success"]), 1)
        self.assertEqual(result["success"][0]["version_no"], "V2.0")


class TestQuoteApprovalServicePendingTasks(unittest.TestCase):
    """测试获取待审批任务"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(self.mock_db)
        self.service.approval_engine = MagicMock()

    def test_get_pending_tasks_empty(self):
        """测试空任务列表"""
        self.service.approval_engine.get_pending_tasks.return_value = []
        
        result = self.service.get_pending_tasks(user_id=100)
        
        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_pending_tasks_basic(self):
        """测试基本任务列表"""
        # Mock任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.instance.id = 100
        mock_task.instance.entity_id = 50
        mock_task.instance.urgency = "HIGH"
        mock_task.instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_task.instance.initiator.real_name = "张三"
        mock_task.node.node_name = "部门经理审批"
        
        # Mock报价
        mock_quote = MagicMock()
        mock_quote.id = 50
        mock_quote.quote_code = "Q2024001"
        mock_quote.customer_id = 200
        mock_quote.customer.name = "ABC公司"
        
        # Mock版本
        mock_version = MagicMock()
        mock_version.version_no = "V1.0"
        mock_version.total_price = Decimal("50000.00")
        mock_version.gross_margin = Decimal("0.3")
        mock_version.lead_time_days = 45
        mock_quote.current_version = mock_version
        
        self.service.approval_engine.get_pending_tasks.return_value = [mock_task]
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.service.get_pending_tasks(user_id=100)
        
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["task_id"], 1)
        self.assertEqual(item["quote_code"], "Q2024001")
        self.assertEqual(item["customer_name"], "ABC公司")
        self.assertEqual(item["total_price"], 50000.0)
        self.assertEqual(item["gross_margin"], 0.3)
        self.assertEqual(item["urgency"], "HIGH")

    def test_get_pending_tasks_with_customer_filter(self):
        """测试按客户筛选"""
        # Mock任务
        mock_task1 = MagicMock()
        mock_task1.instance.entity_id = 1
        mock_task2 = MagicMock()
        mock_task2.instance.entity_id = 2
        
        # Mock报价
        mock_quote1 = MagicMock()
        mock_quote1.id = 1
        mock_quote1.customer_id = 100  # 匹配
        mock_quote1.quote_code = "Q001"
        mock_quote1.customer.name = "客户A"
        mock_version1 = MagicMock()
        mock_version1.version_no = "V1.0"
        mock_version1.total_price = Decimal("1000")
        mock_version1.gross_margin = Decimal("0.2")
        mock_version1.lead_time_days = 30
        mock_quote1.current_version = mock_version1
        
        mock_quote2 = MagicMock()
        mock_quote2.id = 2
        mock_quote2.customer_id = 200  # 不匹配
        mock_quote2.quote_code = "Q002"
        mock_quote2.customer.name = "客户B"
        mock_quote2.current_version = mock_version1
        
        self.service.approval_engine.get_pending_tasks.return_value = [mock_task1, mock_task2]
        
        # Mock db.query根据循环次数返回不同的quote
        query_count = [0]
        def mock_query_first():
            query_count[0] += 1
            if query_count[0] == 1:
                return mock_quote1
            else:
                return mock_quote2
        
        self.mock_db.query.return_value.filter.return_value.first = mock_query_first
        
        result = self.service.get_pending_tasks(user_id=100, customer_id=100)
        
        # 只有customer_id=100的任务
        self.assertEqual(result["total"], 1)

    def test_get_pending_tasks_pagination(self):
        """测试分页"""
        # 创建10个任务
        mock_tasks = []
        for i in range(10):
            task = MagicMock()
            task.id = i + 1
            task.instance.id = i + 100
            task.instance.entity_id = i + 50
            task.instance.urgency = "NORMAL"
            task.instance.created_at = datetime(2024, 1, 1)
            task.instance.initiator.real_name = f"用户{i}"
            task.node.node_name = "审批节点"
            mock_tasks.append(task)
            
            # Mock对应的quote
            quote = MagicMock()
            quote.quote_code = f"Q{i:04d}"
            quote.customer.name = f"客户{i}"
            version = MagicMock()
            version.version_no = "V1.0"
            version.total_price = Decimal("1000")
            version.gross_margin = Decimal("0.2")
            version.lead_time_days = 30
            quote.current_version = version
            self.mock_db.query.return_value.filter.return_value.first.return_value = quote
        
        self.service.approval_engine.get_pending_tasks.return_value = mock_tasks
        
        # 测试第1页（offset=0, limit=5）
        result = self.service.get_pending_tasks(user_id=100, offset=0, limit=5)
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(result["items"]), 5)
        
        # 测试第2页（offset=5, limit=5）
        result = self.service.get_pending_tasks(user_id=100, offset=5, limit=5)
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(result["items"]), 5)


class TestQuoteApprovalServiceActions(unittest.TestCase):
    """测试审批操作"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(self.mock_db)
        self.service.approval_engine = MagicMock()

    def test_perform_action_approve(self):
        """测试通过操作"""
        mock_result = MagicMock()
        mock_result.status = "APPROVED"
        self.service.approval_engine.approve.return_value = mock_result
        
        result = self.service.perform_action(
            task_id=1,
            action="approve",
            approver_id=100,
            comment="同意"
        )
        
        self.assertEqual(result["task_id"], 1)
        self.assertEqual(result["action"], "approve")
        self.assertEqual(result["instance_status"], "APPROVED")
        self.service.approval_engine.approve.assert_called_once_with(
            task_id=1,
            approver_id=100,
            comment="同意"
        )

    def test_perform_action_reject(self):
        """测试拒绝操作"""
        mock_result = MagicMock()
        mock_result.status = "REJECTED"
        self.service.approval_engine.reject.return_value = mock_result
        
        result = self.service.perform_action(
            task_id=2,
            action="reject",
            approver_id=200,
            comment="不符合要求"
        )
        
        self.assertEqual(result["task_id"], 2)
        self.assertEqual(result["action"], "reject")
        self.assertEqual(result["instance_status"], "REJECTED")
        self.service.approval_engine.reject.assert_called_once_with(
            task_id=2,
            approver_id=200,
            comment="不符合要求"
        )

    def test_perform_action_invalid(self):
        """测试无效操作类型"""
        with self.assertRaises(ValueError) as context:
            self.service.perform_action(
                task_id=1,
                action="invalid_action",
                approver_id=100
            )
        self.assertIn("不支持的操作类型", str(context.exception))

    def test_perform_batch_actions_approve(self):
        """测试批量通过"""
        self.service.approval_engine.approve.return_value = MagicMock()
        
        result = self.service.perform_batch_actions(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=100
        )
        
        self.assertEqual(len(result["success"]), 3)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(self.service.approval_engine.approve.call_count, 3)

    def test_perform_batch_actions_reject(self):
        """测试批量拒绝"""
        self.service.approval_engine.reject.return_value = MagicMock()
        
        result = self.service.perform_batch_actions(
            task_ids=[4, 5],
            action="reject",
            approver_id=200,
            comment="批量拒绝"
        )
        
        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(self.service.approval_engine.reject.call_count, 2)

    def test_perform_batch_actions_mixed_results(self):
        """测试批量操作（部分成功、部分失败）"""
        # 第一次成功，第二次抛出异常，第三次成功
        self.service.approval_engine.approve.side_effect = [
            MagicMock(),  # 成功
            Exception("审批失败"),  # 失败
            MagicMock(),  # 成功
        ]
        
        result = self.service.perform_batch_actions(
            task_ids=[1, 2, 3],
            action="approve",
            approver_id=100
        )
        
        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["task_id"], 2)

    def test_perform_batch_actions_invalid_action(self):
        """测试批量操作无效action"""
        result = self.service.perform_batch_actions(
            task_ids=[1, 2],
            action="unknown",
            approver_id=100
        )
        
        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 2)
        self.assertIn("不支持的操作", result["errors"][0]["error"])


class TestQuoteApprovalServiceStatus(unittest.TestCase):
    """测试审批状态查询"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(self.mock_db)

    def test_get_quote_approval_status_not_found(self):
        """测试报价不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_quote_approval_status(quote_id=999)
        
        self.assertIsNone(result)

    def test_get_quote_approval_status_no_instance(self):
        """测试没有审批实例"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q001"
        mock_quote.status = "DRAFT"
        
        # Mock查询：第一次返回quote，第二次返回None（没有instance）
        query_count = [0]
        def mock_query(*args):
            query_count[0] += 1
            mock_result = MagicMock()
            if query_count[0] == 1:  # Quote查询
                mock_result.filter.return_value.first.return_value = mock_quote
            else:  # ApprovalInstance查询
                mock_result.filter.return_value.order_by.return_value.first.return_value = None
            return mock_result
        
        self.mock_db.query.side_effect = mock_query
        
        result = self.service.get_quote_approval_status(quote_id=1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["quote_code"], "Q001")
        self.assertIsNone(result["approval_instance"])

    def test_get_quote_approval_status_with_instance(self):
        """测试包含审批实例信息"""
        # Mock报价
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q2024001"
        mock_quote.status = "PENDING_APPROVAL"
        mock_quote.customer.name = "客户A"
        
        # Mock版本
        mock_version = MagicMock()
        mock_version.version_no = "V1.0"
        mock_version.total_price = Decimal("10000")
        mock_version.gross_margin = Decimal("0.25")
        mock_quote.current_version = mock_version
        
        # Mock审批实例
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        mock_instance.urgency = "NORMAL"
        mock_instance.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_instance.completed_at = None
        
        # Mock任务历史
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task1.node.node_name = "经理审批"
        mock_task1.assignee.real_name = "张经理"
        mock_task1.status = "APPROVED"
        mock_task1.action = "approve"
        mock_task1.comment = "同意"
        mock_task1.completed_at = datetime(2024, 1, 2, 10, 0, 0)
        
        # 配置mock
        query_count = [0]
        def mock_query(*args):
            query_count[0] += 1
            mock_result = MagicMock()
            if query_count[0] == 1:  # Quote查询
                mock_result.filter.return_value.first.return_value = mock_quote
            elif query_count[0] == 2:  # ApprovalInstance查询
                mock_result.filter.return_value.order_by.return_value.first.return_value = mock_instance
            elif query_count[0] == 3:  # ApprovalTask查询
                mock_result.filter.return_value.order_by.return_value.all.return_value = [mock_task1]
            return mock_result
        
        self.mock_db.query.side_effect = mock_query
        
        result = self.service.get_quote_approval_status(quote_id=1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["instance_id"], 100)
        self.assertEqual(result["instance_status"], "PENDING")
        self.assertEqual(len(result["task_history"]), 1)
        self.assertEqual(result["task_history"][0]["node_name"], "经理审批")
        self.assertEqual(result["version_info"]["version_no"], "V1.0")


class TestQuoteApprovalServiceWithdraw(unittest.TestCase):
    """测试撤回审批"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(self.mock_db)
        self.service.approval_engine = MagicMock()

    def test_withdraw_approval_quote_not_found(self):
        """测试报价不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=999, user_id=100)
        self.assertEqual(str(context.exception), "报价不存在")

    def test_withdraw_approval_no_pending_instance(self):
        """测试没有进行中的审批"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        
        # Mock: quote存在，但没有pending的instance
        query_count = [0]
        def mock_query_filter(*args, **kwargs):
            query_count[0] += 1
            mock_result = MagicMock()
            if query_count[0] == 1:  # Quote查询
                mock_result.first.return_value = mock_quote
            else:  # ApprovalInstance查询
                mock_result.first.return_value = None
            return mock_result
        
        self.mock_db.query.return_value.filter.side_effect = mock_query_filter
        
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=1, user_id=100)
        self.assertEqual(str(context.exception), "没有进行中的审批流程可撤回")

    def test_withdraw_approval_permission_denied(self):
        """测试没有撤回权限（不是发起人）"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q001"
        
        mock_instance = MagicMock()
        mock_instance.initiator_id = 100  # 发起人是100
        
        # Mock查询
        query_count = [0]
        def mock_query_filter(*args, **kwargs):
            query_count[0] += 1
            mock_result = MagicMock()
            if query_count[0] == 1:
                mock_result.first.return_value = mock_quote
            else:
                mock_result.first.return_value = mock_instance
            return mock_result
        
        self.mock_db.query.return_value.filter.side_effect = mock_query_filter
        
        # 用户200尝试撤回（不是发起人）
        with self.assertRaises(ValueError) as context:
            self.service.withdraw_approval(quote_id=1, user_id=200, reason="撤回")
        self.assertEqual(str(context.exception), "只能撤回自己提交的审批")

    def test_withdraw_approval_success(self):
        """测试撤回成功"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q2024001"
        
        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.initiator_id = 50  # 发起人
        
        # Mock查询
        query_count = [0]
        def mock_query_filter(*args, **kwargs):
            query_count[0] += 1
            mock_result = MagicMock()
            if query_count[0] == 1:
                mock_result.first.return_value = mock_quote
            else:
                mock_result.first.return_value = mock_instance
            return mock_result
        
        self.mock_db.query.return_value.filter.side_effect = mock_query_filter
        
        result = self.service.withdraw_approval(
            quote_id=1,
            user_id=50,  # 发起人自己撤回
            reason="需要修改报价"
        )
        
        self.assertEqual(result["quote_id"], 1)
        self.assertEqual(result["quote_code"], "Q2024001")
        self.assertEqual(result["status"], "withdrawn")
        
        # 验证调用了engine的withdraw
        self.service.approval_engine.withdraw.assert_called_once_with(
            instance_id=100,
            user_id=50
        )


class TestQuoteApprovalServiceHistory(unittest.TestCase):
    """测试审批历史"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(self.mock_db)

    def test_get_approval_history_empty(self):
        """测试空历史"""
        self.mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        self.mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_approval_history(user_id=100)
        
        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_get_approval_history_basic(self):
        """测试基本历史记录"""
        # Mock任务
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.instance.entity_id = 50
        mock_task.action = "approve"
        mock_task.status = "APPROVED"
        mock_task.comment = "同意"
        mock_task.completed_at = datetime(2024, 1, 10, 15, 0, 0)
        
        # Mock报价
        mock_quote = MagicMock()
        mock_quote.quote_code = "Q2024001"
        mock_quote.customer.name = "客户A"
        
        self.mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 1
        self.mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_task]
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.service.get_approval_history(user_id=100)
        
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["task_id"], 1)
        self.assertEqual(item["quote_code"], "Q2024001")
        self.assertEqual(item["action"], "approve")
        self.assertEqual(item["status"], "APPROVED")

    def test_get_approval_history_with_status_filter(self):
        """测试带状态筛选的历史"""
        # 验证filter被调用时包含status_filter
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.get_approval_history(
            user_id=100,
            status_filter="APPROVED"
        )
        
        # 验证filter被调用
        self.assertTrue(mock_query.filter.called)


class TestQuoteApprovalServicePrivateMethods(unittest.TestCase):
    """测试私有辅助方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(self.mock_db)

    def test_build_form_data(self):
        """测试构建表单数据"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q001"
        mock_quote.customer_id = 100
        mock_quote.customer.name = "测试客户"
        
        mock_version = MagicMock()
        mock_version.id = 10
        mock_version.version_no = "V1.0"
        mock_version.total_price = Decimal("5000.50")
        mock_version.cost_total = Decimal("4000.00")
        mock_version.gross_margin = Decimal("0.20")
        mock_version.lead_time_days = 30
        
        form_data = self.service._build_form_data(mock_quote, mock_version)
        
        self.assertEqual(form_data["quote_id"], 1)
        self.assertEqual(form_data["quote_code"], "Q001")
        self.assertEqual(form_data["version_id"], 10)
        self.assertEqual(form_data["version_no"], "V1.0")
        self.assertEqual(form_data["total_price"], 5000.50)
        self.assertEqual(form_data["cost_total"], 4000.00)
        self.assertEqual(form_data["gross_margin"], 0.20)
        self.assertEqual(form_data["customer_id"], 100)
        self.assertEqual(form_data["customer_name"], "测试客户")
        self.assertEqual(form_data["lead_time_days"], 30)

    def test_build_form_data_with_none_values(self):
        """测试构建表单数据（包含None值）"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q001"
        mock_quote.customer_id = 100
        mock_quote.customer = None  # customer为None
        
        mock_version = MagicMock()
        mock_version.id = 10
        mock_version.version_no = "V1.0"
        mock_version.total_price = None
        mock_version.cost_total = None
        mock_version.gross_margin = None
        mock_version.lead_time_days = None
        
        form_data = self.service._build_form_data(mock_quote, mock_version)
        
        self.assertEqual(form_data["total_price"], 0)
        self.assertEqual(form_data["cost_total"], 0)
        self.assertEqual(form_data["gross_margin"], 0)
        self.assertIsNone(form_data["customer_name"])
        self.assertIsNone(form_data["lead_time_days"])

    def test_get_current_version_with_current(self):
        """测试获取当前版本（current_version存在）"""
        mock_quote = MagicMock()
        mock_version = MagicMock()
        mock_version.id = 10
        mock_quote.current_version = mock_version
        
        result = self.service._get_current_version(mock_quote)
        
        self.assertEqual(result.id, 10)

    def test_get_current_version_fallback_to_latest(self):
        """测试获取当前版本（fallback到最新版本）"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.current_version = None
        
        mock_version = MagicMock()
        mock_version.id = 20
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_version
        
        result = self.service._get_current_version(mock_quote)
        
        self.assertEqual(result.id, 20)

    def test_get_current_version_none_quote(self):
        """测试获取当前版本（quote为None）"""
        result = self.service._get_current_version(None)
        self.assertIsNone(result)


class TestQuoteApprovalServiceEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = QuoteApprovalService(self.mock_db)
        self.service.approval_engine = MagicMock()

    def test_submit_with_exception(self):
        """测试提交时抛出异常"""
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.status = "DRAFT"
        mock_version = MagicMock()
        mock_quote.current_version = mock_version
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        # Mock approval_engine.submit抛出异常
        self.service.approval_engine.submit.side_effect = Exception("系统错误")
        
        result = self.service.submit_quotes_for_approval(
            quote_ids=[1],
            initiator_id=100
        )
        
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("系统错误", result["errors"][0]["error"])

    def test_get_pending_tasks_quote_not_found(self):
        """测试待审批任务中报价被删除"""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.instance.entity_id = 999  # 不存在的报价
        
        self.service.approval_engine.get_pending_tasks.return_value = [mock_task]
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_pending_tasks(user_id=100)
        
        # 应该返回任务，但quote相关字段为None
        self.assertEqual(result["total"], 1)
        item = result["items"][0]
        self.assertIsNone(item["quote_code"])

    def test_empty_quote_ids(self):
        """测试空的quote_ids列表"""
        result = self.service.submit_quotes_for_approval(
            quote_ids=[],
            initiator_id=100
        )
        
        self.assertEqual(len(result["success"]), 0)
        self.assertEqual(len(result["errors"]), 0)


if __name__ == "__main__":
    unittest.main()

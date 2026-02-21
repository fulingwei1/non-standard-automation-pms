# -*- coding: utf-8 -*-
"""
报价审批适配器单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库查询）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter
from app.models.sales.quotes import Quote, QuoteVersion
from app.models.sales.technical_assessment import QuoteApproval
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.project.customer import Customer
from app.models.user import User


class TestQuoteAdapterCore(unittest.TestCase):
    """测试核心适配器方法"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.db)
        self.entity_id = 1
        self.instance = MagicMock(spec=ApprovalInstance)

    # ========== get_entity() 测试 ==========

    def test_get_entity_success(self):
        """测试成功获取报价实体"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.id = self.entity_id
        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        result = self.adapter.get_entity(self.entity_id)

        self.assertEqual(result, mock_quote)
        self.db.query.assert_called_once_with(Quote)

    def test_get_entity_not_found(self):
        """测试获取不存在的报价"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(self.entity_id)

        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_basic(self):
        """测试获取基础报价数据"""
        mock_quote = self._create_mock_quote(
            quote_code="QT-2024-001",
            status="DRAFT",
            customer_id=10,
            owner_id=20
        )

        mock_customer = MagicMock(spec=Customer)
        mock_customer.name = "测试客户A"

        mock_owner = MagicMock(spec=User)
        mock_owner.name = "张三"

        mock_quote.customer = mock_customer
        mock_quote.owner = mock_owner

        self._setup_basic_query(mock_quote)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证基础字段
        self.assertEqual(result["quote_code"], "QT-2024-001")
        self.assertEqual(result["status"], "DRAFT")
        self.assertEqual(result["customer_id"], 10)
        self.assertEqual(result["customer_name"], "测试客户A")
        self.assertEqual(result["owner_id"], 20)
        self.assertEqual(result["owner_name"], "张三")

    def test_get_entity_data_with_version(self):
        """测试获取包含版本信息的报价数据"""
        mock_version = self._create_mock_version(
            version_no=1,
            total_price=Decimal("100000.00"),
            cost_total=Decimal("70000.00"),
            gross_margin=Decimal("0.3"),  # 30%（小数形式）
            lead_time_days=30,
            delivery_date=date(2024, 3, 15)
        )

        mock_quote = self._create_mock_quote(quote_code="QT-2024-001")
        mock_quote.current_version = mock_version

        self._setup_basic_query(mock_quote)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证版本数据
        self.assertEqual(result["version_no"], 1)
        self.assertEqual(result["total_price"], 100000.0)
        self.assertEqual(result["cost_total"], 70000.0)
        self.assertEqual(result["gross_margin"], 30.0)  # 转换为百分比
        self.assertEqual(result["lead_time_days"], 30)
        self.assertEqual(result["delivery_date"], "2024-03-15")

    def test_get_entity_data_gross_margin_already_percentage(self):
        """测试毛利率已经是百分比形式"""
        mock_version = self._create_mock_version(
            total_price=Decimal("100000.00"),
            gross_margin=Decimal("30.0")  # 已经是百分比
        )

        mock_quote = self._create_mock_quote()
        mock_quote.current_version = mock_version

        self._setup_basic_query(mock_quote)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证毛利率保持不变
        self.assertEqual(result["gross_margin"], 30.0)

    def test_get_entity_data_gross_margin_none(self):
        """测试毛利率为None"""
        mock_version = self._create_mock_version(
            total_price=Decimal("100000.00"),
            gross_margin=None
        )

        mock_quote = self._create_mock_quote()
        mock_quote.current_version = mock_version

        self._setup_basic_query(mock_quote)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证毛利率为None
        self.assertIsNone(result["gross_margin"])

    def test_get_entity_data_no_current_version_fallback(self):
        """测试没有current_version时回退到最新版本"""
        mock_version = self._create_mock_version(
            version_no=2,
            total_price=Decimal("200000.00")
        )

        mock_quote = self._create_mock_quote()
        mock_quote.current_version = None

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Quote:
                mock_query.filter.return_value.first.return_value = mock_quote
            elif model == QuoteVersion:
                # 模拟order_by和first的链式调用
                mock_query.filter.return_value.order_by.return_value.first.return_value = mock_version
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证使用了回退版本
        self.assertEqual(result["version_no"], 2)
        self.assertEqual(result["total_price"], 200000.0)

    def test_get_entity_data_no_version_at_all(self):
        """测试完全没有版本"""
        mock_quote = self._create_mock_quote()
        mock_quote.current_version = None

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Quote:
                mock_query.filter.return_value.first.return_value = mock_quote
            elif model == QuoteVersion:
                mock_query.filter.return_value.order_by.return_value.first.return_value = None
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证只有基础字段，没有版本字段
        self.assertIn("quote_code", result)
        self.assertNotIn("version_no", result)
        self.assertNotIn("total_price", result)

    def test_get_entity_data_quote_not_found(self):
        """测试获取不存在报价的数据"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity_data(self.entity_id)

        # 应返回空字典
        self.assertEqual(result, {})

    def test_get_entity_data_customer_none(self):
        """测试客户为None的情况"""
        mock_quote = self._create_mock_quote()
        mock_quote.customer = None

        self._setup_basic_query(mock_quote)

        result = self.adapter.get_entity_data(self.entity_id)

        self.assertIsNone(result["customer_name"])

    def test_get_entity_data_owner_none(self):
        """测试负责人为None的情况"""
        mock_quote = self._create_mock_quote()
        mock_quote.owner = None

        self._setup_basic_query(mock_quote)

        result = self.adapter.get_entity_data(self.entity_id)

        self.assertIsNone(result["owner_name"])

    # ========== on_submit() 测试 ==========

    def test_on_submit_success(self):
        """测试成功提交审批"""
        mock_quote = self._create_mock_quote(status="DRAFT")
        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        self.adapter.on_submit(self.entity_id, self.instance)

        # 验证状态更改
        self.assertEqual(mock_quote.status, "PENDING_APPROVAL")
        self.db.flush.assert_called_once()

    def test_on_submit_quote_not_found(self):
        """测试提交不存在的报价"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_submit(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_approved() 测试 ==========

    def test_on_approved_success(self):
        """测试成功审批通过"""
        mock_quote = self._create_mock_quote(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        self.adapter.on_approved(self.entity_id, self.instance)

        # 验证状态更改为APPROVED
        self.assertEqual(mock_quote.status, "APPROVED")
        self.db.flush.assert_called_once()

    def test_on_approved_quote_not_found(self):
        """测试审批通过不存在的报价"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_approved(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_rejected() 测试 ==========

    def test_on_rejected_success(self):
        """测试成功驳回审批"""
        mock_quote = self._create_mock_quote(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 验证状态更改为REJECTED
        self.assertEqual(mock_quote.status, "REJECTED")
        self.db.flush.assert_called_once()

    def test_on_rejected_quote_not_found(self):
        """测试驳回不存在的报价"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_withdrawn() 测试 ==========

    def test_on_withdrawn_success(self):
        """测试成功撤回审批"""
        mock_quote = self._create_mock_quote(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 验证状态恢复为DRAFT
        self.assertEqual(mock_quote.status, "DRAFT")
        self.db.flush.assert_called_once()

    def test_on_withdrawn_quote_not_found(self):
        """测试撤回不存在的报价"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== get_title() 测试 ==========

    def test_get_title_with_customer(self):
        """测试生成包含客户名称的标题"""
        mock_customer = MagicMock(spec=Customer)
        mock_customer.name = "华为技术有限公司"

        mock_quote = self._create_mock_quote(quote_code="QT-2024-001")
        mock_quote.customer = mock_customer

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, "报价审批 - QT-2024-001 (华为技术有限公司)")

    def test_get_title_without_customer(self):
        """测试生成无客户的标题"""
        mock_quote = self._create_mock_quote(quote_code="QT-2024-002")
        mock_quote.customer = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, "报价审批 - QT-2024-002 (未知客户)")

    def test_get_title_quote_not_found(self):
        """测试生成不存在报价的标题"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, f"报价审批 - #{self.entity_id}")

    # ========== get_summary() 测试 ==========

    def test_get_summary_full_data(self):
        """测试生成完整摘要"""
        data = {
            "customer_name": "华为技术",
            "total_price": 100000.00,
            "gross_margin": 30.5,
            "lead_time_days": 45
        }

        with patch.object(self.adapter, 'get_entity_data', return_value=data):
            summary = self.adapter.get_summary(self.entity_id)

        # 验证摘要包含所有关键信息
        self.assertIn("客户: 华为技术", summary)
        self.assertIn("总价: ¥100,000.00", summary)
        self.assertIn("毛利率: 30.5%", summary)
        self.assertIn("交期: 45天", summary)

    def test_get_summary_partial_data(self):
        """测试生成部分数据的摘要"""
        data = {
            "customer_name": "测试客户",
            "total_price": 50000.00
        }

        with patch.object(self.adapter, 'get_entity_data', return_value=data):
            summary = self.adapter.get_summary(self.entity_id)

        # 只包含存在的字段
        self.assertIn("客户: 测试客户", summary)
        self.assertIn("总价: ¥50,000.00", summary)
        self.assertNotIn("毛利率", summary)
        self.assertNotIn("交期", summary)

    def test_get_summary_no_data(self):
        """测试生成空数据的摘要"""
        with patch.object(self.adapter, 'get_entity_data', return_value={}):
            summary = self.adapter.get_summary(self.entity_id)

        # 应返回空字符串
        self.assertEqual(summary, "")

    def test_get_summary_zero_gross_margin(self):
        """测试毛利率为0的情况"""
        data = {
            "customer_name": "测试客户",
            "gross_margin": 0.0
        }

        with patch.object(self.adapter, 'get_entity_data', return_value=data):
            summary = self.adapter.get_summary(self.entity_id)

        # 毛利率为0也应该显示
        self.assertIn("毛利率: 0.0%", summary)

    # ========== validate_submit() 测试 ==========

    def test_validate_submit_success_from_draft(self):
        """测试从草稿状态成功验证提交"""
        mock_version = self._create_mock_version()
        mock_quote = self._create_mock_quote(status="DRAFT")
        mock_quote.current_version = mock_version

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_submit_success_from_rejected(self):
        """测试从驳回状态成功验证提交"""
        mock_version = self._create_mock_version()
        mock_quote = self._create_mock_quote(status="REJECTED")
        mock_quote.current_version = mock_version

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_submit_quote_not_found(self):
        """测试验证不存在的报价"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "报价不存在")

    def test_validate_submit_invalid_status(self):
        """测试无效状态下提交"""
        mock_quote = self._create_mock_quote(status="APPROVED")
        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertIn("不允许提交审批", error)

    def test_validate_submit_no_version(self):
        """测试没有任何版本"""
        mock_quote = self._create_mock_quote(status="DRAFT")
        mock_quote.current_version = None

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Quote:
                mock_query.filter.return_value.first.return_value = mock_quote
            elif model == QuoteVersion:
                mock_query.filter.return_value.count.return_value = 0
            return mock_query

        self.db.query.side_effect = query_side_effect

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "报价未添加任何版本，无法提交审批")

    def test_validate_submit_has_versions_but_no_current(self):
        """测试有版本但没有current_version（应该通过）"""
        mock_quote = self._create_mock_quote(status="DRAFT")
        mock_quote.current_version = None

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Quote:
                mock_query.filter.return_value.first.return_value = mock_quote
            elif model == QuoteVersion:
                # 有1个版本
                mock_query.filter.return_value.count.return_value = 1
            return mock_query

        self.db.query.side_effect = query_side_effect

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    # ========== submit_for_approval() 测试 ==========

    def test_submit_for_approval_success(self):
        """测试成功提交审批"""
        mock_version = self._create_mock_version(
            id=100,
            quote_id=1,
            quote_code="QT-2024-001",
            quote_total=Decimal("100000.00"),
            margin_percent=Decimal("30.0"),
            status="DRAFT"
        )
        mock_version.approval_instance_id = None

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 200
        mock_instance.status = "PENDING"

        # Mock WorkflowEngine
        with patch('app.services.approval_engine.workflow_engine.WorkflowEngine') as MockEngine:
            mock_engine = MockEngine.return_value
            mock_engine.create_instance.return_value = mock_instance

            result = self.adapter.submit_for_approval(
                quote_version=mock_version,
                initiator_id=10,
                title="测试报价审批",
                summary="测试摘要"
            )

            # 验证WorkflowEngine被正确调用
            MockEngine.assert_called_once_with(self.db)
            mock_engine.create_instance.assert_called_once()
            
            call_kwargs = mock_engine.create_instance.call_args[1]
            self.assertEqual(call_kwargs["flow_code"], "SALES_QUOTE")
            self.assertEqual(call_kwargs["business_type"], "SALES_QUOTE")
            self.assertEqual(call_kwargs["business_id"], 100)
            self.assertEqual(call_kwargs["submitted_by"], 10)

            # 验证返回实例
            self.assertEqual(result, mock_instance)

            # 验证报价版本被更新
            self.assertEqual(mock_version.approval_instance_id, 200)
            self.assertEqual(mock_version.approval_status, "PENDING")
            self.db.add.assert_called_with(mock_version)
            self.db.commit.assert_called_once()

    def test_submit_for_approval_already_submitted(self):
        """测试已经提交过的报价"""
        mock_version = self._create_mock_version()
        mock_version.approval_instance_id = 999

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 999

        self.db.query.return_value.filter.return_value.first.return_value = mock_instance

        with patch('app.services.approval_engine.adapters.quote.logger') as mock_logger:
            result = self.adapter.submit_for_approval(
                quote_version=mock_version,
                initiator_id=10
            )

            # 验证记录警告
            mock_logger.warning.assert_called_once()
            
            # 验证返回现有实例
            self.assertEqual(result, mock_instance)

    def test_submit_for_approval_default_title_summary(self):
        """测试使用默认标题和摘要"""
        mock_version = self._create_mock_version(quote_code="QT-2024-002")
        mock_version.approval_instance_id = None

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 300

        with patch('app.services.approval_engine.workflow_engine.WorkflowEngine') as MockEngine:
            mock_engine = MockEngine.return_value
            mock_engine.create_instance.return_value = mock_instance

            self.adapter.submit_for_approval(
                quote_version=mock_version,
                initiator_id=10
            )

            # 验证使用默认标题
            call_kwargs = mock_engine.create_instance.call_args[1]
            self.assertEqual(call_kwargs["business_title"], "QT-2024-002")

    # ========== create_quote_approval() 测试 ==========

    def test_create_quote_approval_new(self):
        """测试创建新的报价审批记录"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.node_name = "销售经理审批"
        mock_task.assignee_id = 50

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 100

        mock_user = MagicMock(spec=User)
        mock_user.real_name = "李四"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == QuoteApproval:
                mock_query.filter.return_value.first.return_value = None
            elif model == User:
                mock_query.filter.return_value.first.return_value = mock_user
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.create_quote_approval(mock_instance, mock_task)

        # 验证创建新记录
        self.assertIsNotNone(result)
        self.assertEqual(result.quote_version_id, 100)
        self.assertEqual(result.approval_level, 1)
        self.assertEqual(result.approval_role, "销售经理审批")
        self.assertEqual(result.approver_id, 50)
        self.assertEqual(result.approver_name, "李四")
        self.assertEqual(result.status, "PENDING")
        self.assertIsNone(result.approval_result)

        self.db.add.assert_called_once_with(result)

    def test_create_quote_approval_existing(self):
        """测试创建已存在的审批记录"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 100

        mock_existing = MagicMock(spec=QuoteApproval)

        self.db.query.return_value.filter.return_value.first.return_value = mock_existing

        result = self.adapter.create_quote_approval(mock_instance, mock_task)

        # 返回现有记录
        self.assertEqual(result, mock_existing)
        self.db.add.assert_not_called()

    def test_create_quote_approval_no_assignee(self):
        """测试创建无审批人的记录"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.node_name = "自动审批"
        mock_task.assignee_id = None

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 100

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == QuoteApproval:
                mock_query.filter.return_value.first.return_value = None
            elif model == User:
                mock_query.filter.return_value.first.return_value = None
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.create_quote_approval(mock_instance, mock_task)

        # 验证创建记录，审批人字段为空
        self.assertIsNone(result.approver_id)
        self.assertEqual(result.approver_name, "")

    # ========== update_quote_approval_from_action() 测试 ==========

    def test_update_quote_approval_approve(self):
        """测试更新审批记录为通过"""
        mock_approval = MagicMock(spec=QuoteApproval)

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = MagicMock(spec=ApprovalInstance)
        mock_task.instance.entity_id = 100

        self.db.query.return_value.filter.return_value.first.return_value = mock_approval

        with patch('app.services.approval_engine.adapters.quote.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 20, 14, 30, 0)
            mock_datetime.now.return_value = mock_now

            result = self.adapter.update_quote_approval_from_action(
                task=mock_task,
                action="APPROVE",
                comment="同意报价"
            )

            # 验证更新
            self.assertEqual(result.approval_result, "APPROVED")
            self.assertEqual(result.approval_opinion, "同意报价")
            self.assertEqual(result.status, "APPROVED")
            self.assertEqual(result.approved_at, mock_now)

            self.db.add.assert_called_once_with(mock_approval)
            self.db.commit.assert_called_once()

    def test_update_quote_approval_reject(self):
        """测试更新审批记录为驳回"""
        mock_approval = MagicMock(spec=QuoteApproval)

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = MagicMock(spec=ApprovalInstance)
        mock_task.instance.entity_id = 100

        self.db.query.return_value.filter.return_value.first.return_value = mock_approval

        with patch('app.services.approval_engine.adapters.quote.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 20, 15, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = self.adapter.update_quote_approval_from_action(
                task=mock_task,
                action="REJECT",
                comment="价格过高"
            )

            # 验证更新
            self.assertEqual(result.approval_result, "REJECTED")
            self.assertEqual(result.approval_opinion, "价格过高")
            self.assertEqual(result.status, "REJECTED")
            self.assertEqual(result.approved_at, mock_now)

    def test_update_quote_approval_not_found(self):
        """测试更新不存在的审批记录"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = MagicMock(spec=ApprovalInstance)
        mock_task.instance.entity_id = 100

        self.db.query.return_value.filter.return_value.first.return_value = None

        with patch('app.services.approval_engine.adapters.quote.logger') as mock_logger:
            result = self.adapter.update_quote_approval_from_action(
                task=mock_task,
                action="APPROVE"
            )

            # 验证记录警告
            mock_logger.warning.assert_called_once()
            
            # 返回None
            self.assertIsNone(result)
            self.db.commit.assert_not_called()

    def test_update_quote_approval_without_comment(self):
        """测试无意见的审批更新"""
        mock_approval = MagicMock(spec=QuoteApproval)

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = MagicMock(spec=ApprovalInstance)
        mock_task.instance.entity_id = 100

        self.db.query.return_value.filter.return_value.first.return_value = mock_approval

        with patch('app.services.approval_engine.adapters.quote.datetime'):
            result = self.adapter.update_quote_approval_from_action(
                task=mock_task,
                action="APPROVE",
                comment=None
            )

            # 验证意见为None
            self.assertEqual(result.approval_opinion, None)

    # ========== 辅助方法 ==========

    def _create_mock_quote(self, **kwargs):
        """创建模拟报价对象"""
        mock_quote = MagicMock(spec=Quote)
        
        # 设置默认值
        defaults = {
            'id': self.entity_id,
            'quote_code': 'QT-TEST-001',
            'status': 'DRAFT',
            'customer_id': None,
            'owner_id': None,
            'current_version': None,
        }
        
        # 合并自定义值
        defaults.update(kwargs)
        
        # 设置属性
        for key, value in defaults.items():
            setattr(mock_quote, key, value)
        
        # 设置默认的customer和owner为None
        if not hasattr(mock_quote, 'customer'):
            mock_quote.customer = None
        if not hasattr(mock_quote, 'owner'):
            mock_quote.owner = None
        
        return mock_quote

    def _create_mock_version(self, **kwargs):
        """创建模拟报价版本对象"""
        mock_version = MagicMock(spec=QuoteVersion)
        
        # 设置默认值
        defaults = {
            'id': 1,
            'quote_id': self.entity_id,
            'version_no': 1,
            'quote_code': 'QT-TEST-001',
            'total_price': Decimal("100000.00"),
            'cost_total': Decimal("70000.00"),
            'gross_margin': Decimal("0.3"),
            'lead_time_days': 30,
            'delivery_date': None,
            'quote_total': Decimal("100000.00"),
            'margin_percent': Decimal("30.0"),
            'status': 'DRAFT',
            'approval_instance_id': None,
            'approval_status': None,
        }
        
        # 合并自定义值
        defaults.update(kwargs)
        
        # 设置属性
        for key, value in defaults.items():
            setattr(mock_version, key, value)
        
        return mock_version

    def _setup_basic_query(self, mock_quote):
        """设置基础查询返回"""
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Quote:
                mock_query.filter.return_value.first.return_value = mock_quote
            elif model == QuoteVersion:
                # 如果没有 current_version，QuoteVersion 查询应返回 None
                mock_query.filter.return_value.order_by.return_value.first.return_value = None
            return mock_query

        self.db.query.side_effect = query_side_effect


class TestAdapterEntityType(unittest.TestCase):
    """测试适配器类属性"""

    def test_entity_type(self):
        """测试entity_type类属性"""
        self.assertEqual(QuoteApprovalAdapter.entity_type, "QUOTE")


if __name__ == '__main__':
    unittest.main()

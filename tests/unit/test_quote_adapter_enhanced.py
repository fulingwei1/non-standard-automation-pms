# -*- coding: utf-8 -*-
"""
报价审批适配器单元测试

测试 QuoteApprovalAdapter 的所有核心方法和边界条件
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter


class TestQuoteApprovalAdapter(unittest.TestCase):
    """QuoteApprovalAdapter 单元测试"""

    def setUp(self):
        """测试前设置"""
        self.db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.db)

    def tearDown(self):
        """测试后清理"""
        self.db.reset_mock()

    # ========== 初始化测试 ========== #

    def test_init(self):
        """测试适配器初始化"""
        adapter = QuoteApprovalAdapter(self.db)
        self.assertEqual(adapter.db, self.db)
        self.assertEqual(adapter.entity_type, "QUOTE")

    def test_entity_type_is_quote(self):
        """测试实体类型为 QUOTE"""
        self.assertEqual(QuoteApprovalAdapter.entity_type, "QUOTE")

    # ========== get_entity 测试 ========== #

    def test_get_entity_success(self):
        """测试成功获取报价实体"""
        mock_quote = Mock()
        mock_quote.id = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        result = self.adapter.get_entity(1)

        self.assertEqual(result, mock_quote)
        self.db.query.assert_called_once()

    def test_get_entity_not_found(self):
        """测试获取不存在的报价实体"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(999)

        self.assertIsNone(result)

    def test_get_entity_with_zero_id(self):
        """测试获取ID为0的实体"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(0)

        self.assertIsNone(result)

    # ========== get_entity_data 测试 ========== #

    def test_get_entity_data_complete(self):
        """测试获取完整报价数据"""
        mock_customer = Mock()
        mock_customer.name = "测试客户"

        mock_owner = Mock()
        mock_owner.name = "张三"

        mock_version = Mock()
        mock_version.version_no = 1
        mock_version.total_price = Decimal("10000.00")
        mock_version.cost_total = Decimal("7000.00")
        mock_version.gross_margin = Decimal("0.30")  # 30% 小数形式
        mock_version.lead_time_days = 15
        mock_version.delivery_date = datetime(2024, 3, 15)

        mock_quote = Mock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q2024001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = 1
        mock_quote.customer = mock_customer
        mock_quote.owner_id = 1
        mock_quote.owner = mock_owner
        mock_quote.current_version = mock_version

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        data = self.adapter.get_entity_data(1)

        self.assertEqual(data["quote_code"], "Q2024001")
        self.assertEqual(data["status"], "DRAFT")
        self.assertEqual(data["customer_name"], "测试客户")
        self.assertEqual(data["owner_name"], "张三")
        self.assertEqual(data["version_no"], 1)
        self.assertEqual(data["total_price"], 10000.00)
        self.assertEqual(data["cost_total"], 7000.00)
        self.assertEqual(data["gross_margin"], 30.0)  # 转换为百分比
        self.assertEqual(data["lead_time_days"], 15)
        self.assertTrue(data["delivery_date"].startswith("2024-03-15"))  # 日期格式可能包含时间

    def test_get_entity_data_gross_margin_already_percentage(self):
        """测试毛利率已经是百分比形式"""
        mock_version = Mock()
        mock_version.version_no = 1
        mock_version.total_price = Decimal("10000.00")
        mock_version.cost_total = Decimal("7000.00")
        mock_version.gross_margin = Decimal("30")  # 已经是百分比
        mock_version.lead_time_days = 15
        mock_version.delivery_date = None

        mock_quote = Mock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q2024001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = None
        mock_quote.customer = None
        mock_quote.owner_id = None
        mock_quote.owner = None
        mock_quote.current_version = mock_version

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        data = self.adapter.get_entity_data(1)

        self.assertEqual(data["gross_margin"], 30.0)  # 保持不变

    def test_get_entity_data_gross_margin_none(self):
        """测试毛利率为None"""
        mock_version = Mock()
        mock_version.version_no = 1
        mock_version.total_price = Decimal("10000.00")
        mock_version.cost_total = Decimal("7000.00")
        mock_version.gross_margin = None
        mock_version.lead_time_days = 15
        mock_version.delivery_date = None

        mock_quote = Mock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q2024001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = None
        mock_quote.customer = None
        mock_quote.owner_id = None
        mock_quote.owner = None
        mock_quote.current_version = mock_version

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        data = self.adapter.get_entity_data(1)

        self.assertIsNone(data["gross_margin"])

    def test_get_entity_data_no_current_version_fallback(self):
        """测试没有当前版本时回退到最新版本"""
        mock_version = Mock()
        mock_version.version_no = 2
        mock_version.total_price = Decimal("10000.00")
        mock_version.cost_total = None
        mock_version.gross_margin = Decimal("0.30")
        mock_version.lead_time_days = None
        mock_version.delivery_date = None

        mock_quote = Mock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q2024001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = None
        mock_quote.customer = None
        mock_quote.owner_id = None
        mock_quote.owner = None
        mock_quote.current_version = None

        # 模拟两次查询：第一次获取 quote，第二次获取最新版本
        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_quote,
            None,
        ]
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_version
        )

        data = self.adapter.get_entity_data(1)

        self.assertEqual(data["version_no"], 2)
        self.assertEqual(data["cost_total"], 0)  # None 转为 0

    def test_get_entity_data_entity_not_found(self):
        """测试实体不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        data = self.adapter.get_entity_data(999)

        self.assertEqual(data, {})

    def test_get_entity_data_no_version(self):
        """测试完全没有版本"""
        mock_quote = Mock()
        mock_quote.id = 1
        mock_quote.quote_code = "Q2024001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = None
        mock_quote.customer = None
        mock_quote.owner_id = None
        mock_quote.owner = None
        mock_quote.current_version = None

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_quote,
            None,
        ]
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        data = self.adapter.get_entity_data(1)

        self.assertEqual(data["quote_code"], "Q2024001")
        self.assertNotIn("version_no", data)
        self.assertNotIn("total_price", data)

    # ========== 状态回调测试 ========== #

    def test_on_submit(self):
        """测试提交审批回调"""
        mock_quote = Mock()
        mock_instance = Mock()

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        self.adapter.on_submit(1, mock_instance)

        self.assertEqual(mock_quote.status, "PENDING_APPROVAL")
        self.db.flush.assert_called_once()

    def test_on_submit_entity_not_found(self):
        """测试提交时实体不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        mock_instance = Mock()

        self.adapter.on_submit(999, mock_instance)

        self.db.flush.assert_not_called()

    def test_on_approved(self):
        """测试审批通过回调"""
        mock_quote = Mock()
        mock_instance = Mock()

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        self.adapter.on_approved(1, mock_instance)

        self.assertEqual(mock_quote.status, "APPROVED")
        self.db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回回调"""
        mock_quote = Mock()
        mock_instance = Mock()

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        self.adapter.on_rejected(1, mock_instance)

        self.assertEqual(mock_quote.status, "REJECTED")
        self.db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试撤回审批回调"""
        mock_quote = Mock()
        mock_instance = Mock()

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        self.adapter.on_withdrawn(1, mock_instance)

        self.assertEqual(mock_quote.status, "DRAFT")
        self.db.flush.assert_called_once()

    # ========== 标题和摘要测试 ========== #

    def test_get_title_with_customer(self):
        """测试生成审批标题（有客户）"""
        mock_customer = Mock()
        mock_customer.name = "测试客户"

        mock_quote = Mock()
        mock_quote.quote_code = "Q2024001"
        mock_quote.customer = mock_customer

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        title = self.adapter.get_title(1)

        self.assertEqual(title, "报价审批 - Q2024001 (测试客户)")

    def test_get_title_without_customer(self):
        """测试生成审批标题（无客户）"""
        mock_quote = Mock()
        mock_quote.quote_code = "Q2024001"
        mock_quote.customer = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        title = self.adapter.get_title(1)

        self.assertEqual(title, "报价审批 - Q2024001 (未知客户)")

    def test_get_title_entity_not_found(self):
        """测试生成标题时实体不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        title = self.adapter.get_title(999)

        self.assertEqual(title, "报价审批 - #999")

    def test_get_summary_complete(self):
        """测试生成完整摘要"""
        with patch.object(
            self.adapter,
            "get_entity_data",
            return_value={
                "customer_name": "测试客户",
                "total_price": 10000.00,
                "gross_margin": 30.0,
                "lead_time_days": 15,
            },
        ):
            summary = self.adapter.get_summary(1)

            self.assertIn("客户: 测试客户", summary)
            self.assertIn("总价: ¥10,000.00", summary)
            self.assertIn("毛利率: 30.0%", summary)
            self.assertIn("交期: 15天", summary)

    def test_get_summary_partial(self):
        """测试生成部分摘要"""
        with patch.object(
            self.adapter,
            "get_entity_data",
            return_value={
                "customer_name": "测试客户",
                "total_price": 5000.00,
            },
        ):
            summary = self.adapter.get_summary(1)

            self.assertIn("客户: 测试客户", summary)
            self.assertIn("总价: ¥5,000.00", summary)
            self.assertNotIn("毛利率", summary)

    def test_get_summary_empty_data(self):
        """测试数据为空时生成摘要"""
        with patch.object(self.adapter, "get_entity_data", return_value={}):
            summary = self.adapter.get_summary(1)

            self.assertEqual(summary, "")

    # ========== validate_submit 测试 ========== #

    def test_validate_submit_success_draft(self):
        """测试草稿状态可以提交"""
        mock_version = Mock()
        mock_quote = Mock()
        mock_quote.status = "DRAFT"
        mock_quote.current_version = mock_version

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        valid, msg = self.adapter.validate_submit(1)

        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_validate_submit_success_rejected(self):
        """测试驳回状态可以提交"""
        mock_version = Mock()
        mock_quote = Mock()
        mock_quote.status = "REJECTED"
        mock_quote.current_version = mock_version

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        valid, msg = self.adapter.validate_submit(1)

        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_validate_submit_entity_not_found(self):
        """测试实体不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        valid, msg = self.adapter.validate_submit(999)

        self.assertFalse(valid)
        self.assertEqual(msg, "报价不存在")

    def test_validate_submit_invalid_status(self):
        """测试无效状态不能提交"""
        mock_quote = Mock()
        mock_quote.status = "APPROVED"

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote

        valid, msg = self.adapter.validate_submit(1)

        self.assertFalse(valid)
        self.assertIn("当前状态(APPROVED)不允许提交审批", msg)

    def test_validate_submit_no_version(self):
        """测试没有版本不能提交"""
        mock_quote = Mock()
        mock_quote.status = "DRAFT"
        mock_quote.current_version = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_quote
        self.db.query.return_value.filter.return_value.count.return_value = 0

        valid, msg = self.adapter.validate_submit(1)

        self.assertFalse(valid)
        self.assertEqual(msg, "报价未添加任何版本，无法提交审批")

    # ========== submit_for_approval 测试 ========== #

    @patch("app.services.approval_engine.workflow_engine.WorkflowEngine")
    def test_submit_for_approval_success(self, mock_workflow_engine_class):
        """测试成功提交审批"""
        mock_version = Mock()
        mock_version.id = 1
        mock_version.quote_id = 10
        mock_version.quote_code = "Q2024001"
        mock_version.quote_total = Decimal("10000.00")
        mock_version.margin_percent = Decimal("30.00")
        mock_version.status = "DRAFT"
        mock_version.approval_instance_id = None

        mock_instance = Mock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"

        mock_engine = Mock()
        mock_engine.create_instance.return_value = mock_instance
        mock_workflow_engine_class.return_value = mock_engine

        result = self.adapter.submit_for_approval(mock_version, initiator_id=1)

        self.assertEqual(result, mock_instance)
        self.assertEqual(mock_version.approval_instance_id, 100)
        self.assertEqual(mock_version.approval_status, "PENDING")
        self.db.add.assert_called_once_with(mock_version)
        self.db.commit.assert_called_once()

    @patch("app.services.approval_engine.workflow_engine.WorkflowEngine")
    def test_submit_for_approval_already_submitted(self, mock_workflow_engine_class):
        """测试重复提交审批"""
        mock_version = Mock()
        mock_version.approval_instance_id = 100
        mock_version.quote_code = "Q2024001"

        mock_instance = Mock()
        self.db.query.return_value.filter.return_value.first.return_value = (
            mock_instance
        )

        result = self.adapter.submit_for_approval(mock_version, initiator_id=1)

        self.assertEqual(result, mock_instance)
        mock_workflow_engine_class.assert_not_called()

    @patch("app.services.approval_engine.workflow_engine.WorkflowEngine")
    def test_submit_for_approval_with_custom_params(self, mock_workflow_engine_class):
        """测试带自定义参数提交审批"""
        mock_version = Mock()
        mock_version.id = 1
        mock_version.quote_id = 10
        mock_version.quote_code = "Q2024001"
        mock_version.quote_total = Decimal("10000.00")
        mock_version.margin_percent = Decimal("30.00")
        mock_version.status = "DRAFT"
        mock_version.approval_instance_id = None

        mock_instance = Mock()
        mock_instance.id = 100
        mock_instance.status = "PENDING"

        mock_engine = Mock()
        mock_engine.create_instance.return_value = mock_instance
        mock_workflow_engine_class.return_value = mock_engine

        result = self.adapter.submit_for_approval(
            mock_version,
            initiator_id=1,
            title="自定义标题",
            summary="自定义摘要",
            urgency="HIGH",
            cc_user_ids=[2, 3],
        )

        self.assertEqual(result, mock_instance)
        mock_engine.create_instance.assert_called_once()

    # ========== create_quote_approval 测试 ========== #
    
    @unittest.skip("QuoteApproval model not implemented yet")
    def test_create_quote_approval_success(self):
        """测试成功创建报价审批记录 (跳过 - 模型未实现)"""
        pass

    @unittest.skip("QuoteApproval model not implemented yet")
    def test_create_quote_approval_already_exists(self):
        """测试审批记录已存在 (跳过 - 模型未实现)"""
        pass

    # ========== update_quote_approval_from_action 测试 ========== #

    @unittest.skip("QuoteApproval model not implemented yet")
    def test_update_quote_approval_approve(self):
        """测试批准操作更新审批记录 (跳过 - 模型未实现)"""
        pass

    @unittest.skip("QuoteApproval model not implemented yet")
    def test_update_quote_approval_reject(self):
        """测试拒绝操作更新审批记录 (跳过 - 模型未实现)"""
        pass

    @unittest.skip("QuoteApproval model not implemented yet")
    def test_update_quote_approval_not_found(self):
        """测试审批记录不存在 (跳过 - 模型未实现)"""
        pass


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
报价审批适配器单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 所有测试必须通过
6. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime, date

from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.sales.quotes import Quote, QuoteVersion


class TestQuoteApprovalAdapter(unittest.TestCase):
    """测试 QuoteApprovalAdapter 核心方法"""

    def setUp(self):
        """每个测试前的准备"""
        self.mock_db = MagicMock()
        self.adapter = QuoteApprovalAdapter(self.mock_db)

    # ========== get_entity() 测试 ==========

    def test_get_entity_success(self):
        """测试获取报价实体 - 成功"""
        # 创建mock报价
        mock_quote = MagicMock(spec=Quote)
        mock_quote.id = 1
        mock_quote.quote_code = "QT202401001"
        
        # 配置查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.adapter.get_entity(1)
        
        self.assertEqual(result, mock_quote)
        self.mock_db.query.assert_called_once()

    def test_get_entity_not_found(self):
        """测试获取报价实体 - 未找到"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_entity(999)
        
        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_with_current_version(self):
        """测试获取报价数据 - 有当前版本"""
        # 创建mock customer和owner
        mock_customer = MagicMock()
        mock_customer.name = "测试客户"
        
        mock_owner = MagicMock()
        mock_owner.name = "张三"
        
        # 创建mock版本
        mock_version = MagicMock(spec=QuoteVersion)
        mock_version.version_no = "v1.0"
        mock_version.total_price = Decimal("100000")
        mock_version.cost_total = Decimal("80000")
        mock_version.gross_margin = Decimal("0.2")  # 20%
        mock_version.lead_time_days = 30
        mock_version.delivery_date = date(2024, 3, 1)
        
        # 创建mock报价
        mock_quote = MagicMock(spec=Quote)
        mock_quote.id = 1
        mock_quote.quote_code = "QT202401001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = 1
        mock_quote.customer = mock_customer
        mock_quote.owner_id = 2
        mock_quote.owner = mock_owner
        mock_quote.current_version = mock_version
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.adapter.get_entity_data(1)
        
        self.assertEqual(result["quote_code"], "QT202401001")
        self.assertEqual(result["customer_name"], "测试客户")
        self.assertEqual(result["owner_name"], "张三")
        self.assertEqual(result["total_price"], 100000.0)
        self.assertEqual(result["cost_total"], 80000.0)
        self.assertEqual(result["gross_margin"], 20.0)  # 转换为百分比
        self.assertEqual(result["lead_time_days"], 30)
        self.assertEqual(result["delivery_date"], "2024-03-01")

    def test_get_entity_data_gross_margin_already_percentage(self):
        """测试获取报价数据 - 毛利率已经是百分比形式"""
        mock_version = MagicMock(spec=QuoteVersion)
        mock_version.version_no = "v1.0"
        mock_version.total_price = Decimal("100000")
        mock_version.cost_total = Decimal("80000")
        mock_version.gross_margin = Decimal("20")  # 已经是百分比
        mock_version.lead_time_days = 30
        mock_version.delivery_date = None
        
        mock_quote = MagicMock(spec=Quote)
        mock_quote.quote_code = "QT202401001"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = 1
        mock_quote.customer = MagicMock(name="客户A")
        mock_quote.owner_id = 2
        mock_quote.owner = MagicMock(name="员工A")
        mock_quote.current_version = mock_version
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.adapter.get_entity_data(1)
        
        self.assertEqual(result["gross_margin"], 20.0)  # 保持不变

    def test_get_entity_data_no_current_version(self):
        """测试获取报价数据 - 无当前版本但有历史版本"""
        mock_version = MagicMock(spec=QuoteVersion)
        mock_version.version_no = "v1.0"
        mock_version.total_price = Decimal("50000")
        mock_version.cost_total = Decimal("40000")
        mock_version.gross_margin = Decimal("0.25")
        mock_version.lead_time_days = 15
        mock_version.delivery_date = None
        
        mock_quote = MagicMock(spec=Quote)
        mock_quote.id = 1
        mock_quote.quote_code = "QT202401002"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = 1
        mock_quote.customer = MagicMock(name="客户B")
        mock_quote.owner_id = 2
        mock_quote.owner = MagicMock(name="员工B")
        mock_quote.current_version = None  # 无当前版本
        
        # 配置查询历史版本
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_quote,  # 第一次查询返回quote
        ]
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_version
        
        result = self.adapter.get_entity_data(1)
        
        self.assertEqual(result["version_no"], "v1.0")
        self.assertEqual(result["gross_margin"], 25.0)

    def test_get_entity_data_quote_not_found(self):
        """测试获取报价数据 - 报价不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_entity_data(999)
        
        self.assertEqual(result, {})

    def test_get_entity_data_no_customer(self):
        """测试获取报价数据 - 无客户"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.quote_code = "QT202401003"
        mock_quote.status = "DRAFT"
        mock_quote.customer_id = None
        mock_quote.customer = None
        mock_quote.owner_id = 2
        mock_quote.owner = MagicMock(name="员工C")
        mock_quote.current_version = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = self.adapter.get_entity_data(1)
        
        self.assertIsNone(result["customer_name"])

    # ========== on_submit() 测试 ==========

    def test_on_submit_success(self):
        """测试提交审批回调 - 成功"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.status = "DRAFT"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        self.adapter.on_submit(1, mock_instance)
        
        self.assertEqual(mock_quote.status, "PENDING_APPROVAL")
        self.mock_db.flush.assert_called_once()

    def test_on_submit_quote_not_found(self):
        """测试提交审批回调 - 报价不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        # 不应抛出异常
        self.adapter.on_submit(999, mock_instance)
        
        self.mock_db.flush.assert_not_called()

    # ========== on_approved() 测试 ==========

    def test_on_approved_success(self):
        """测试审批通过回调 - 成功"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.status = "PENDING_APPROVAL"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        self.adapter.on_approved(1, mock_instance)
        
        self.assertEqual(mock_quote.status, "APPROVED")
        self.mock_db.flush.assert_called_once()

    # ========== on_rejected() 测试 ==========

    def test_on_rejected_success(self):
        """测试审批驳回回调 - 成功"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.status = "PENDING_APPROVAL"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        self.adapter.on_rejected(1, mock_instance)
        
        self.assertEqual(mock_quote.status, "REJECTED")
        self.mock_db.flush.assert_called_once()

    # ========== on_withdrawn() 测试 ==========

    def test_on_withdrawn_success(self):
        """测试撤回审批回调 - 成功"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.status = "PENDING_APPROVAL"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        self.adapter.on_withdrawn(1, mock_instance)
        
        self.assertEqual(mock_quote.status, "DRAFT")
        self.mock_db.flush.assert_called_once()

    # ========== get_title() 测试 ==========

    def test_get_title_success(self):
        """测试生成审批标题 - 成功"""
        mock_customer = MagicMock()
        mock_customer.name = "华为技术有限公司"
        
        mock_quote = MagicMock(spec=Quote)
        mock_quote.quote_code = "QT202401001"
        mock_quote.customer = mock_customer
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.adapter.get_title(1)
        
        self.assertEqual(result, "报价审批 - QT202401001 (华为技术有限公司)")

    def test_get_title_no_customer(self):
        """测试生成审批标题 - 无客户"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.quote_code = "QT202401002"
        mock_quote.customer = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.adapter.get_title(1)
        
        self.assertEqual(result, "报价审批 - QT202401002 (未知客户)")

    def test_get_title_quote_not_found(self):
        """测试生成审批标题 - 报价不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_title(999)
        
        self.assertEqual(result, "报价审批 - #999")

    # ========== get_summary() 测试 ==========

    def test_get_summary_full_data(self):
        """测试生成审批摘要 - 完整数据"""
        mock_customer = MagicMock()
        mock_customer.name = "客户A"
        
        mock_version = MagicMock()
        mock_version.version_no = "v1.0"
        mock_version.total_price = Decimal("100000")
        mock_version.cost_total = Decimal("80000")
        mock_version.gross_margin = Decimal("0.2")
        mock_version.lead_time_days = 30
        mock_version.delivery_date = date(2024, 3, 1)
        
        mock_quote = MagicMock(spec=Quote)
        mock_quote.quote_code = "QT202401001"
        mock_quote.customer = mock_customer
        mock_quote.current_version = mock_version
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.adapter.get_summary(1)
        
        self.assertIn("客户: 客户A", result)
        self.assertIn("总价: ¥100,000.00", result)
        self.assertIn("毛利率: 20.0%", result)
        self.assertIn("交期: 30天", result)

    def test_get_summary_partial_data(self):
        """测试生成审批摘要 - 部分数据"""
        mock_customer = MagicMock()
        mock_customer.name = "客户B"
        
        mock_version = MagicMock()
        mock_version.version_no = "v1.0"
        mock_version.total_price = Decimal("50000")
        mock_version.cost_total = None
        mock_version.gross_margin = None
        mock_version.lead_time_days = None
        mock_version.delivery_date = None
        
        mock_quote = MagicMock(spec=Quote)
        mock_quote.quote_code = "QT202401002"
        mock_quote.customer = mock_customer
        mock_quote.current_version = mock_version
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.adapter.get_summary(1)
        
        self.assertIn("客户: 客户B", result)
        self.assertIn("总价: ¥50,000.00", result)
        self.assertNotIn("毛利率", result)
        self.assertNotIn("交期", result)

    def test_get_summary_no_data(self):
        """测试生成审批摘要 - 无数据"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.get_summary(999)
        
        self.assertEqual(result, "")

    # ========== validate_submit() 测试 ==========

    def test_validate_submit_success(self):
        """测试验证提交 - 成功"""
        mock_version = MagicMock(spec=QuoteVersion)
        
        mock_quote = MagicMock(spec=Quote)
        mock_quote.status = "DRAFT"
        mock_quote.current_version = mock_version
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        valid, msg = self.adapter.validate_submit(1)
        
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_validate_submit_from_rejected(self):
        """测试验证提交 - 从驳回状态提交"""
        mock_version = MagicMock(spec=QuoteVersion)
        
        mock_quote = MagicMock(spec=Quote)
        mock_quote.status = "REJECTED"
        mock_quote.current_version = mock_version
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        valid, msg = self.adapter.validate_submit(1)
        
        self.assertTrue(valid)

    def test_validate_submit_quote_not_found(self):
        """测试验证提交 - 报价不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        valid, msg = self.adapter.validate_submit(999)
        
        self.assertFalse(valid)
        self.assertEqual(msg, "报价不存在")

    def test_validate_submit_invalid_status(self):
        """测试验证提交 - 状态不允许提交"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.status = "APPROVED"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        valid, msg = self.adapter.validate_submit(1)
        
        self.assertFalse(valid)
        self.assertIn("当前状态", msg)

    def test_validate_submit_no_version(self):
        """测试验证提交 - 无版本"""
        mock_quote = MagicMock(spec=Quote)
        mock_quote.status = "DRAFT"
        mock_quote.current_version = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        valid, msg = self.adapter.validate_submit(1)
        
        self.assertFalse(valid)
        self.assertIn("未添加任何版本", msg)

    # ========== submit_for_approval() 测试 ==========

    @patch('app.services.approval_engine.workflow_engine.WorkflowEngine')
    def test_submit_for_approval_success(self, mock_workflow_engine_class):
        """测试提交审批 - 成功"""
        # 创建mock报价版本
        mock_quote_version = MagicMock()
        mock_quote_version.id = 1
        mock_quote_version.quote_id = 10
        mock_quote_version.quote_code = "QT202401001"
        mock_quote_version.quote_total = Decimal("100000")
        mock_quote_version.margin_percent = Decimal("20")
        mock_quote_version.status = "DRAFT"
        mock_quote_version.approval_instance_id = None
        
        # 创建mock审批实例
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 100
        mock_instance.status = "PENDING"
        
        # 配置WorkflowEngine mock
        mock_engine = MagicMock()
        mock_engine.create_instance.return_value = mock_instance
        mock_workflow_engine_class.return_value = mock_engine
        
        result = self.adapter.submit_for_approval(
            quote_version=mock_quote_version,
            initiator_id=1,
            title="测试报价审批",
            summary="测试摘要",
            urgency="NORMAL"
        )
        
        self.assertEqual(result, mock_instance)
        self.assertEqual(mock_quote_version.approval_instance_id, 100)
        self.assertEqual(mock_quote_version.approval_status, "PENDING")
        self.mock_db.add.assert_called_with(mock_quote_version)
        self.mock_db.commit.assert_called_once()

    @patch('app.services.approval_engine.workflow_engine.WorkflowEngine')
    def test_submit_for_approval_already_submitted(self, mock_workflow_engine_class):
        """测试提交审批 - 已经提交过"""
        mock_quote_version = MagicMock()
        mock_quote_version.id = 1
        mock_quote_version.quote_code = "QT202401001"
        mock_quote_version.approval_instance_id = 100  # 已有审批实例
        
        # 创建已存在的审批实例
        mock_existing_instance = MagicMock(spec=ApprovalInstance)
        mock_existing_instance.id = 100
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_instance
        
        result = self.adapter.submit_for_approval(
            quote_version=mock_quote_version,
            initiator_id=1
        )
        
        self.assertEqual(result, mock_existing_instance)
        # 不应该创建新实例
        mock_workflow_engine_class.assert_not_called()

    # ========== create_quote_approval() 测试 ==========

    @patch('app.models.sales.technical_assessment.QuoteApproval')
    def test_create_quote_approval_new(self, mock_quote_approval_class):
        """测试创建报价审批记录 - 新建"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 1
        
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.node_name = "部门经理审批"
        mock_task.assignee_id = 10
        
        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.real_name = "李经理"
        
        # 配置查询
        self.mock_db.query.return_value.filter.side_effect = [
            MagicMock(first=MagicMock(return_value=None)),  # 无现有记录
            MagicMock(first=MagicMock(return_value=mock_user))  # 查询用户
        ]
        
        mock_approval = MagicMock()
        mock_quote_approval_class.return_value = mock_approval
        
        result = self.adapter.create_quote_approval(mock_instance, mock_task)
        
        self.assertEqual(result, mock_approval)
        self.mock_db.add.assert_called_with(mock_approval)

    @patch('app.models.sales.technical_assessment.QuoteApproval')
    def test_create_quote_approval_existing(self, mock_quote_approval_class):
        """测试创建报价审批记录 - 已存在"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 1
        
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        
        mock_existing_approval = MagicMock()
        
        # 配置查询返回已存在的记录
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_approval
        
        result = self.adapter.create_quote_approval(mock_instance, mock_task)
        
        self.assertEqual(result, mock_existing_approval)
        self.mock_db.add.assert_not_called()

    # ========== update_quote_approval_from_action() 测试 ==========

    @patch('app.models.sales.technical_assessment.QuoteApproval')
    @patch('app.services.approval_engine.adapters.quote.datetime')
    def test_update_quote_approval_approve(self, mock_datetime, mock_quote_approval_class):
        """测试更新审批记录 - 通过"""
        mock_now = datetime(2024, 1, 15, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 1
        
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = mock_instance
        
        mock_approval = MagicMock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_approval
        
        result = self.adapter.update_quote_approval_from_action(
            task=mock_task,
            action="APPROVE",
            comment="同意"
        )
        
        self.assertEqual(result, mock_approval)
        self.assertEqual(mock_approval.approval_result, "APPROVED")
        self.assertEqual(mock_approval.approval_opinion, "同意")
        self.assertEqual(mock_approval.status, "APPROVED")
        self.assertEqual(mock_approval.approved_at, mock_now)
        self.mock_db.add.assert_called_with(mock_approval)
        self.mock_db.commit.assert_called_once()

    @patch('app.models.sales.technical_assessment.QuoteApproval')
    @patch('app.services.approval_engine.adapters.quote.datetime')
    def test_update_quote_approval_reject(self, mock_datetime, mock_quote_approval_class):
        """测试更新审批记录 - 驳回"""
        mock_now = datetime(2024, 1, 15, 11, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 1
        
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = mock_instance
        
        mock_approval = MagicMock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_approval
        
        result = self.adapter.update_quote_approval_from_action(
            task=mock_task,
            action="REJECT",
            comment="不同意"
        )
        
        self.assertEqual(result, mock_approval)
        self.assertEqual(mock_approval.approval_result, "REJECTED")
        self.assertEqual(mock_approval.approval_opinion, "不同意")
        self.assertEqual(mock_approval.status, "REJECTED")
        self.assertEqual(mock_approval.approved_at, mock_now)

    @patch('app.models.sales.technical_assessment.QuoteApproval')
    def test_update_quote_approval_not_found(self, mock_quote_approval_class):
        """测试更新审批记录 - 记录不存在"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 1
        
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = mock_instance
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.adapter.update_quote_approval_from_action(
            task=mock_task,
            action="APPROVE"
        )
        
        self.assertIsNone(result)
        self.mock_db.commit.assert_not_called()

    # ========== 边界情况测试 ==========

    def test_gross_margin_none(self):
        """测试毛利率为None的情况"""
        mock_version = MagicMock()
        mock_version.version_no = "v1.0"
        mock_version.total_price = Decimal("100000")
        mock_version.cost_total = Decimal("80000")
        mock_version.gross_margin = None
        mock_version.lead_time_days = 30
        mock_version.delivery_date = None
        
        mock_quote = MagicMock(spec=Quote)
        mock_quote.quote_code = "QT202401001"
        mock_quote.customer = MagicMock(name="客户A")
        mock_quote.owner = MagicMock(name="员工A")
        mock_quote.current_version = mock_version
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = self.adapter.get_entity_data(1)
        
        self.assertIsNone(result["gross_margin"])

    def test_entity_type_attribute(self):
        """测试entity_type属性"""
        self.assertEqual(self.adapter.entity_type, "QUOTE")


if __name__ == "__main__":
    unittest.main()

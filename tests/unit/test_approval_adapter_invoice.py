# -*- coding: utf-8 -*-
"""
发票审批适配器单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率

参考: test_condition_parser_rewrite.py的mock策略
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
from app.models.sales.invoices import Invoice, InvoiceApproval
from app.models.approval.instance import ApprovalInstance
from app.models.approval.task import ApprovalTask
from app.models.user import User


class TestInvoiceApprovalAdapter(unittest.TestCase):
    """测试发票审批适配器"""

    def setUp(self):
        """每个测试前初始化"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        self.adapter = InvoiceApprovalAdapter(self.mock_db)

    # ========== get_entity() 测试 ==========

    def test_get_entity_found(self):
        """测试成功获取发票"""
        # 准备mock数据
        mock_invoice = Invoice(
            id=1,
            invoice_code="INV-2024-001",
            status="DRAFT"
        )
        
        # 配置mock查询链
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        # 执行
        result = self.adapter.get_entity(1)
        
        # 验证
        self.assertEqual(result, mock_invoice)
        self.mock_db.query.assert_called_once()

    def test_get_entity_not_found(self):
        """测试发票不存在"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        result = self.adapter.get_entity(999)
        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_complete(self):
        """测试获取完整发票数据"""
        # 创建完整的发票对象
        mock_contract = MagicMock()
        mock_contract.contract_code = "CNT-2024-001"
        
        mock_invoice = Invoice(
            id=1,
            invoice_code="INV-2024-001",
            status="DRAFT",
            invoice_type="VAT_SPECIAL",
            amount=Decimal("10000.00"),
            tax_rate=Decimal("0.13"),
            tax_amount=Decimal("1300.00"),
            total_amount=Decimal("11300.00"),
            contract_id=100,
            project_id=200,
            buyer_name="测试客户",
            buyer_tax_no="91110000000000001X",
            issue_date=date(2024, 1, 15),
            due_date=date(2024, 2, 15)
        )
        mock_invoice.contract = mock_contract
        
        # Mock查询
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        # 执行
        result = self.adapter.get_entity_data(1)
        
        # 验证
        self.assertEqual(result["invoice_code"], "INV-2024-001")
        self.assertEqual(result["status"], "DRAFT")
        self.assertEqual(result["invoice_type"], "VAT_SPECIAL")
        self.assertEqual(result["amount"], 10000.00)
        self.assertEqual(result["tax_rate"], 0.13)
        self.assertEqual(result["tax_amount"], 1300.00)
        self.assertEqual(result["total_amount"], 11300.00)
        self.assertEqual(result["contract_id"], 100)
        self.assertEqual(result["contract_code"], "CNT-2024-001")
        self.assertEqual(result["project_id"], 200)
        self.assertEqual(result["buyer_name"], "测试客户")
        self.assertEqual(result["buyer_tax_no"], "91110000000000001X")
        self.assertEqual(result["issue_date"], "2024-01-15")
        self.assertEqual(result["due_date"], "2024-02-15")

    def test_get_entity_data_minimal(self):
        """测试获取最小化发票数据（部分字段为None）"""
        mock_invoice = Invoice(
            id=1,
            invoice_code="INV-2024-002",
            status="DRAFT",
            invoice_type="ORDINARY",
            amount=None,
            tax_rate=None,
            tax_amount=None,
            total_amount=None,
            contract_id=None,
            project_id=None,
            buyer_name=None,
            buyer_tax_no=None,
            issue_date=None,
            due_date=None
        )
        mock_invoice.contract = None
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        result = self.adapter.get_entity_data(1)
        
        # 验证None值的处理
        self.assertEqual(result["amount"], 0)
        self.assertEqual(result["tax_rate"], 0)
        self.assertEqual(result["tax_amount"], 0)
        self.assertEqual(result["total_amount"], 0)
        self.assertIsNone(result["contract_code"])
        self.assertIsNone(result["issue_date"])
        self.assertIsNone(result["due_date"])

    def test_get_entity_data_not_found(self):
        """测试发票不存在时返回空字典"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        result = self.adapter.get_entity_data(999)
        self.assertEqual(result, {})

    # ========== 状态回调测试 ==========

    def test_on_submit(self):
        """测试提交审批回调"""
        mock_invoice = Invoice(id=1, status="DRAFT")
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        mock_instance = MagicMock()
        
        self.adapter.on_submit(1, mock_instance)
        
        # 验证状态已更新
        self.assertEqual(mock_invoice.status, "PENDING_APPROVAL")
        self.mock_db.flush.assert_called_once()

    def test_on_submit_invoice_not_found(self):
        """测试提交时发票不存在"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        mock_instance = MagicMock()
        
        # 不应该抛出异常
        self.adapter.on_submit(999, mock_instance)
        self.mock_db.flush.assert_not_called()

    def test_on_approved(self):
        """测试审批通过回调"""
        mock_invoice = Invoice(id=1, status="PENDING_APPROVAL")
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        mock_instance = MagicMock()
        
        self.adapter.on_approved(1, mock_instance)
        
        self.assertEqual(mock_invoice.status, "APPROVED")
        self.mock_db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回回调"""
        mock_invoice = Invoice(id=1, status="PENDING_APPROVAL")
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        mock_instance = MagicMock()
        
        self.adapter.on_rejected(1, mock_instance)
        
        self.assertEqual(mock_invoice.status, "REJECTED")
        self.mock_db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试撤回审批回调"""
        mock_invoice = Invoice(id=1, status="PENDING_APPROVAL")
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        mock_instance = MagicMock()
        
        self.adapter.on_withdrawn(1, mock_instance)
        
        self.assertEqual(mock_invoice.status, "DRAFT")
        self.mock_db.flush.assert_called_once()

    # ========== get_title() 测试 ==========

    def test_get_title_with_buyer_name(self):
        """测试生成标题（带购买方名称）"""
        mock_invoice = Invoice(
            id=1,
            invoice_code="INV-2024-001",
            buyer_name="测试客户"
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        result = self.adapter.get_title(1)
        
        self.assertEqual(result, "发票审批 - INV-2024-001 (测试客户)")

    def test_get_title_without_buyer_name(self):
        """测试生成标题（无购买方名称）"""
        mock_invoice = Invoice(
            id=1,
            invoice_code="INV-2024-001",
            buyer_name=None
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        result = self.adapter.get_title(1)
        
        self.assertEqual(result, "发票审批 - INV-2024-001 (未知客户)")

    def test_get_title_invoice_not_found(self):
        """测试发票不存在时的标题"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        result = self.adapter.get_title(999)
        
        self.assertEqual(result, "发票审批 - #999")

    # ========== get_summary() 测试 ==========

    def test_get_summary_complete(self):
        """测试生成完整摘要"""
        mock_contract = MagicMock()
        mock_contract.contract_code = "CNT-2024-001"
        
        mock_invoice = Invoice(
            id=1,
            invoice_code="INV-2024-001",
            buyer_name="测试客户",
            total_amount=Decimal("11300.00"),
            invoice_type="VAT_SPECIAL",
            contract_id=100
        )
        mock_invoice.contract = mock_contract
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        result = self.adapter.get_summary(1)
        
        # 验证摘要包含所有关键信息
        self.assertIn("购买方: 测试客户", result)
        self.assertIn("含税金额: ¥11,300.00", result)
        self.assertIn("类型: VAT_SPECIAL", result)
        self.assertIn("合同: CNT-2024-001", result)

    def test_get_summary_partial(self):
        """测试生成部分摘要（缺少某些字段）"""
        mock_invoice = Invoice(
            id=1,
            invoice_code="INV-2024-002",
            buyer_name="测试客户",
            total_amount=Decimal("5000.00"),
            invoice_type=None,
            contract_id=None
        )
        mock_invoice.contract = None
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        result = self.adapter.get_summary(1)
        
        self.assertIn("购买方: 测试客户", result)
        self.assertIn("含税金额: ¥5,000.00", result)
        # 不应该包含空字段
        self.assertNotIn("类型:", result)
        self.assertNotIn("合同:", result)

    def test_get_summary_empty(self):
        """测试发票不存在时返回空摘要"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        result = self.adapter.get_summary(999)
        
        self.assertEqual(result, "")

    # ========== validate_submit() 测试 ==========

    def test_validate_submit_success_draft(self):
        """测试草稿状态可以提交"""
        mock_invoice = Invoice(
            id=1,
            status="DRAFT",
            amount=Decimal("10000.00"),
            buyer_name="测试客户"
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        valid, message = self.adapter.validate_submit(1)
        
        self.assertTrue(valid)
        self.assertEqual(message, "")

    def test_validate_submit_success_rejected(self):
        """测试驳回状态可以重新提交"""
        mock_invoice = Invoice(
            id=1,
            status="REJECTED",
            amount=Decimal("10000.00"),
            buyer_name="测试客户"
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        valid, message = self.adapter.validate_submit(1)
        
        self.assertTrue(valid)
        self.assertEqual(message, "")

    def test_validate_submit_fail_not_found(self):
        """测试发票不存在"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        valid, message = self.adapter.validate_submit(999)
        
        self.assertFalse(valid)
        self.assertEqual(message, "发票不存在")

    def test_validate_submit_fail_wrong_status(self):
        """测试错误状态不允许提交"""
        mock_invoice = Invoice(
            id=1,
            status="APPROVED",
            amount=Decimal("10000.00"),
            buyer_name="测试客户"
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        valid, message = self.adapter.validate_submit(1)
        
        self.assertFalse(valid)
        self.assertIn("APPROVED", message)
        self.assertIn("不允许提交审批", message)

    def test_validate_submit_fail_zero_amount(self):
        """测试金额为0不允许提交"""
        mock_invoice = Invoice(
            id=1,
            status="DRAFT",
            amount=Decimal("0"),
            buyer_name="测试客户"
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        valid, message = self.adapter.validate_submit(1)
        
        self.assertFalse(valid)
        self.assertEqual(message, "发票金额必须大于0")

    def test_validate_submit_fail_none_amount(self):
        """测试金额为None不允许提交"""
        mock_invoice = Invoice(
            id=1,
            status="DRAFT",
            amount=None,
            buyer_name="测试客户"
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        valid, message = self.adapter.validate_submit(1)
        
        self.assertFalse(valid)
        self.assertEqual(message, "发票金额必须大于0")

    def test_validate_submit_fail_no_buyer_name(self):
        """测试缺少购买方名称不允许提交"""
        mock_invoice = Invoice(
            id=1,
            status="DRAFT",
            amount=Decimal("10000.00"),
            buyer_name=None
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        valid, message = self.adapter.validate_submit(1)
        
        self.assertFalse(valid)
        self.assertEqual(message, "请填写购买方名称")

    # ========== create_invoice_approval() 测试 ==========

    def test_create_invoice_approval_new(self):
        """测试创建新的发票审批记录"""
        # Mock instance
        mock_instance = ApprovalInstance()
        mock_instance.entity_id = 1
        
        # Mock task
        mock_task = ApprovalTask()
        mock_task.node_order = 1
        mock_task.node_name = "财务审核"
        mock_task.assignee_id = 10
        mock_task.due_at = datetime(2024, 1, 20, 12, 0, 0)
        mock_task.instance = mock_instance
        
        # Mock user
        mock_user = User(password_hash="test_hash_123")
        mock_user.id = 10
        mock_user.real_name = "张三"
        
        # Mock查询 - 先查不存在，再查user
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == InvoiceApproval:
                mock_filter = mock_query.filter.return_value
                mock_filter.first.return_value = None  # 不存在
            elif model == User:
                mock_filter = mock_query.filter.return_value
                mock_filter.first.return_value = mock_user
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        # 执行
        with patch('app.services.approval_engine.adapters.invoice.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 0, 0)
            
            result = self.adapter.create_invoice_approval(mock_instance, mock_task)
        
        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.invoice_id, 1)
        self.assertEqual(result.approval_level, 1)
        self.assertEqual(result.approval_role, "财务审核")
        self.assertEqual(result.approver_id, 10)
        self.assertEqual(result.approver_name, "张三")
        self.assertIsNone(result.approval_result)
        self.assertEqual(result.status, "PENDING")
        self.assertFalse(result.is_overdue)
        self.mock_db.add.assert_called_once_with(result)

    def test_create_invoice_approval_existing(self):
        """测试审批记录已存在时返回现有记录"""
        mock_instance = ApprovalInstance()
        mock_instance.entity_id = 1
        
        mock_task = ApprovalTask()
        mock_task.node_order = 1
        mock_task.instance = mock_instance
        
        # Mock existing record
        existing_approval = InvoiceApproval(
            id=100,
            invoice_id=1,
            approval_level=1
        )
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = existing_approval
        
        result = self.adapter.create_invoice_approval(mock_instance, mock_task)
        
        # 应该返回现有记录，不创建新的
        self.assertEqual(result, existing_approval)
        self.mock_db.add.assert_not_called()

    def test_create_invoice_approval_no_assignee(self):
        """测试没有审批人时"""
        mock_instance = ApprovalInstance()
        mock_instance.entity_id = 1
        
        mock_task = ApprovalTask()
        mock_task.node_order = 1
        mock_task.node_name = "财务审核"
        mock_task.assignee_id = None  # 没有审批人
        mock_task.due_at = None
        mock_task.instance = mock_instance
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == InvoiceApproval:
                mock_filter = mock_query.filter.return_value
                mock_filter.first.return_value = None
            elif model == User:
                mock_filter = mock_query.filter.return_value
                mock_filter.first.return_value = None
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        with patch('app.services.approval_engine.adapters.invoice.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 0, 0)
            
            result = self.adapter.create_invoice_approval(mock_instance, mock_task)
        
        self.assertIsNotNone(result)
        self.assertIsNone(result.approver_id)
        self.assertEqual(result.approver_name, "")
        # due_date应该是当前时间+48小时
        expected_due = datetime(2024, 1, 15, 10, 0, 0) + timedelta(hours=48)
        self.assertEqual(result.due_date, expected_due)

    # ========== update_invoice_approval_from_action() 测试 ==========

    def test_update_invoice_approval_approve(self):
        """测试更新审批记录为通过"""
        # Mock instance
        mock_instance = ApprovalInstance()
        mock_instance.entity_id = 1
        
        # Mock task
        mock_task = ApprovalTask()
        mock_task.node_order = 1
        mock_task.instance = mock_instance
        
        # Mock existing approval
        mock_approval = InvoiceApproval(
            invoice_id=1,
            approval_level=1,
            status="PENDING"
        )
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_approval
        
        # 执行
        with patch('app.services.approval_engine.adapters.invoice.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 14, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            result = self.adapter.update_invoice_approval_from_action(
                mock_task, "APPROVE", "同意"
            )
        
        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.approval_result, "APPROVED")
        self.assertEqual(result.approval_opinion, "同意")
        self.assertEqual(result.status, "APPROVED")
        self.assertEqual(result.approved_at, mock_now)
        self.mock_db.add.assert_called_once_with(result)
        self.mock_db.commit.assert_called_once()

    def test_update_invoice_approval_reject(self):
        """测试更新审批记录为驳回"""
        mock_instance = ApprovalInstance()
        mock_instance.entity_id = 1
        
        mock_task = ApprovalTask()
        mock_task.node_order = 1
        mock_task.instance = mock_instance
        
        mock_approval = InvoiceApproval(
            invoice_id=1,
            approval_level=1,
            status="PENDING"
        )
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_approval
        
        with patch('app.services.approval_engine.adapters.invoice.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 14, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            result = self.adapter.update_invoice_approval_from_action(
                mock_task, "REJECT", "金额有误"
            )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.approval_result, "REJECTED")
        self.assertEqual(result.approval_opinion, "金额有误")
        self.assertEqual(result.status, "REJECTED")
        self.assertEqual(result.approved_at, mock_now)

    def test_update_invoice_approval_not_found(self):
        """测试审批记录不存在"""
        mock_instance = ApprovalInstance()
        mock_instance.entity_id = 1
        
        mock_task = ApprovalTask()
        mock_task.node_order = 1
        mock_task.instance = mock_instance
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        result = self.adapter.update_invoice_approval_from_action(
            mock_task, "APPROVE", "同意"
        )
        
        # 应该返回None并记录警告
        self.assertIsNone(result)
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_not_called()

    def test_update_invoice_approval_unknown_action(self):
        """测试未知的审批操作"""
        mock_instance = ApprovalInstance()
        mock_instance.entity_id = 1
        
        mock_task = ApprovalTask()
        mock_task.node_order = 1
        mock_task.instance = mock_instance
        
        mock_approval = InvoiceApproval(
            invoice_id=1,
            approval_level=1,
            status="PENDING"
        )
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_approval
        
        result = self.adapter.update_invoice_approval_from_action(
            mock_task, "UNKNOWN", "测试"
        )
        
        # 未知操作不应该更新字段
        self.assertIsNone(result.approval_result)
        self.assertIsNone(result.approved_at)

    # ========== 边界情况测试 ==========

    def test_entity_type_constant(self):
        """测试entity_type常量"""
        self.assertEqual(self.adapter.entity_type, "INVOICE")

    def test_get_entity_data_with_zero_decimals(self):
        """测试处理零值的Decimal字段"""
        mock_invoice = Invoice(
            id=1,
            invoice_code="INV-2024-003",
            status="DRAFT",
            invoice_type="ORDINARY",
            amount=Decimal("0"),
            tax_rate=Decimal("0"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("0"),
            contract_id=None,
            project_id=None,
            buyer_name="测试",
            buyer_tax_no=None,
            issue_date=None,
            due_date=None
        )
        mock_invoice.contract = None
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        result = self.adapter.get_entity_data(1)
        
        # Decimal(0)应该转换为float 0
        self.assertEqual(result["amount"], 0.0)
        self.assertEqual(result["tax_rate"], 0.0)
        self.assertEqual(result["tax_amount"], 0.0)
        self.assertEqual(result["total_amount"], 0.0)

    def test_validate_submit_negative_amount(self):
        """测试负金额不允许提交"""
        mock_invoice = Invoice(
            id=1,
            status="DRAFT",
            amount=Decimal("-100.00"),
            buyer_name="测试客户"
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        valid, message = self.adapter.validate_submit(1)
        
        self.assertFalse(valid)
        self.assertEqual(message, "发票金额必须大于0")

    def test_validate_submit_empty_buyer_name(self):
        """测试空字符串购买方名称不允许提交"""
        mock_invoice = Invoice(
            id=1,
            status="DRAFT",
            amount=Decimal("10000.00"),
            buyer_name=""  # 空字符串
        )
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_invoice
        
        valid, message = self.adapter.validate_submit(1)
        
        self.assertFalse(valid)
        self.assertEqual(message, "请填写购买方名称")


if __name__ == "__main__":
    unittest.main()

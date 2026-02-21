# -*- coding: utf-8 -*-
"""
发票审批适配器单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库查询）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
from app.models.sales.invoices import Invoice, InvoiceApproval
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.user import User
from app.models.sales.contracts import Contract


class TestInvoiceAdapterCore(unittest.TestCase):
    """测试核心适配器方法"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.adapter = InvoiceApprovalAdapter(self.db)
        self.entity_id = 1
        self.instance = MagicMock(spec=ApprovalInstance)

    # ========== get_entity() 测试 ==========

    def test_get_entity_success(self):
        """测试成功获取发票实体"""
        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.id = self.entity_id
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        result = self.adapter.get_entity(self.entity_id)

        self.assertEqual(result, mock_invoice)
        self.db.query.assert_called_once_with(Invoice)

    def test_get_entity_not_found(self):
        """测试获取不存在的发票"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(self.entity_id)

        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_basic(self):
        """测试获取基础发票数据"""
        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-001",
            status="DRAFT",
            invoice_type="增值税专用发票",
            amount=Decimal("10000.00"),
            tax_rate=Decimal("0.13"),
            tax_amount=Decimal("1300.00"),
            total_amount=Decimal("11300.00"),
            buyer_name="测试客户",
            buyer_tax_no="91110000123456789X"
        )

        self._setup_query_returns(mock_invoice)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证基础字段
        self.assertEqual(result["invoice_code"], "INV-2024-001")
        self.assertEqual(result["status"], "DRAFT")
        self.assertEqual(result["invoice_type"], "增值税专用发票")
        self.assertEqual(result["amount"], 10000.00)
        self.assertEqual(result["tax_rate"], 0.13)
        self.assertEqual(result["tax_amount"], 1300.00)
        self.assertEqual(result["total_amount"], 11300.00)
        self.assertEqual(result["buyer_name"], "测试客户")
        self.assertEqual(result["buyer_tax_no"], "91110000123456789X")

    def test_get_entity_data_with_contract(self):
        """测试获取包含合同信息的发票数据"""
        mock_contract = MagicMock(spec=Contract)
        mock_contract.contract_code = "CTR-2024-001"

        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-002",
            contract_id=10
        )
        mock_invoice.contract = mock_contract

        self._setup_query_returns(mock_invoice)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证合同信息
        self.assertEqual(result["contract_id"], 10)
        self.assertEqual(result["contract_code"], "CTR-2024-001")

    def test_get_entity_data_without_contract(self):
        """测试获取没有合同的发票数据"""
        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-003",
            contract_id=None
        )
        mock_invoice.contract = None

        self._setup_query_returns(mock_invoice)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证合同字段为None
        self.assertIsNone(result["contract_id"])
        self.assertIsNone(result["contract_code"])

    def test_get_entity_data_with_dates(self):
        """测试包含日期字段的数据"""
        issue_date = datetime(2024, 1, 10)
        due_date = datetime(2024, 2, 10)

        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-004",
            issue_date=issue_date,
            due_date=due_date
        )

        self._setup_query_returns(mock_invoice)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证日期被转换为ISO格式
        self.assertEqual(result["issue_date"], issue_date.isoformat())
        self.assertEqual(result["due_date"], due_date.isoformat())

    def test_get_entity_data_with_null_dates(self):
        """测试日期为空的情况"""
        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-005",
            issue_date=None,
            due_date=None
        )

        self._setup_query_returns(mock_invoice)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证日期为None
        self.assertIsNone(result["issue_date"])
        self.assertIsNone(result["due_date"])

    def test_get_entity_data_with_null_amounts(self):
        """测试金额为空的情况"""
        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-006",
            amount=None,
            tax_rate=None,
            tax_amount=None,
            total_amount=None
        )

        self._setup_query_returns(mock_invoice)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证金额字段默认为0
        self.assertEqual(result["amount"], 0)
        self.assertEqual(result["tax_rate"], 0)
        self.assertEqual(result["tax_amount"], 0)
        self.assertEqual(result["total_amount"], 0)

    def test_get_entity_data_not_found(self):
        """测试获取不存在发票的数据"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity_data(self.entity_id)

        # 应返回空字典
        self.assertEqual(result, {})

    # ========== on_submit() 测试 ==========

    def test_on_submit_success(self):
        """测试成功提交审批"""
        mock_invoice = self._create_mock_invoice(status="DRAFT")
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        self.adapter.on_submit(self.entity_id, self.instance)

        # 验证状态更改
        self.assertEqual(mock_invoice.status, "PENDING_APPROVAL")
        self.db.flush.assert_called_once()

    def test_on_submit_invoice_not_found(self):
        """测试提交不存在的发票"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_submit(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_approved() 测试 ==========

    def test_on_approved_success(self):
        """测试成功审批通过"""
        mock_invoice = self._create_mock_invoice(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        self.adapter.on_approved(self.entity_id, self.instance)

        # 验证状态更改为APPROVED
        self.assertEqual(mock_invoice.status, "APPROVED")
        self.db.flush.assert_called_once()

    def test_on_approved_invoice_not_found(self):
        """测试审批通过不存在的发票"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_approved(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_rejected() 测试 ==========

    def test_on_rejected_success(self):
        """测试成功驳回审批"""
        mock_invoice = self._create_mock_invoice(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 验证状态更改为REJECTED
        self.assertEqual(mock_invoice.status, "REJECTED")
        self.db.flush.assert_called_once()

    def test_on_rejected_invoice_not_found(self):
        """测试驳回不存在的发票"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_withdrawn() 测试 ==========

    def test_on_withdrawn_success(self):
        """测试成功撤回审批"""
        mock_invoice = self._create_mock_invoice(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 验证状态恢复为DRAFT
        self.assertEqual(mock_invoice.status, "DRAFT")
        self.db.flush.assert_called_once()

    def test_on_withdrawn_invoice_not_found(self):
        """测试撤回不存在的发票"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== get_title() 测试 ==========

    def test_get_title_success(self):
        """测试生成发票审批标题"""
        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-001",
            buyer_name="测试客户A"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, "发票审批 - INV-2024-001 (测试客户A)")

    def test_get_title_without_buyer_name(self):
        """测试生成没有购买方名称的标题"""
        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-002",
            buyer_name=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, "发票审批 - INV-2024-002 (未知客户)")

    def test_get_title_invoice_not_found(self):
        """测试生成不存在发票的标题"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, f"发票审批 - #{self.entity_id}")

    # ========== get_summary() 测试 ==========

    def test_get_summary_full_info(self):
        """测试生成包含完整信息的摘要"""
        mock_contract = MagicMock(spec=Contract)
        mock_contract.contract_code = "CTR-2024-001"

        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-001",
            buyer_name="测试客户A",
            total_amount=Decimal("11300.00"),
            invoice_type="增值税专用发票",
            contract_id=10
        )
        mock_invoice.contract = mock_contract

        self._setup_query_returns(mock_invoice)

        summary = self.adapter.get_summary(self.entity_id)

        # 验证摘要包含所有信息
        self.assertIn("购买方: 测试客户A", summary)
        self.assertIn("含税金额: ¥11,300.00", summary)
        self.assertIn("类型: 增值税专用发票", summary)
        self.assertIn("合同: CTR-2024-001", summary)

    def test_get_summary_minimal_info(self):
        """测试生成最少信息的摘要"""
        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-002",
            buyer_name=None,
            total_amount=None,
            invoice_type=None,
            contract_id=None
        )
        mock_invoice.contract = None

        self._setup_query_returns(mock_invoice)

        summary = self.adapter.get_summary(self.entity_id)

        # 当get_entity_data返回空字典时，摘要为空字符串
        self.assertEqual(summary, "")

    def test_get_summary_invoice_not_found(self):
        """测试生成不存在发票的摘要"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        summary = self.adapter.get_summary(self.entity_id)

        # 应返回空字符串
        self.assertEqual(summary, "")

    # ========== validate_submit() 测试 ==========

    def test_validate_submit_success_from_draft(self):
        """测试从草稿状态成功验证提交"""
        mock_invoice = self._create_mock_invoice(
            status="DRAFT",
            amount=Decimal("10000.00"),
            buyer_name="测试客户"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_submit_success_from_rejected(self):
        """测试从驳回状态成功验证提交"""
        mock_invoice = self._create_mock_invoice(
            status="REJECTED",
            amount=Decimal("5000.00"),
            buyer_name="测试客户B"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_submit_invoice_not_found(self):
        """测试验证不存在的发票"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "发票不存在")

    def test_validate_submit_invalid_status(self):
        """测试无效状态下提交"""
        mock_invoice = self._create_mock_invoice(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertIn("不允许提交审批", error)

    def test_validate_submit_zero_amount(self):
        """测试金额为0"""
        mock_invoice = self._create_mock_invoice(
            status="DRAFT",
            amount=Decimal("0"),
            buyer_name="测试客户"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "发票金额必须大于0")

    def test_validate_submit_negative_amount(self):
        """测试金额为负数"""
        mock_invoice = self._create_mock_invoice(
            status="DRAFT",
            amount=Decimal("-1000.00"),
            buyer_name="测试客户"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "发票金额必须大于0")

    def test_validate_submit_null_amount(self):
        """测试金额为空"""
        mock_invoice = self._create_mock_invoice(
            status="DRAFT",
            amount=None,
            buyer_name="测试客户"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "发票金额必须大于0")

    def test_validate_submit_missing_buyer_name(self):
        """测试缺少购买方名称"""
        mock_invoice = self._create_mock_invoice(
            status="DRAFT",
            amount=Decimal("10000.00"),
            buyer_name=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请填写购买方名称")

    def test_validate_submit_empty_buyer_name(self):
        """测试购买方名称为空字符串"""
        mock_invoice = self._create_mock_invoice(
            status="DRAFT",
            amount=Decimal("10000.00"),
            buyer_name=""
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请填写购买方名称")

    # ========== submit_for_approval() 测试 ==========

    def test_submit_for_approval_already_submitted(self):
        """测试发票已经提交审批"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 100

        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-001",
            approval_instance_id=100
        )

        # 设置查询返回已存在的实例
        self.db.query.return_value.filter.return_value.first.return_value = mock_instance

        with patch('app.services.approval_engine.adapters.invoice.logger') as mock_logger:
            result = self.adapter.submit_for_approval(
                invoice=mock_invoice,
                initiator_id=1
            )

            # 验证返回已存在的实例
            self.assertEqual(result, mock_instance)
            # 验证记录了警告日志
            mock_logger.warning.assert_called_once()

    def test_submit_for_approval_create_new_instance(self):
        """测试创建新的审批实例"""
        mock_contract = MagicMock(spec=Contract)
        mock_contract.contract_code = "CTR-2024-001"

        mock_invoice = self._create_mock_invoice(
            invoice_code="INV-2024-001",
            approval_instance_id=None,
            contract_id=10,
            amount=Decimal("10000.00"),
            tax_rate=Decimal("0.13"),
            tax_amount=Decimal("1300.00"),
            total_amount=Decimal("11300.00")
        )
        mock_invoice.contract = mock_contract

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 200
        mock_instance.status = "PENDING"

        with patch('app.services.approval_engine.workflow_engine.WorkflowEngine') as MockWorkflowEngine:
            mock_engine = MagicMock()
            mock_engine.create_instance.return_value = mock_instance
            MockWorkflowEngine.return_value = mock_engine

            result = self.adapter.submit_for_approval(
                invoice=mock_invoice,
                initiator_id=1,
                title="测试审批",
                summary="测试摘要",
                urgency="HIGH",
                cc_user_ids=[2, 3]
            )

            # 验证返回新实例
            self.assertEqual(result, mock_instance)

            # 验证调用了WorkflowEngine.create_instance
            mock_engine.create_instance.assert_called_once()
            call_kwargs = mock_engine.create_instance.call_args[1]
            self.assertEqual(call_kwargs['flow_code'], "SALES_INVOICE")
            self.assertEqual(call_kwargs['business_type'], "SALES_INVOICE")
            self.assertEqual(call_kwargs['business_id'], mock_invoice.id)
            self.assertEqual(call_kwargs['submitted_by'], 1)

            # 验证更新了发票
            self.assertEqual(mock_invoice.approval_instance_id, 200)
            self.assertEqual(mock_invoice.approval_status, "PENDING")
            self.db.add.assert_called_once_with(mock_invoice)
            self.db.commit.assert_called_once()

    # ========== create_invoice_approval() 测试 ==========

    def test_create_invoice_approval_existing(self):
        """测试已存在的发票审批记录"""
        self.instance.entity_id = 1

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.assignee_id = 10

        existing_approval = MagicMock(spec=InvoiceApproval)
        existing_approval.id = 100

        self.db.query.return_value.filter.return_value.first.return_value = existing_approval

        result = self.adapter.create_invoice_approval(self.instance, mock_task)

        # 验证返回已存在的记录
        self.assertEqual(result, existing_approval)
        # 不应该添加新记录
        self.db.add.assert_not_called()

    def test_create_invoice_approval_create_new(self):
        """测试创建新的发票审批记录"""
        self.instance.entity_id = 1

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 2
        mock_task.node_name = "财务审批"
        mock_task.assignee_id = 20
        mock_task.due_at = datetime(2024, 1, 15, 18, 0, 0)

        mock_user = MagicMock(spec=User)
        mock_user.real_name = "张三"

        # 设置查询返回：第一次查询InvoiceApproval返回None，第二次查询User返回mock_user
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == InvoiceApproval:
                mock_query.filter.return_value.first.return_value = None
            elif model == User:
                mock_query.filter.return_value.first.return_value = mock_user
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.create_invoice_approval(self.instance, mock_task)

        # 验证添加了新记录
        self.db.add.assert_called_once()
        added_approval = self.db.add.call_args[0][0]
        
        self.assertEqual(added_approval.invoice_id, 1)
        self.assertEqual(added_approval.approval_level, 2)
        self.assertEqual(added_approval.approval_role, "财务审批")
        self.assertEqual(added_approval.approver_id, 20)
        self.assertEqual(added_approval.approver_name, "张三")
        self.assertIsNone(added_approval.approval_result)
        self.assertEqual(added_approval.status, "PENDING")
        self.assertEqual(added_approval.due_date, datetime(2024, 1, 15, 18, 0, 0))
        self.assertFalse(added_approval.is_overdue)

    def test_create_invoice_approval_no_due_at(self):
        """测试没有到期时间的情况（使用默认48小时）"""
        self.instance.entity_id = 1

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.node_name = "部门审批"
        mock_task.assignee_id = None
        mock_task.due_at = None

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == InvoiceApproval:
                mock_query.filter.return_value.first.return_value = None
            elif model == User:
                mock_query.filter.return_value.first.return_value = None
            return mock_query

        self.db.query.side_effect = query_side_effect

        with patch('app.services.approval_engine.adapters.invoice.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 10, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = self.adapter.create_invoice_approval(self.instance, mock_task)

            # 验证使用了默认到期时间（48小时后）
            self.db.add.assert_called_once()
            added_approval = self.db.add.call_args[0][0]
            expected_due = mock_now + timedelta(hours=48)
            self.assertEqual(added_approval.due_date, expected_due)

    def test_create_invoice_approval_no_assignee(self):
        """测试没有审批人的情况"""
        self.instance.entity_id = 1

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.node_name = "待分配"
        mock_task.assignee_id = None
        mock_task.due_at = datetime(2024, 1, 15, 18, 0, 0)

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == InvoiceApproval:
                mock_query.filter.return_value.first.return_value = None
            elif model == User:
                mock_query.filter.return_value.first.return_value = None
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.create_invoice_approval(self.instance, mock_task)

        # 验证没有审批人信息
        self.db.add.assert_called_once()
        added_approval = self.db.add.call_args[0][0]
        self.assertIsNone(added_approval.approver_id)
        self.assertEqual(added_approval.approver_name, "")

    # ========== update_invoice_approval_from_action() 测试 ==========

    def test_update_invoice_approval_approve(self):
        """测试审批通过更新"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.instance.entity_id = 1
        mock_task.node_order = 1

        mock_approval = MagicMock(spec=InvoiceApproval)
        mock_approval.invoice_id = 1
        mock_approval.approval_level = 1

        self.db.query.return_value.filter.return_value.first.return_value = mock_approval

        with patch('app.services.approval_engine.adapters.invoice.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = self.adapter.update_invoice_approval_from_action(
                task=mock_task,
                action="APPROVE",
                comment="同意通过"
            )

            # 验证更新了审批结果
            self.assertEqual(mock_approval.approval_result, "APPROVED")
            self.assertEqual(mock_approval.approval_opinion, "同意通过")
            self.assertEqual(mock_approval.status, "APPROVED")
            self.assertEqual(mock_approval.approved_at, mock_now)
            
            self.db.add.assert_called_once_with(mock_approval)
            self.db.commit.assert_called_once()

    def test_update_invoice_approval_reject(self):
        """测试审批驳回更新"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.instance.entity_id = 2
        mock_task.node_order = 2

        mock_approval = MagicMock(spec=InvoiceApproval)
        mock_approval.invoice_id = 2
        mock_approval.approval_level = 2

        self.db.query.return_value.filter.return_value.first.return_value = mock_approval

        with patch('app.services.approval_engine.adapters.invoice.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 11, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = self.adapter.update_invoice_approval_from_action(
                task=mock_task,
                action="REJECT",
                comment="金额有误"
            )

            # 验证更新了驳回结果
            self.assertEqual(mock_approval.approval_result, "REJECTED")
            self.assertEqual(mock_approval.approval_opinion, "金额有误")
            self.assertEqual(mock_approval.status, "REJECTED")
            self.assertEqual(mock_approval.approved_at, mock_now)
            
            self.db.add.assert_called_once_with(mock_approval)
            self.db.commit.assert_called_once()

    def test_update_invoice_approval_not_found(self):
        """测试更新不存在的审批记录"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.instance.entity_id = 999
        mock_task.node_order = 1

        self.db.query.return_value.filter.return_value.first.return_value = None

        with patch('app.services.approval_engine.adapters.invoice.logger') as mock_logger:
            result = self.adapter.update_invoice_approval_from_action(
                task=mock_task,
                action="APPROVE",
                comment="同意"
            )

            # 验证返回None
            self.assertIsNone(result)
            # 验证记录了警告日志
            mock_logger.warning.assert_called_once()
            # 不应该提交
            self.db.commit.assert_not_called()

    def test_update_invoice_approval_no_comment(self):
        """测试没有审批意见的更新"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.instance.entity_id = 1
        mock_task.node_order = 1

        mock_approval = MagicMock(spec=InvoiceApproval)

        self.db.query.return_value.filter.return_value.first.return_value = mock_approval

        with patch('app.services.approval_engine.adapters.invoice.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 0, 0)

            result = self.adapter.update_invoice_approval_from_action(
                task=mock_task,
                action="APPROVE",
                comment=None
            )

            # 验证审批意见为None
            self.assertIsNone(mock_approval.approval_opinion)

    # ========== 辅助方法 ==========

    def _create_mock_invoice(self, **kwargs):
        """创建模拟发票对象"""
        mock_invoice = MagicMock(spec=Invoice)
        
        # 设置默认值
        defaults = {
            'id': self.entity_id,
            'invoice_code': 'INV-TEST-001',
            'status': 'DRAFT',
            'invoice_type': '增值税专用发票',
            'amount': Decimal("10000.00"),
            'tax_rate': Decimal("0.13"),
            'tax_amount': Decimal("1300.00"),
            'total_amount': Decimal("11300.00"),
            'contract_id': None,
            'project_id': None,
            'buyer_name': '测试客户',
            'buyer_tax_no': '91110000123456789X',
            'issue_date': None,
            'due_date': None,
            'approval_instance_id': None,
            'approval_status': None,
        }
        
        # 合并自定义值
        defaults.update(kwargs)
        
        # 设置属性
        for key, value in defaults.items():
            setattr(mock_invoice, key, value)
        
        # 默认没有合同
        if 'contract' not in kwargs:
            mock_invoice.contract = None
        
        return mock_invoice

    def _setup_query_returns(self, mock_invoice):
        """设置基础查询返回"""
        self.db.query.return_value.filter.return_value.first.return_value = mock_invoice


class TestAdapterEntityType(unittest.TestCase):
    """测试适配器类属性"""

    def test_entity_type(self):
        """测试entity_type类属性"""
        self.assertEqual(InvoiceApprovalAdapter.entity_type, "INVOICE")


if __name__ == '__main__':
    unittest.main()

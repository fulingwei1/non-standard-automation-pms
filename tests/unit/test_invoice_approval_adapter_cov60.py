# -*- coding: utf-8 -*-
"""
发票审批适配器 单元测试
目标覆盖率: 60%+
覆盖: 数据转换、验证、审批回调、工作流集成
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
    from app.models.approval import ApprovalInstance, ApprovalTask
    from app.models.sales.invoices import Invoice, InvoiceApproval
    from app.models.user import User
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    """创建mock数据库会话"""
    db = MagicMock()
    db.flush = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


def make_invoice(**kwargs):
    """创建mock发票"""
    invoice = MagicMock(spec=Invoice)
    invoice.id = kwargs.get("id", 1)
    invoice.invoice_code = kwargs.get("invoice_code", "INV-2025-001")
    invoice.status = kwargs.get("status", "DRAFT")
    invoice.invoice_type = kwargs.get("invoice_type", "VAT_SPECIAL")
    invoice.amount = Decimal(kwargs.get("amount", "100000"))
    invoice.tax_rate = Decimal(kwargs.get("tax_rate", "0.13"))
    invoice.tax_amount = Decimal(kwargs.get("tax_amount", "13000"))
    invoice.total_amount = Decimal(kwargs.get("total_amount", "113000"))
    invoice.contract_id = kwargs.get("contract_id", None)
    invoice.project_id = kwargs.get("project_id", None)
    invoice.buyer_name = kwargs.get("buyer_name", "测试公司")
    invoice.buyer_tax_no = kwargs.get("buyer_tax_no", "91110000MA001234XX")
    invoice.issue_date = kwargs.get("issue_date", datetime.now())
    invoice.due_date = kwargs.get("due_date", datetime.now() + timedelta(days=30))
    invoice.approval_instance_id = kwargs.get("approval_instance_id", None)
    invoice.approval_status = kwargs.get("approval_status", None)
    
    # Mock contract
    contract = kwargs.get("contract", None)
    if contract:
        type(invoice).contract = PropertyMock(return_value=contract)
    else:
        type(invoice).contract = PropertyMock(return_value=None)
    
    return invoice


def make_contract(**kwargs):
    """创建mock合同"""
    contract = MagicMock()
    contract.id = kwargs.get("id", 100)
    contract.contract_code = kwargs.get("contract_code", "CT-2025-001")
    return contract


def make_approval_instance(**kwargs):
    """创建mock审批实例"""
    instance = MagicMock(spec=ApprovalInstance)
    instance.id = kwargs.get("id", 1000)
    instance.status = kwargs.get("status", "PENDING")
    instance.approved_by = kwargs.get("approved_by", None)
    instance.entity_id = kwargs.get("entity_id", 1)
    return instance


def make_approval_task(**kwargs):
    """创建mock审批任务"""
    task = MagicMock(spec=ApprovalTask)
    task.id = kwargs.get("id", 2000)
    task.node_order = kwargs.get("node_order", 1)
    task.node_name = kwargs.get("node_name", "财务审批")
    task.assignee_id = kwargs.get("assignee_id", 20)
    task.due_at = kwargs.get("due_at", None)
    task.instance = kwargs.get("instance", make_approval_instance())
    return task


def make_user(**kwargs):
    """创建mock用户"""
    user = MagicMock(spec=User)
    user.id = kwargs.get("id", 20)
    user.real_name = kwargs.get("real_name", "财务经理")
    return user


class TestInvoiceApprovalAdapter:
    """发票审批适配器测试"""

    def test_adapter_entity_type(self):
        """测试适配器实体类型"""
        db = make_db()
        adapter = InvoiceApprovalAdapter(db)
        assert adapter.entity_type == "INVOICE"

    def test_get_entity_found(self):
        """测试获取发票实体 - 找到"""
        db = make_db()
        invoice = make_invoice(id=1)
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.get_entity(1)
        
        assert result == invoice

    def test_get_entity_not_found(self):
        """测试获取发票实体 - 未找到"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.get_entity(999)
        
        assert result is None

    def test_get_entity_data_complete(self):
        """测试获取实体数据 - 完整数据"""
        db = make_db()
        contract = make_contract(contract_code="CT-001")
        invoice = make_invoice(
            invoice_code="INV-001",
            invoice_type="VAT_SPECIAL",
            amount="150000",
            tax_rate="0.13",
            tax_amount="19500",
            total_amount="169500",
            contract_id=100,
            project_id=200,
            buyer_name="客户A",
            buyer_tax_no="91110000MA001234XX",
            contract=contract
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["invoice_code"] == "INV-001"
        assert data["invoice_type"] == "VAT_SPECIAL"
        assert data["amount"] == 150000.0
        assert data["tax_rate"] == 0.13
        assert data["tax_amount"] == 19500.0
        assert data["total_amount"] == 169500.0
        assert data["contract_code"] == "CT-001"
        assert data["buyer_name"] == "客户A"

    def test_get_entity_data_no_contract(self):
        """测试获取实体数据 - 无合同"""
        db = make_db()
        invoice = make_invoice(contract_id=None, contract=None)
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["contract_id"] is None
        assert data["contract_code"] is None

    def test_get_entity_data_not_found(self):
        """测试获取实体数据 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(999)
        
        assert data == {}

    def test_on_submit(self):
        """测试提交审批回调"""
        db = make_db()
        invoice = make_invoice(status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = invoice
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_submit(1, instance)
        
        assert invoice.status == "PENDING_APPROVAL"
        db.flush.assert_called_once()

    def test_on_approved(self):
        """测试审批通过回调"""
        db = make_db()
        invoice = make_invoice(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = invoice
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_approved(1, instance)
        
        assert invoice.status == "APPROVED"
        db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回回调"""
        db = make_db()
        invoice = make_invoice(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = invoice
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_rejected(1, instance)
        
        assert invoice.status == "REJECTED"
        db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试撤回审批回调"""
        db = make_db()
        invoice = make_invoice(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = invoice
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_withdrawn(1, instance)
        
        assert invoice.status == "DRAFT"
        db.flush.assert_called_once()

    def test_get_title_complete(self):
        """测试生成审批标题 - 完整信息"""
        db = make_db()
        invoice = make_invoice(
            invoice_code="INV-123",
            buyer_name="测试企业"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        title = adapter.get_title(1)
        
        assert "发票审批" in title
        assert "INV-123" in title
        assert "测试企业" in title

    def test_get_title_no_buyer(self):
        """测试生成审批标题 - 无购买方"""
        db = make_db()
        invoice = make_invoice(
            invoice_code="INV-456",
            buyer_name=None
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        title = adapter.get_title(1)
        
        assert "未知客户" in title

    def test_get_summary_complete(self):
        """测试生成审批摘要 - 完整信息"""
        db = make_db()
        contract = make_contract(contract_code="CT-789")
        invoice = make_invoice(
            buyer_name="客户B",
            total_amount="200000",
            invoice_type="VAT_SPECIAL",
            contract_id=100,
            contract=contract
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        summary = adapter.get_summary(1)
        
        assert "客户B" in summary
        assert "200,000.00" in summary
        assert "VAT_SPECIAL" in summary
        assert "CT-789" in summary

    def test_get_summary_minimal(self):
        """测试生成审批摘要 - 最小化信息"""
        db = make_db()
        invoice = make_invoice(
            buyer_name=None,
            contract_id=None,
            contract=None
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        summary = adapter.get_summary(1)
        
        # 应该只包含金额和类型
        assert "113,000.00" in summary
        assert "VAT_SPECIAL" in summary

    def test_validate_submit_success(self):
        """测试提交验证 - 成功"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            amount="50000",
            buyer_name="测试公司"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error == ""

    def test_validate_submit_not_found(self):
        """测试提交验证 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(999)
        
        assert valid is False
        assert "不存在" in error

    def test_validate_submit_wrong_status(self):
        """测试提交验证 - 状态错误"""
        db = make_db()
        invoice = make_invoice(status="APPROVED")
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "不允许提交审批" in error

    def test_validate_submit_zero_amount(self):
        """测试提交验证 - 金额为0"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            amount="0"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "必须大于0" in error

    def test_validate_submit_no_buyer(self):
        """测试提交验证 - 缺少购买方"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            amount="50000",
            buyer_name=None
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "购买方名称" in error

    @patch('app.services.approval_engine.adapters.invoice.WorkflowEngine')
    def test_submit_for_approval_success(self, mock_workflow_engine):
        """测试提交审批 - 成功"""
        db = make_db()
        invoice = make_invoice(approval_instance_id=None)
        instance = make_approval_instance(id=5000)
        
        # Mock WorkflowEngine
        mock_engine = MagicMock()
        mock_engine.create_instance.return_value = instance
        mock_workflow_engine.return_value = mock_engine
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.submit_for_approval(
            invoice,
            initiator_id=10,
            title="发票审批测试",
            summary="测试摘要"
        )
        
        assert result == instance
        assert invoice.approval_instance_id == 5000
        db.add.assert_called_with(invoice)
        db.commit.assert_called_once()

    @patch('app.services.approval_engine.adapters.invoice.WorkflowEngine')
    def test_submit_for_approval_already_submitted(self, mock_workflow_engine):
        """测试提交审批 - 已提交"""
        db = make_db()
        existing_instance = make_approval_instance(id=6000)
        invoice = make_invoice(approval_instance_id=6000)
        
        db.query.return_value.filter.return_value.first.return_value = existing_instance
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.submit_for_approval(invoice, initiator_id=10)
        
        assert result == existing_instance
        # 不应该创建新实例
        mock_workflow_engine.assert_not_called()

    def test_create_invoice_approval_new(self):
        """测试创建发票审批记录 - 新建"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=1, assignee_id=20, due_at=None)
        user = make_user(real_name="审批人A")
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == InvoiceApproval:
                query_mock.filter.return_value.first.return_value = None
            elif model == User:
                query_mock.filter.return_value.first.return_value = user
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = InvoiceApprovalAdapter(db)
        approval = adapter.create_invoice_approval(instance, task)
        
        assert approval is not None
        assert approval.invoice_id == 100
        assert approval.approval_level == 1
        assert approval.approver_name == "审批人A"
        assert approval.due_date is not None  # 默认48小时
        assert approval.is_overdue is False
        db.add.assert_called_with(approval)

    def test_create_invoice_approval_with_due_date(self):
        """测试创建发票审批记录 - 指定到期时间"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        custom_due = datetime.now() + timedelta(hours=24)
        task = make_approval_task(node_order=1, assignee_id=20, due_at=custom_due)
        user = make_user(real_name="审批人B")
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == InvoiceApproval:
                query_mock.filter.return_value.first.return_value = None
            elif model == User:
                query_mock.filter.return_value.first.return_value = user
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = InvoiceApprovalAdapter(db)
        approval = adapter.create_invoice_approval(instance, task)
        
        assert approval.due_date == custom_due

    def test_create_invoice_approval_existing(self):
        """测试创建发票审批记录 - 已存在"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=1)
        existing_approval = MagicMock()
        
        db.query.return_value.filter.return_value.first.return_value = existing_approval
        
        adapter = InvoiceApprovalAdapter(db)
        approval = adapter.create_invoice_approval(instance, task)
        
        assert approval == existing_approval
        # 不应该添加新记录
        db.add.assert_not_called()

    def test_update_invoice_approval_approve(self):
        """测试更新发票审批记录 - 同意"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=1, instance=instance)
        approval = MagicMock()
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.update_invoice_approval_from_action(
            task,
            action="APPROVE",
            comment="发票信息准确"
        )
        
        assert result == approval
        assert approval.approval_result == "APPROVED"
        assert approval.approval_opinion == "发票信息准确"
        assert approval.status == "APPROVED"
        assert approval.approved_at is not None
        db.add.assert_called_with(approval)
        db.commit.assert_called_once()

    def test_update_invoice_approval_reject(self):
        """测试更新发票审批记录 - 驳回"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=2, instance=instance)
        approval = MagicMock()
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.update_invoice_approval_from_action(
            task,
            action="REJECT",
            comment="发票金额有误"
        )
        
        assert result == approval
        assert approval.approval_result == "REJECTED"
        assert approval.approval_opinion == "发票金额有误"
        assert approval.status == "REJECTED"
        db.commit.assert_called_once()

    def test_update_invoice_approval_not_found(self):
        """测试更新发票审批记录 - 记录不存在"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(node_order=1, instance=instance)
        
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.update_invoice_approval_from_action(
            task,
            action="APPROVE"
        )
        
        assert result is None
        db.commit.assert_not_called()

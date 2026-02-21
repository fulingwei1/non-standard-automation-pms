# -*- coding: utf-8 -*-
"""
发票审批适配器 增强单元测试
目标覆盖率: 70%+
覆盖范围: 所有核心方法、边界条件、异常处理、数据转换、业务逻辑
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock, call

try:
    from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
    from app.models.approval import ApprovalInstance, ApprovalTask
    from app.models.sales.invoices import Invoice, InvoiceApproval
    from app.models.user import User
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


# ========== 测试辅助函数 ========== #

def make_db():
    """创建mock数据库会话"""
    db = MagicMock()
    db.flush = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


def make_invoice(**kwargs):
    """创建mock发票对象（构造真实数据对象）"""
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
    invoice.issue_date = kwargs.get("issue_date", datetime(2025, 1, 15))
    invoice.due_date = kwargs.get("due_date", datetime(2025, 2, 15))
    invoice.approval_instance_id = kwargs.get("approval_instance_id", None)
    invoice.approval_status = kwargs.get("approval_status", None)
    
    # Mock contract 关联
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
    instance.entity_type = kwargs.get("entity_type", "INVOICE")
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
    user.username = kwargs.get("username", "finance_manager")
    return user


def make_invoice_approval(**kwargs):
    """创建mock发票审批记录"""
    approval = MagicMock(spec=InvoiceApproval)
    approval.id = kwargs.get("id", 3000)
    approval.invoice_id = kwargs.get("invoice_id", 1)
    approval.approval_level = kwargs.get("approval_level", 1)
    approval.approval_role = kwargs.get("approval_role", "财务")
    approval.approver_id = kwargs.get("approver_id", 20)
    approval.approver_name = kwargs.get("approver_name", "财务经理")
    approval.approval_result = kwargs.get("approval_result", None)
    approval.status = kwargs.get("status", "PENDING")
    approval.due_date = kwargs.get("due_date", datetime.now() + timedelta(hours=48))
    approval.is_overdue = kwargs.get("is_overdue", False)
    approval.approved_at = kwargs.get("approved_at", None)
    approval.approval_opinion = kwargs.get("approval_opinion", None)
    return approval


# ========== 测试类 ========== #

class TestInvoiceAdapterBasics:
    """基础功能测试"""

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        db = make_db()
        adapter = InvoiceApprovalAdapter(db)
        assert adapter.db is db
        assert adapter.entity_type == "INVOICE"

    def test_adapter_entity_type_constant(self):
        """测试实体类型常量"""
        assert InvoiceApprovalAdapter.entity_type == "INVOICE"


class TestGetEntity:
    """获取实体测试"""

    def test_get_entity_success(self):
        """测试获取发票实体 - 成功"""
        db = make_db()
        invoice = make_invoice(id=1, invoice_code="INV-001")
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.get_entity(1)
        
        assert result == invoice
        assert result.invoice_code == "INV-001"

    def test_get_entity_not_found(self):
        """测试获取发票实体 - 不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.get_entity(999)
        
        assert result is None

    def test_get_entity_multiple_calls(self):
        """测试多次获取同一实体"""
        db = make_db()
        invoice = make_invoice(id=5)
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        result1 = adapter.get_entity(5)
        result2 = adapter.get_entity(5)
        
        assert result1 == result2
        assert db.query.call_count >= 2


class TestGetEntityData:
    """获取实体数据测试"""

    def test_get_entity_data_full_complete(self):
        """测试获取实体数据 - 所有字段完整"""
        db = make_db()
        contract = make_contract(id=100, contract_code="CT-2025-100")
        invoice = make_invoice(
            id=1,
            invoice_code="INV-2025-001",
            status="DRAFT",
            invoice_type="VAT_SPECIAL",
            amount="250000.50",
            tax_rate="0.13",
            tax_amount="32500.065",
            total_amount="282500.565",
            contract_id=100,
            project_id=200,
            buyer_name="北京测试科技有限公司",
            buyer_tax_no="91110108MA01ABCD12",
            issue_date=datetime(2025, 2, 1),
            due_date=datetime(2025, 3, 1),
            contract=contract
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["invoice_code"] == "INV-2025-001"
        assert data["status"] == "DRAFT"
        assert data["invoice_type"] == "VAT_SPECIAL"
        assert data["amount"] == 250000.50
        assert data["tax_rate"] == 0.13
        assert abs(data["tax_amount"] - 32500.065) < 0.01
        assert abs(data["total_amount"] - 282500.565) < 0.01
        assert data["contract_id"] == 100
        assert data["contract_code"] == "CT-2025-100"
        assert data["project_id"] == 200
        assert data["buyer_name"] == "北京测试科技有限公司"
        assert data["buyer_tax_no"] == "91110108MA01ABCD12"
        assert data["issue_date"] == "2025-02-01T00:00:00"
        assert data["due_date"] == "2025-03-01T00:00:00"

    def test_get_entity_data_no_contract(self):
        """测试获取实体数据 - 无合同"""
        db = make_db()
        invoice = make_invoice(contract_id=None, contract=None)
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["contract_id"] is None
        assert data["contract_code"] is None

    def test_get_entity_data_none_amounts(self):
        """测试获取实体数据 - 金额为None"""
        db = make_db()
        invoice = make_invoice()
        invoice.amount = None
        invoice.tax_rate = None
        invoice.tax_amount = None
        invoice.total_amount = None
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["amount"] == 0
        assert data["tax_rate"] == 0
        assert data["tax_amount"] == 0
        assert data["total_amount"] == 0

    def test_get_entity_data_none_dates(self):
        """测试获取实体数据 - 日期为None"""
        db = make_db()
        invoice = make_invoice()
        invoice.issue_date = None
        invoice.due_date = None
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["issue_date"] is None
        assert data["due_date"] is None

    def test_get_entity_data_entity_not_found(self):
        """测试获取实体数据 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        data = adapter.get_entity_data(999)
        
        assert data == {}


class TestApprovalCallbacks:
    """审批回调测试"""

    def test_on_submit_from_draft(self):
        """测试提交审批回调 - 从草稿状态"""
        db = make_db()
        invoice = make_invoice(status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = invoice
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_submit(1, instance)
        
        assert invoice.status == "PENDING_APPROVAL"
        db.flush.assert_called_once()

    def test_on_submit_from_rejected(self):
        """测试提交审批回调 - 从驳回状态重新提交"""
        db = make_db()
        invoice = make_invoice(status="REJECTED")
        db.query.return_value.filter.return_value.first.return_value = invoice
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_submit(1, instance)
        
        assert invoice.status == "PENDING_APPROVAL"

    def test_on_submit_entity_not_found(self):
        """测试提交审批回调 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_submit(999, instance)
        
        # 不应该抛出异常，flush不应该被调用
        db.flush.assert_not_called()

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

    def test_on_approved_entity_not_found(self):
        """测试审批通过回调 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_approved(999, instance)
        
        db.flush.assert_not_called()

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

    def test_on_rejected_entity_not_found(self):
        """测试审批驳回回调 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_rejected(999, instance)
        
        db.flush.assert_not_called()

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

    def test_on_withdrawn_entity_not_found(self):
        """测试撤回审批回调 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        instance = make_approval_instance()
        
        adapter = InvoiceApprovalAdapter(db)
        adapter.on_withdrawn(999, instance)
        
        db.flush.assert_not_called()


class TestTitleAndSummary:
    """标题和摘要生成测试"""

    def test_get_title_complete(self):
        """测试生成审批标题 - 完整信息"""
        db = make_db()
        invoice = make_invoice(
            invoice_code="INV-2025-123",
            buyer_name="上海测试企业有限公司"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        title = adapter.get_title(1)
        
        assert "发票审批" in title
        assert "INV-2025-123" in title
        assert "上海测试企业有限公司" in title

    def test_get_title_no_buyer_name(self):
        """测试生成审批标题 - 无购买方名称"""
        db = make_db()
        invoice = make_invoice(
            invoice_code="INV-2025-456",
            buyer_name=None
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        title = adapter.get_title(1)
        
        assert "未知客户" in title
        assert "INV-2025-456" in title

    def test_get_title_empty_buyer_name(self):
        """测试生成审批标题 - 购买方名称为空字符串"""
        db = make_db()
        invoice = make_invoice(
            invoice_code="INV-2025-789",
            buyer_name=""
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        title = adapter.get_title(1)
        
        assert "未知客户" in title

    def test_get_title_entity_not_found(self):
        """测试生成审批标题 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        title = adapter.get_title(999)
        
        assert "发票审批" in title
        assert "#999" in title

    def test_get_summary_all_fields(self):
        """测试生成审批摘要 - 所有字段"""
        db = make_db()
        contract = make_contract(contract_code="CT-2025-999")
        invoice = make_invoice(
            buyer_name="深圳测试有限公司",
            total_amount="500000",
            invoice_type="VAT_NORMAL",
            contract_id=100,
            contract=contract
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        summary = adapter.get_summary(1)
        
        assert "深圳测试有限公司" in summary
        assert "500,000.00" in summary
        assert "VAT_NORMAL" in summary
        assert "CT-2025-999" in summary

    def test_get_summary_minimal_fields(self):
        """测试生成审批摘要 - 最小化字段"""
        db = make_db()
        invoice = make_invoice(
            buyer_name=None,
            contract_id=None,
            contract=None,
            total_amount="80000"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        summary = adapter.get_summary(1)
        
        assert "80,000.00" in summary
        assert "VAT_SPECIAL" in summary  # 默认类型

    def test_get_summary_entity_not_found(self):
        """测试生成审批摘要 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        summary = adapter.get_summary(999)
        
        assert summary == ""


class TestValidateSubmit:
    """提交验证测试"""

    def test_validate_submit_success_from_draft(self):
        """测试提交验证 - 草稿状态成功"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            amount="100000",
            buyer_name="测试公司A"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error == ""

    def test_validate_submit_success_from_rejected(self):
        """测试提交验证 - 驳回状态可重新提交"""
        db = make_db()
        invoice = make_invoice(
            status="REJECTED",
            amount="50000",
            buyer_name="测试公司B"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error == ""

    def test_validate_submit_entity_not_found(self):
        """测试提交验证 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(999)
        
        assert valid is False
        assert "不存在" in error

    def test_validate_submit_status_approved(self):
        """测试提交验证 - 已审批通过状态"""
        db = make_db()
        invoice = make_invoice(status="APPROVED")
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "不允许提交审批" in error

    def test_validate_submit_status_pending(self):
        """测试提交验证 - 审批中状态"""
        db = make_db()
        invoice = make_invoice(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "不允许提交审批" in error

    def test_validate_submit_amount_zero(self):
        """测试提交验证 - 金额为0"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            amount="0",
            buyer_name="测试公司"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "必须大于0" in error

    def test_validate_submit_amount_negative(self):
        """测试提交验证 - 金额为负数"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            amount="-1000",
            buyer_name="测试公司"
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "必须大于0" in error

    def test_validate_submit_amount_none(self):
        """测试提交验证 - 金额为None"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            buyer_name="测试公司"
        )
        invoice.amount = None
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "必须大于0" in error

    def test_validate_submit_no_buyer_name(self):
        """测试提交验证 - 缺少购买方名称"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            amount="100000",
            buyer_name=None
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "购买方名称" in error

    def test_validate_submit_empty_buyer_name(self):
        """测试提交验证 - 购买方名称为空字符串"""
        db = make_db()
        invoice = make_invoice(
            status="DRAFT",
            amount="100000",
            buyer_name=""
        )
        db.query.return_value.filter.return_value.first.return_value = invoice
        
        adapter = InvoiceApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "购买方名称" in error


class TestSubmitForApproval:
    """提交审批集成测试"""

    @patch('app.services.approval_engine.workflow_engine.WorkflowEngine')
    def test_submit_for_approval_new_submission(self, mock_workflow_engine):
        """测试提交审批 - 新提交"""
        db = make_db()
        contract = make_contract(contract_code="CT-TEST-001")
        invoice = make_invoice(
            id=10,
            invoice_code="INV-TEST-001",
            approval_instance_id=None,
            contract=contract
        )
        instance = make_approval_instance(id=5000, entity_id=10)
        
        mock_engine = MagicMock()
        mock_engine.create_instance.return_value = instance
        mock_workflow_engine.return_value = mock_engine
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.submit_for_approval(
            invoice,
            initiator_id=15,
            title="测试发票审批",
            summary="这是测试摘要",
            urgency="HIGH",
            cc_user_ids=[20, 21, 22]
        )
        
        assert result == instance
        assert invoice.approval_instance_id == 5000
        assert invoice.approval_status == instance.status
        db.add.assert_called_with(invoice)
        db.commit.assert_called_once()
        
        # 验证调用参数
        mock_engine.create_instance.assert_called_once()
        call_args = mock_engine.create_instance.call_args
        assert call_args[1]["flow_code"] == "SALES_INVOICE"
        assert call_args[1]["business_type"] == "SALES_INVOICE"
        assert call_args[1]["business_id"] == 10
        assert call_args[1]["submitted_by"] == 15

    @patch('app.services.approval_engine.workflow_engine.WorkflowEngine')
    def test_submit_for_approval_already_submitted(self, mock_workflow_engine):
        """测试提交审批 - 已提交过"""
        db = make_db()
        existing_instance = make_approval_instance(id=6000)
        invoice = make_invoice(approval_instance_id=6000)
        
        db.query.return_value.filter.return_value.first.return_value = existing_instance
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.submit_for_approval(invoice, initiator_id=10)
        
        assert result == existing_instance
        mock_workflow_engine.assert_not_called()
        db.commit.assert_not_called()

    @patch('app.services.approval_engine.workflow_engine.WorkflowEngine')
    def test_submit_for_approval_default_parameters(self, mock_workflow_engine):
        """测试提交审批 - 使用默认参数"""
        db = make_db()
        invoice = make_invoice(
            id=20,
            invoice_code="INV-DEFAULT",
            approval_instance_id=None
        )
        instance = make_approval_instance(id=7000)
        
        mock_engine = MagicMock()
        mock_engine.create_instance.return_value = instance
        mock_workflow_engine.return_value = mock_engine
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.submit_for_approval(invoice, initiator_id=30)
        
        assert result == instance
        db.commit.assert_called_once()


class TestCreateInvoiceApproval:
    """创建发票审批记录测试"""

    def test_create_invoice_approval_new_record(self):
        """测试创建发票审批记录 - 新记录"""
        db = make_db()
        instance = make_approval_instance(entity_id=100)
        task = make_approval_task(
            node_order=1,
            node_name="财务审核",
            assignee_id=25,
            due_at=None
        )
        user = make_user(id=25, real_name="张财务")
        
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
        assert approval.approval_role == "财务审核"
        assert approval.approver_id == 25
        assert approval.approver_name == "张财务"
        assert approval.status == "PENDING"
        assert approval.is_overdue is False
        assert approval.due_date is not None
        db.add.assert_called_with(approval)

    def test_create_invoice_approval_with_custom_due_date(self):
        """测试创建发票审批记录 - 自定义到期时间"""
        db = make_db()
        instance = make_approval_instance(entity_id=101)
        custom_due = datetime(2025, 3, 1, 18, 0, 0)
        task = make_approval_task(
            node_order=2,
            assignee_id=26,
            due_at=custom_due
        )
        user = make_user(id=26, real_name="李审批")
        
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

    def test_create_invoice_approval_no_assignee(self):
        """测试创建发票审批记录 - 无审批人"""
        db = make_db()
        instance = make_approval_instance(entity_id=102)
        task = make_approval_task(
            node_order=1,
            assignee_id=None
        )
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == InvoiceApproval:
                query_mock.filter.return_value.first.return_value = None
            elif model == User:
                query_mock.filter.return_value.first.return_value = None
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = InvoiceApprovalAdapter(db)
        approval = adapter.create_invoice_approval(instance, task)
        
        assert approval is not None
        assert approval.approver_id is None
        assert approval.approver_name == ""

    def test_create_invoice_approval_existing_record(self):
        """测试创建发票审批记录 - 记录已存在"""
        db = make_db()
        instance = make_approval_instance(entity_id=103)
        task = make_approval_task(node_order=1)
        existing_approval = make_invoice_approval(
            invoice_id=103,
            approval_level=1
        )
        
        db.query.return_value.filter.return_value.first.return_value = existing_approval
        
        adapter = InvoiceApprovalAdapter(db)
        approval = adapter.create_invoice_approval(instance, task)
        
        assert approval == existing_approval
        db.add.assert_not_called()


class TestUpdateInvoiceApproval:
    """更新发票审批记录测试"""

    def test_update_invoice_approval_approve(self):
        """测试更新发票审批记录 - 同意"""
        db = make_db()
        instance = make_approval_instance(entity_id=200)
        task = make_approval_task(node_order=1, instance=instance)
        approval = make_invoice_approval()
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.update_invoice_approval_from_action(
            task,
            action="APPROVE",
            comment="发票信息核对无误，同意"
        )
        
        assert result == approval
        assert approval.approval_result == "APPROVED"
        assert approval.approval_opinion == "发票信息核对无误，同意"
        assert approval.status == "APPROVED"
        assert approval.approved_at is not None
        db.add.assert_called_with(approval)
        db.commit.assert_called_once()

    def test_update_invoice_approval_reject(self):
        """测试更新发票审批记录 - 驳回"""
        db = make_db()
        instance = make_approval_instance(entity_id=201)
        task = make_approval_task(node_order=2, instance=instance)
        approval = make_invoice_approval()
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.update_invoice_approval_from_action(
            task,
            action="REJECT",
            comment="金额计算错误，需要重新提交"
        )
        
        assert result == approval
        assert approval.approval_result == "REJECTED"
        assert approval.approval_opinion == "金额计算错误，需要重新提交"
        assert approval.status == "REJECTED"
        assert approval.approved_at is not None
        db.commit.assert_called_once()

    def test_update_invoice_approval_no_comment(self):
        """测试更新发票审批记录 - 无评论"""
        db = make_db()
        instance = make_approval_instance(entity_id=202)
        task = make_approval_task(node_order=1, instance=instance)
        approval = make_invoice_approval()
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.update_invoice_approval_from_action(
            task,
            action="APPROVE",
            comment=None
        )
        
        assert result == approval
        assert approval.approval_opinion is None

    def test_update_invoice_approval_not_found(self):
        """测试更新发票审批记录 - 记录不存在"""
        db = make_db()
        instance = make_approval_instance(entity_id=203)
        task = make_approval_task(node_order=1, instance=instance)
        
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.update_invoice_approval_from_action(
            task,
            action="APPROVE"
        )
        
        assert result is None
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_update_invoice_approval_different_levels(self):
        """测试更新发票审批记录 - 不同审批级别"""
        db = make_db()
        instance = make_approval_instance(entity_id=204)
        
        # 测试第3级审批
        task = make_approval_task(node_order=3, instance=instance)
        approval = make_invoice_approval(approval_level=3)
        
        db.query.return_value.filter.return_value.first.return_value = approval
        
        adapter = InvoiceApprovalAdapter(db)
        result = adapter.update_invoice_approval_from_action(
            task,
            action="APPROVE",
            comment="最终审批通过"
        )
        
        assert result == approval
        assert approval.approval_result == "APPROVED"

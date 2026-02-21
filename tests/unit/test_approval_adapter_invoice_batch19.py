# -*- coding: utf-8 -*-
"""
审批适配器 - 发票适配器 单元测试 (Batch 19)

测试 app/services/approval_engine/adapters/invoice.py
覆盖率目标: 60%+
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.sales.invoices import Invoice, InvoiceApproval
from app.models.user import User
from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter


@pytest.mark.unit
class TestInvoiceApprovalAdapterInit:
    """测试初始化"""

    def test_init_success(self):
        """测试成功初始化"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        assert adapter.db == mock_db
        assert adapter.entity_type == "INVOICE"


@pytest.mark.unit
class TestGetEntity:
    """测试 get_entity 方法"""

    def test_get_entity_found(self):
        """测试获取存在的发票"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.id = 123
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        result = adapter.get_entity(123)

        assert result == mock_invoice
        mock_db.query.assert_called_once()

    def test_get_entity_not_found(self):
        """测试获取不存在的发票"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity(999)

        assert result is None


@pytest.mark.unit
class TestGetEntityData:
    """测试 get_entity_data 方法"""

    def test_get_entity_data_success(self):
        """测试成功获取发票数据"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        # 创建模拟发票
        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.id = 123
        mock_invoice.invoice_code = "INV-2024-001"
        mock_invoice.status = "DRAFT"
        mock_invoice.invoice_type = "VAT"
        mock_invoice.amount = Decimal("10000.00")
        mock_invoice.tax_rate = Decimal("0.13")
        mock_invoice.tax_amount = Decimal("1300.00")
        mock_invoice.total_amount = Decimal("11300.00")
        mock_invoice.contract_id = 456
        mock_invoice.project_id = 789
        mock_invoice.buyer_name = "ABC Company"
        mock_invoice.buyer_tax_no = "123456789"
        mock_invoice.issue_date = datetime(2024, 1, 15)
        mock_invoice.due_date = datetime(2024, 2, 15)

        # 模拟关联合同
        mock_contract = MagicMock()
        mock_contract.contract_code = "CON-2024-001"
        mock_invoice.contract = mock_contract

        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        result = adapter.get_entity_data(123)

        assert result["invoice_code"] == "INV-2024-001"
        assert result["status"] == "DRAFT"
        assert result["invoice_type"] == "VAT"
        assert result["amount"] == 10000.00
        assert result["tax_rate"] == 0.13
        assert result["total_amount"] == 11300.00
        assert result["contract_code"] == "CON-2024-001"
        assert result["buyer_name"] == "ABC Company"

    def test_get_entity_data_invoice_not_found(self):
        """测试发票不存在时返回空字典"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity_data(999)

        assert result == {}

    def test_get_entity_data_no_contract(self):
        """测试发票无合同关联"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.invoice_code = "INV-2024-002"
        mock_invoice.status = "DRAFT"
        mock_invoice.invoice_type = "ORDINARY"
        mock_invoice.amount = Decimal("5000.00")
        mock_invoice.tax_rate = None
        mock_invoice.tax_amount = None
        mock_invoice.total_amount = Decimal("5000.00")
        mock_invoice.contract = None
        mock_invoice.contract_id = None
        mock_invoice.project_id = None
        mock_invoice.buyer_name = "XYZ Ltd"
        mock_invoice.buyer_tax_no = None
        mock_invoice.issue_date = None
        mock_invoice.due_date = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        result = adapter.get_entity_data(123)

        assert result["contract_code"] is None
        assert result["tax_rate"] == 0
        assert result["tax_amount"] == 0


@pytest.mark.unit
class TestCallbacks:
    """测试生命周期回调方法"""

    def test_on_submit(self):
        """测试提交时回调"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_instance = MagicMock(spec=ApprovalInstance)

        adapter.on_submit(123, mock_instance)

        assert mock_invoice.status == "PENDING_APPROVAL"
        mock_db.flush.assert_called_once()

    def test_on_approved(self):
        """测试审批通过时回调"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_instance = MagicMock(spec=ApprovalInstance)

        adapter.on_approved(123, mock_instance)

        assert mock_invoice.status == "APPROVED"
        mock_db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回时回调"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_instance = MagicMock(spec=ApprovalInstance)

        adapter.on_rejected(123, mock_instance)

        assert mock_invoice.status == "REJECTED"
        mock_db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试撤回时回调"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_instance = MagicMock(spec=ApprovalInstance)

        adapter.on_withdrawn(123, mock_instance)

        assert mock_invoice.status == "DRAFT"
        mock_db.flush.assert_called_once()

    def test_callback_invoice_not_found(self):
        """测试发票不存在时回调不报错"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_instance = MagicMock(spec=ApprovalInstance)

        # 这些方法不应抛出异常
        adapter.on_submit(999, mock_instance)
        adapter.on_approved(999, mock_instance)
        adapter.on_rejected(999, mock_instance)
        adapter.on_withdrawn(999, mock_instance)


@pytest.mark.unit
class TestGetTitleAndSummary:
    """测试获取标题和摘要"""

    def test_get_title_success(self):
        """测试成功获取标题"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.invoice_code = "INV-2024-003"
        mock_invoice.buyer_name = "测试公司"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        title = adapter.get_title(123)

        assert title == "发票审批 - INV-2024-003 (测试公司)"

    def test_get_title_no_buyer_name(self):
        """测试无购买方名称时的标题"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.invoice_code = "INV-2024-004"
        mock_invoice.buyer_name = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        title = adapter.get_title(123)

        assert title == "发票审批 - INV-2024-004 (未知客户)"

    def test_get_title_invoice_not_found(self):
        """测试发票不存在时的标题"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        title = adapter.get_title(999)

        assert title == "发票审批 - #999"

    def test_get_summary_success(self):
        """测试成功获取摘要"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.buyer_name = "测试公司"
        mock_invoice.total_amount = Decimal("11300.00")
        mock_invoice.invoice_type = "VAT"
        mock_invoice.contract = MagicMock()
        mock_invoice.contract.contract_code = "CON-2024-001"
        mock_invoice.invoice_code = "INV-2024-001"
        mock_invoice.status = "DRAFT"
        mock_invoice.amount = Decimal("10000.00")
        mock_invoice.tax_rate = Decimal("0.13")
        mock_invoice.tax_amount = Decimal("1300.00")
        mock_invoice.contract_id = 1
        mock_invoice.project_id = 1
        mock_invoice.buyer_tax_no = "123"
        mock_invoice.issue_date = None
        mock_invoice.due_date = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        summary = adapter.get_summary(123)

        assert "购买方: 测试公司" in summary
        assert "含税金额: ¥11,300.00" in summary
        assert "类型: VAT" in summary
        assert "合同: CON-2024-001" in summary

    def test_get_summary_minimal_data(self):
        """测试最小数据的摘要"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.buyer_name = None
        mock_invoice.total_amount = None
        mock_invoice.invoice_type = None
        mock_invoice.contract = None
        mock_invoice.invoice_code = "INV"
        mock_invoice.status = "DRAFT"
        mock_invoice.amount = None
        mock_invoice.tax_rate = None
        mock_invoice.tax_amount = None
        mock_invoice.contract_id = None
        mock_invoice.project_id = None
        mock_invoice.buyer_tax_no = None
        mock_invoice.issue_date = None
        mock_invoice.due_date = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        summary = adapter.get_summary(123)

        assert summary == ""

    def test_get_summary_invoice_not_found(self):
        """测试发票不存在时的摘要"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        summary = adapter.get_summary(999)

        assert summary == ""


@pytest.mark.unit
class TestValidateSubmit:
    """测试提交验证"""

    def test_validate_submit_success_draft(self):
        """测试草稿状态可以提交"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.status = "DRAFT"
        mock_invoice.amount = Decimal("10000.00")
        mock_invoice.buyer_name = "测试公司"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, message = adapter.validate_submit(123)

        assert valid is True
        assert message == ""

    def test_validate_submit_success_rejected(self):
        """测试驳回状态可以重新提交"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.status = "REJECTED"
        mock_invoice.amount = Decimal("5000.00")
        mock_invoice.buyer_name = "公司B"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, message = adapter.validate_submit(123)

        assert valid is True
        assert message == ""

    def test_validate_submit_invoice_not_found(self):
        """测试发票不存在"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        valid, message = adapter.validate_submit(999)

        assert valid is False
        assert message == "发票不存在"

    def test_validate_submit_invalid_status(self):
        """测试无效状态不能提交"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.status = "APPROVED"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert "当前状态(APPROVED)不允许提交审批" in message

    def test_validate_submit_zero_amount(self):
        """测试金额为0不能提交"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.status = "DRAFT"
        mock_invoice.amount = Decimal("0")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert message == "发票金额必须大于0"

    def test_validate_submit_negative_amount(self):
        """测试负金额不能提交"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.status = "DRAFT"
        mock_invoice.amount = Decimal("-1000.00")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert message == "发票金额必须大于0"

    def test_validate_submit_no_buyer_name(self):
        """测试无购买方名称不能提交"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.status = "DRAFT"
        mock_invoice.amount = Decimal("10000.00")
        mock_invoice.buyer_name = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert message == "请填写购买方名称"

    def test_validate_submit_empty_buyer_name(self):
        """测试空购买方名称不能提交"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.status = "DRAFT"
        mock_invoice.amount = Decimal("10000.00")
        mock_invoice.buyer_name = ""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert message == "请填写购买方名称"


@pytest.mark.unit
class TestSubmitForApproval:
    """测试提交审批"""

    @patch("app.services.approval_engine.workflow_engine.WorkflowEngine")
    def test_submit_for_approval_success(self, mock_workflow_engine_class):
        """测试成功提交审批"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        # 模拟发票
        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.id = 123
        mock_invoice.invoice_code = "INV-2024-001"
        mock_invoice.invoice_type = "VAT"
        mock_invoice.amount = Decimal("10000.00")
        mock_invoice.tax_rate = Decimal("0.13")
        mock_invoice.tax_amount = Decimal("1300.00")
        mock_invoice.total_amount = Decimal("11300.00")
        mock_invoice.contract_id = 456
        mock_invoice.project_id = 789
        mock_invoice.buyer_name = "测试公司"
        mock_invoice.buyer_tax_no = "123456789"
        mock_invoice.issue_date = datetime(2024, 1, 15)
        mock_invoice.due_date = datetime(2024, 2, 15)
        mock_invoice.approval_instance_id = None

        mock_contract = MagicMock()
        mock_contract.contract_code = "CON-2024-001"
        mock_invoice.contract = mock_contract

        # 模拟审批实例
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 999
        mock_instance.status = "PENDING"

        # 模拟WorkflowEngine
        mock_engine = MagicMock()
        mock_engine.create_instance.return_value = mock_instance
        mock_workflow_engine_class.return_value = mock_engine

        result = adapter.submit_for_approval(
            invoice=mock_invoice,
            initiator_id=100,
            title="测试审批",
            summary="测试摘要",
            urgency="HIGH",
            cc_user_ids=[200, 300],
        )

        assert result == mock_instance
        assert mock_invoice.approval_instance_id == 999
        assert mock_invoice.approval_status == "PENDING"
        mock_db.add.assert_called_with(mock_invoice)
        mock_db.commit.assert_called_once()

    @patch("app.services.approval_engine.workflow_engine.WorkflowEngine")
    def test_submit_for_approval_already_submitted(self, mock_workflow_engine_class):
        """测试已提交审批的发票"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        # 模拟已提交审批的发票
        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.invoice_code = "INV-2024-002"
        mock_invoice.approval_instance_id = 888

        # 模拟已存在的审批实例
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 888
        mock_db.query.return_value.filter.return_value.first.return_value = mock_instance

        result = adapter.submit_for_approval(
            invoice=mock_invoice,
            initiator_id=100,
        )

        assert result == mock_instance
        # 不应该创建新实例
        mock_workflow_engine_class.assert_not_called()


@pytest.mark.unit
class TestCreateInvoiceApproval:
    """测试创建发票审批记录"""

    def test_create_invoice_approval_success(self):
        """测试成功创建审批记录"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        # 模拟实例和任务
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 123

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.assignee_id = 200
        mock_task.node_name = "财务审批"
        mock_task.due_at = None

        # 模拟审批人
        mock_approver = MagicMock(spec=User)
        mock_approver.id = 200
        mock_approver.real_name = "张三"

        # Mock query chain: 先返回None（不存在记录），再返回审批人
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 第一次查询：检查是否已存在
            mock_approver,  # 第二次查询：获取审批人
        ]

        result = adapter.create_invoice_approval(mock_instance, mock_task)

        assert result is not None
        assert result.invoice_id == 123
        assert result.approval_level == 1
        assert result.approver_id == 200
        assert result.approver_name == "张三"
        assert result.status == "PENDING"
        mock_db.add.assert_called_once()

    def test_create_invoice_approval_already_exists(self):
        """测试审批记录已存在"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 123

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.assignee_id = 200

        # 模拟已存在的记录
        existing_approval = MagicMock(spec=InvoiceApproval)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_approval

        result = adapter.create_invoice_approval(mock_instance, mock_task)

        assert result == existing_approval
        # 不应该创建新记录
        mock_db.add.assert_not_called()

    def test_create_invoice_approval_no_assignee(self):
        """测试无审批人的情况"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 123

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 2
        mock_task.assignee_id = None
        mock_task.node_name = "自动节点"
        mock_task.due_at = datetime.now() + timedelta(days=1)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = adapter.create_invoice_approval(mock_instance, mock_task)

        assert result is not None
        assert result.approver_id is None
        assert result.approver_name == ""


@pytest.mark.unit
class TestUpdateInvoiceApprovalFromAction:
    """测试更新发票审批记录"""

    def test_update_invoice_approval_approve(self):
        """测试审批通过"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 123

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = mock_instance

        mock_approval = MagicMock(spec=InvoiceApproval)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_approval

        result = adapter.update_invoice_approval_from_action(
            task=mock_task,
            action="APPROVE",
            comment="同意",
        )

        assert result == mock_approval
        assert mock_approval.approval_result == "APPROVED"
        assert mock_approval.approval_opinion == "同意"
        assert mock_approval.status == "APPROVED"
        assert mock_approval.approved_at is not None
        mock_db.add.assert_called_once_with(mock_approval)
        mock_db.commit.assert_called_once()

    def test_update_invoice_approval_reject(self):
        """测试审批驳回"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 123

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = mock_instance

        mock_approval = MagicMock(spec=InvoiceApproval)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_approval

        result = adapter.update_invoice_approval_from_action(
            task=mock_task,
            action="REJECT",
            comment="金额有误",
        )

        assert result == mock_approval
        assert mock_approval.approval_result == "REJECTED"
        assert mock_approval.approval_opinion == "金额有误"
        assert mock_approval.status == "REJECTED"

    def test_update_invoice_approval_not_found(self):
        """测试审批记录不存在"""
        mock_db = MagicMock()
        adapter = InvoiceApprovalAdapter(mock_db)

        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.entity_id = 999

        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.node_order = 1
        mock_task.instance = mock_instance

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = adapter.update_invoice_approval_from_action(
            task=mock_task,
            action="APPROVE",
        )

        assert result is None
        mock_db.commit.assert_not_called()

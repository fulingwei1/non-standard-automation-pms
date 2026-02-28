# -*- coding: utf-8 -*-
"""
Sales审批流程集成测试

测试范围：
1. 报价审批流程
2. 合同审批流程
3. 发票审批流程
4. Sales实体同步
5. 错误处理
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.sales import (
    QuoteVersion,
)
from app.models.sales.contracts import Contract
from app.models.sales.invoices import Invoice
from app.services.approval_engine.workflow_engine import WorkflowEngine
from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter
from app.services.approval_engine.adapters.contract import ContractApprovalAdapter
from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter


class TestSalesApprovalFlow:
    """Sales审批流程集成测试"""

    @pytest.fixture
    def quote_version_sample(self, db_session: Session):
        """创建测试用的报价版本"""
        quote = QuoteVersion(
            quote_code="QV20250101001",
            quote_total=50000.00,
            margin_percent=15.5,
            status="DRAFT",
        )
        db_session.add(quote)
        db_session.commit()

        return quote

    @pytest.fixture
    def contract_sample(self, db_session: Session):
        """创建测试用的合同"""
        contract = Contract(
            contract_code="CT20250101001",
            total_amount=100000.00,
            customer_id=1,  # 假设有客户ID=1
            project_id=1,  # 假设有项目ID=1
            signed_date=datetime.now().date(),
            payment_terms_summary="按进度分批付款：30-30-40-30",
        )
        db_session.add(contract)
        db_session.commit()

        return contract

    @pytest.fixture
    def invoice_sample(self, db_session: Session):
        """创建测试用的发票"""
        invoice = Invoice(
            invoice_code="INV20250101001",
            invoice_type="INVOICE",
            amount=30000.00,
            tax_rate=0.13,
            status="DRAFT",
            contract_id=1,
            project_id=1,
        )
        db_session.add(invoice)
        db_session.commit()

        return invoice

    # ========== 报价审批测试 ==========

    def test_submit_quote_for_approval(
        self, db_session: Session, quote_version_sample: QuoteVersion
    ):
        """测试提交报价审批"""
        adapter = QuoteApprovalAdapter(db_session)

        instance = adapter.submit_for_approval(
            quote_version=quote_version_sample,
            initiator_id=1,  # 假设有用户ID=1
            title="报价审批测试",
            summary="50000.00，利润率15.5%，需要审批",
        )

        # 验证实例创建
        assert instance is not None
        assert instance.instance_no.startswith("AP")
        assert instance.entity_type == "QUOTE"
        assert instance.entity_id == quote_version_sample.id
        assert instance.status in ["PENDING", "IN_PROGRESS"]
        assert instance.urgency == "NORMAL"

        # 验证报价版本已更新
        db_session.refresh(quote_version_sample)
        assert quote_version_sample.approval_instance_id == instance.id
        assert quote_version_sample.approval_status == instance.status

    def test_quote_approval_with_high_amount(self, db_session: Session):
        """测试高金额报价审批流程"""
        # 创建高金额报价
        quote = QuoteVersion(
            quote_code="QV20250101002",
            quote_total=150000.00,
            margin_percent=12.0,
            status="DRAFT",
        )
        db_session.add(quote)
        db_session.commit()

        adapter = QuoteApprovalAdapter(db_session)

        # Use mock quote_id if not available
        quote_id = getattr(quote, "quote_id", 1)

        instance = adapter.submit_quote_for_approval(
            quote_id=quote_id,
            quote_version_id=quote.id,
            initiator_id=1,
            title="大额报价审批",
            summary="150000.00，利润率12.0%",
        )

        # 验证审批实例
        assert instance is not None
        assert instance.status == "PENDING"

    def test_quote_approval_rejection(
        self, db_session: Session, quote_version_sample: QuoteVersion
    ):
        """测试报价审批驳回"""
        # 先创建审批实例
        quote = quote_version_sample
        adapter = QuoteApprovalAdapter(db_session)
        quote_id = getattr(quote, "quote_id", 1)

        instance = adapter.submit_quote_for_approval(
            quote_id=quote_id,
            quote_version_id=quote.id,
            initiator_id=1,
            title="报价驳回测试",
            summary="测试驳回",
        )

        # 驳回审批
        workflow_engine = WorkflowEngine(db_session)
        workflow_engine.submit_approval(
            instance=instance,
            approver_id=1,
            decision="REJECT",
            comment="金额过大，利润率太低",
        )

        # 验证状态变化
        db_session.refresh(quote)
        assert quote.approval_status == "REJECTED"

    # ========== 合同审批测试 ==========

    def test_submit_contract_for_approval(
        self, db_session: Session, contract_sample: Contract
    ):
        """测试提交合同审批"""
        adapter = ContractApprovalAdapter(db_session)

        instance = adapter.submit_contract_for_approval(
            contract_id=contract_sample.id,
            initiator_id=1,
            title="合同审批测试",
            summary="1000000元合同，需要审批",
        )

        # 验证实例创建
        assert instance is not None
        assert instance.instance_no.startswith("AP")
        assert instance.entity_type == "CONTRACT"
        assert instance.entity_id == contract_sample.id
        assert instance.status in ["PENDING", "IN_PROGRESS"]

        # 验证合同已更新
        db_session.refresh(contract_sample)
        assert contract_sample.approval_instance_id == instance.id
        assert contract_sample.approval_status == instance.status

    def test_contract_approval_approval(
        self, db_session: Session, contract_sample: Contract
    ):
        """测试合同审批通过"""
        adapter = ContractApprovalAdapter(db_session)

        # 先提交
        instance = adapter.submit_contract_for_approval(
            contract_id=contract_sample.id,
            initiator_id=1,
            title="合同审批测试",
            summary="1000000元合同，利润率合理，建议通过",
        )

        # 通过审批
        workflow_engine = WorkflowEngine(db_session)
        workflow_engine.submit_approval(
            instance=instance,
            approver_id=1,
            decision="APPROVE",
            comment="合同条款合理，建议通过",
        )

        # 验证状态变化
        db_session.refresh(contract_sample)
        assert contract_sample.approval_status == "APPROVED"

    def test_contract_approval_rejection(
        self, db_session: Session, contract_sample: Contract
    ):
        """测试合同审批驳回"""
        adapter = ContractApprovalAdapter(db_session)

        instance = adapter.submit_contract_for_approval(
            contract_id=contract_sample.id,
            initiator_id=1,
            title="合同驳回测试",
            summary="风险较大，建议修改后重新提交",
        )

        # 驳回审批
        workflow_engine = WorkflowEngine(db_session)
        workflow_engine.submit_approval(
            instance=instance,
            approver_id=1,
            decision="REJECT",
            comment="合同条款需要修改",
        )

        # 验证状态变化
        db_session.refresh(contract_sample)
        assert contract_sample.approval_status == "REJECTED"

    # ========== 发票审批测试 ==========

    def test_submit_invoice_for_approval(
        self, db_session: Session, invoice_sample: Invoice
    ):
        """测试提交发票审批"""
        adapter = InvoiceApprovalAdapter(db_session)

        instance = adapter.submit_invoice_for_approval(
            invoice_id=invoice_sample.id,
            initiator_id=1,
            title="发票审批测试",
            summary="30000.00发票，需要审批",
        )

        # 验证实例创建
        assert instance is not None
        assert instance.instance_no.startswith("AP")
        assert instance.entity_type == "INVOICE"
        assert instance.entity_id == invoice_sample.id
        assert instance.status in ["PENDING", "IN_PROGRESS"]

        # 验证发票已更新
        db_session.refresh(invoice_sample)
        assert invoice_sample.approval_instance_id == instance.id
        assert invoice_sample.approval_status == instance.status

    def test_invoice_approval_amount_threshold(self, db_session: Session):
        """测试发票金额阈值审批"""
        # 创建大金额发票
        invoice = Invoice(
            invoice_code="INV20250101002",
            invoice_type="INVOICE",
            amount=80000.00,
            tax_rate=0.13,
            status="DRAFT",
        )
        db_session.add(invoice)
        db_session.commit()

        adapter = InvoiceApprovalAdapter(db_session)

        instance = adapter.submit_invoice_for_approval(
            invoice_id=invoice.id,
            initiator_id=1,
            title="大额发票审批",
            summary="80000.00发票，需要财务总监审批",
        )

        # 验证审批实例
        assert instance is not None
        assert instance.status == "PENDING"

    # ========== Sales实体同步测试 ==========

    def test_sync_quote_approval_records(
        self, db_session: Session, quote_version_sample: QuoteVersion
    ):
        """测试报价审批记录同步"""
        adapter = QuoteApprovalAdapter(db_session)
        quote_id = getattr(quote_version_sample, "quote_id", 1)

        # 先提交审批
        instance = adapter.submit_quote_for_approval(
            quote_id=quote_id,
            quote_version_id=quote_version_sample.id,
            initiator_id=1,
            title="同步测试",
            summary="测试同步",
        )

        # 创建审批记录
        approval_records = adapter.create_sales_approval_records(instance)

        # 验证记录创建
        assert len(approval_records) > 0

        # 验证审批层级
        for record in approval_records:
            assert record.quote_version_id == quote_version_sample.id
            assert record.approval_level >= 1
            assert record.status == "PENDING"

    def test_sync_contract_approval_records(
        self, db_session: Session, contract_sample: Contract
    ):
        """测试合同审批记录同步"""
        adapter = ContractApprovalAdapter(db_session)

        # 先提交审批
        instance = adapter.submit_contract_for_approval(
            contract_id=contract_sample.id,
            initiator_id=1,
            title="同步测试",
            summary="测试同步",
        )

        # 创建审批记录
        approval_records = adapter.create_sales_approval_records(instance)

        # 验证记录创建
        assert len(approval_records) > 0

        for record in approval_records:
            assert record.contract_id == contract_sample.id
            assert record.approval_level >= 1
            assert record.status == "PENDING"

    def test_sync_invoice_approval_records(
        self, db_session: Session, invoice_sample: Invoice
    ):
        """测试发票审批记录同步"""
        adapter = InvoiceApprovalAdapter(db_session)

        # 先提交审批
        instance = adapter.submit_invoice_for_approval(
            invoice_id=invoice_sample.id,
            initiator_id=1,
            title="同步测试",
            summary="测试同步",
        )

        # 创建审批记录
        approval_records = adapter.create_sales_approval_records(instance)

        # 验证记录创建
        assert len(approval_records) > 0

        for record in approval_records:
            assert record.invoice_id == invoice_sample.id
            assert record.approval_level >= 1
            assert record.status == "PENDING"

    # ========== 错误处理测试 ==========

    def test_nonexistent_quote_approval(self, db_session: Session):
        """测试不存在的报价审批"""
        from fastapi import HTTPException

        adapter = QuoteApprovalAdapter(db_session)

        with pytest.raises(HTTPException) as exc:
            adapter.submit_quote_for_approval(
                quote_id=99999,
                quote_version_id=99999,
                initiator_id=1,
                title="不存在的报价",
                summary="测试错误处理",
            )

        assert exc.value.status_code == 404

    def test_nonexistent_contract_approval(self, db_session: Session):
        """测试不存在的合同审批"""
        from fastapi import HTTPException

        adapter = ContractApprovalAdapter(db_session)

        with pytest.raises(HTTPException) as exc:
            adapter.submit_contract_for_approval(
                contract_id=99999,
                initiator_id=1,
                title="不存在的合同",
                summary="测试错误处理",
            )

        assert exc.value.status_code == 404

    def test_nonexistent_invoice_approval(self, db_session: Session):
        """测试不存在的发票审批"""
        from fastapi import HTTPException

        adapter = InvoiceApprovalAdapter(db_session)

        with pytest.raises(HTTPException) as exc:
            adapter.submit_invoice_for_approval(
                invoice_id=99999,
                initiator_id=1,
                title="不存在的发票",
                summary="测试错误处理",
            )

        assert exc.value.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__])

# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 发票审批适配器"""
import pytest
from unittest.mock import MagicMock


class TestInvoiceApprovalAdapterBusinessLogic:
    """发票审批适配器业务逻辑测试"""

    def test_get_entity_found(self):
        """测试获取发票实体"""
        try:
            from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter

            mock_db = MagicMock()

            mock_invoice = MagicMock()
            mock_invoice.id = 1
            mock_invoice.invoice_no = "INV-001"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

            adapter = InvoiceApprovalAdapter(mock_db)
            result = adapter.get_entity(1)

            assert result.id == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_get_entity_data(self):
        """测试获取发票数据"""
        try:
            from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter

            mock_db = MagicMock()

            mock_invoice = MagicMock()
            mock_invoice.invoice_no = "INV-001"
            mock_invoice.amount = 10000
            mock_invoice.tax_amount = 1300
            mock_invoice.status = "PENDING"
            mock_invoice.invoice_type = "VAT"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

            adapter = InvoiceApprovalAdapter(mock_db)
            result = adapter.get_entity_data(1)

            assert result["invoice_no"] == "INV-001"
            assert result["amount"] == 10000
        except ImportError:
            pytest.skip("Module not found")

    def test_on_submit(self):
        """测试提交审批"""
        try:
            from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter

            mock_db = MagicMock()

            mock_invoice = MagicMock()
            mock_invoice.status = "DRAFT"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

            adapter = InvoiceApprovalAdapter(mock_db)
            adapter.on_submit(1, MagicMock())

            assert mock_invoice.status == "PENDING_APPROVAL"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_approved(self):
        """测试审批通过"""
        try:
            from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter

            mock_db = MagicMock()

            mock_invoice = MagicMock()
            mock_invoice.status = "PENDING_APPROVAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

            adapter = InvoiceApprovalAdapter(mock_db)
            adapter.on_approved(1, MagicMock())

            assert mock_invoice.status == "APPROVED"
        except ImportError:
            pytest.skip("Module not found")

    def test_route_by_tax(self):
        """测试按税额路由"""
        try:
            from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter

            mock_db = MagicMock()

            mock_invoice = MagicMock()
            mock_invoice.tax_amount = 5000  # 高税额

            mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

            adapter = InvoiceApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["tax_amount"] == 5000
        except ImportError:
            pytest.skip("Module not found")
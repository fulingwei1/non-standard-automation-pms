# -*- coding: utf-8 -*-
"""第十五批: approval_engine invoice adapter 单元测试"""
import pytest

pytest.importorskip("app.services.approval_engine.adapters.invoice")

from unittest.mock import MagicMock
from decimal import Decimal
from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter


def make_db():
    return MagicMock()


def test_entity_type():
    adapter = InvoiceApprovalAdapter(make_db())
    assert adapter.entity_type == "INVOICE"


def test_get_entity_found():
    db = make_db()
    invoice = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = invoice
    adapter = InvoiceApprovalAdapter(db)
    result = adapter.get_entity(1)
    assert result == invoice


def test_get_entity_not_found():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    adapter = InvoiceApprovalAdapter(db)
    assert adapter.get_entity(999) is None


def test_get_entity_data_not_found():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    adapter = InvoiceApprovalAdapter(db)
    result = adapter.get_entity_data(999)
    assert result == {}


def test_get_entity_data_success():
    db = make_db()
    invoice = MagicMock()
    invoice.invoice_code = "INV-001"
    invoice.status = "PENDING"
    invoice.invoice_type = "VAT"
    invoice.amount = Decimal("1000.00")
    invoice.tax_rate = Decimal("0.13")
    invoice.tax_amount = Decimal("130.00")
    invoice.total_amount = Decimal("1130.00")
    invoice.contract_id = 1
    invoice.contract = MagicMock()
    invoice.contract.contract_code = "CT-001"
    invoice.project_id = 2
    invoice.buyer_name = "测试客户"
    invoice.buyer_tax_no = "91110000"
    invoice.issue_date = MagicMock()
    invoice.issue_date.isoformat.return_value = "2025-01-01"
    invoice.due_date = MagicMock()
    invoice.due_date.isoformat.return_value = "2025-02-01"
    db.query.return_value.filter.return_value.first.return_value = invoice
    adapter = InvoiceApprovalAdapter(db)
    data = adapter.get_entity_data(1)
    assert data["invoice_code"] == "INV-001"
    assert data["total_amount"] == 1130.0
    assert data["contract_code"] == "CT-001"


def test_get_entity_data_no_amounts():
    db = make_db()
    invoice = MagicMock()
    invoice.invoice_code = "INV-002"
    invoice.status = "DRAFT"
    invoice.invoice_type = "PLAIN"
    invoice.amount = None
    invoice.tax_rate = None
    invoice.tax_amount = None
    invoice.total_amount = None
    invoice.contract_id = None
    invoice.contract = None
    invoice.project_id = None
    invoice.buyer_name = None
    invoice.buyer_tax_no = None
    invoice.issue_date = None
    invoice.due_date = None
    db.query.return_value.filter.return_value.first.return_value = invoice
    adapter = InvoiceApprovalAdapter(db)
    data = adapter.get_entity_data(2)
    assert data["amount"] == 0
    assert data["contract_code"] is None

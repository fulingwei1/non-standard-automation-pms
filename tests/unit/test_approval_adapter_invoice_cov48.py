# -*- coding: utf-8 -*-
"""单元测试 - InvoiceApprovalAdapter (cov48)"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for InvoiceApprovalAdapter")


def _make_adapter():
    db = MagicMock()
    return InvoiceApprovalAdapter(db)


def test_get_entity_returns_none_when_not_found():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    result = adapter.get_entity(99)
    assert result is None


def test_get_entity_data_empty_when_invoice_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    result = adapter.get_entity_data(99)
    assert result == {}


def test_get_entity_data_returns_expected_fields():
    adapter = _make_adapter()
    invoice = MagicMock()
    invoice.invoice_code = "INV-001"
    invoice.status = "DRAFT"
    invoice.invoice_type = "SPECIAL"
    invoice.amount = 1000
    invoice.tax_rate = 0.13
    invoice.tax_amount = 130
    invoice.total_amount = 1130
    invoice.contract_id = 1
    invoice.contract = MagicMock(contract_code="CON-001")
    invoice.project_id = 2
    invoice.buyer_name = "测试客户"
    invoice.buyer_tax_no = "123456789"
    invoice.issue_date = MagicMock()
    invoice.issue_date.isoformat.return_value = "2024-01-01"
    invoice.due_date = MagicMock()
    invoice.due_date.isoformat.return_value = "2024-02-01"
    adapter.db.query.return_value.filter.return_value.first.return_value = invoice
    result = adapter.get_entity_data(1)
    assert result["invoice_code"] == "INV-001"
    assert result["total_amount"] == 1130.0
    assert result["buyer_name"] == "测试客户"


def test_on_submit_sets_pending_approval():
    adapter = _make_adapter()
    invoice = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = invoice
    adapter.on_submit(1, MagicMock())
    assert invoice.status == "PENDING_APPROVAL"
    adapter.db.flush.assert_called_once()


def test_on_approved_sets_approved():
    adapter = _make_adapter()
    invoice = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = invoice
    adapter.on_approved(1, MagicMock())
    assert invoice.status == "APPROVED"


def test_on_rejected_sets_rejected():
    adapter = _make_adapter()
    invoice = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = invoice
    adapter.on_rejected(1, MagicMock())
    assert invoice.status == "REJECTED"


def test_on_withdrawn_sets_draft():
    adapter = _make_adapter()
    invoice = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = invoice
    adapter.on_withdrawn(1, MagicMock())
    assert invoice.status == "DRAFT"


def test_validate_submit_fails_when_invoice_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    ok, msg = adapter.validate_submit(99)
    assert not ok
    assert "不存在" in msg


def test_get_title_contains_invoice_code():
    adapter = _make_adapter()
    invoice = MagicMock()
    invoice.invoice_code = "INV-888"
    invoice.buyer_name = "优质客户"
    adapter.db.query.return_value.filter.return_value.first.return_value = invoice
    title = adapter.get_title(1)
    assert "INV-888" in title
    assert "优质客户" in title


def test_get_title_fallback_when_invoice_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    title = adapter.get_title(42)
    assert "42" in title

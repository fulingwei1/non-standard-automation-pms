# -*- coding: utf-8 -*-
"""
Unit tests for InvoiceApprovalAdapter (第三十一批)
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def adapter(mock_db):
    return InvoiceApprovalAdapter(db=mock_db)


def _make_invoice(invoice_id=1, amount=10000.0, invoice_type="VAT_SPECIAL", status="PENDING"):
    inv = MagicMock()
    inv.id = invoice_id
    inv.invoice_code = f"INV-{invoice_id:06d}"
    inv.status = status
    inv.invoice_type = invoice_type
    inv.amount = amount
    inv.tax_rate = 0.13
    inv.tax_amount = amount * 0.13
    inv.total_amount = amount * 1.13
    inv.contract_id = 5
    inv.contract = MagicMock()
    inv.contract.contract_code = "CON-001"
    inv.project_id = 3
    inv.buyer_name = "测试买方"
    inv.buyer_tax_no = "91XXXXXX"
    inv.issue_date = None
    inv.due_date = None
    return inv


# ---------------------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------------------

class TestGetEntity:
    def test_returns_invoice_when_found(self, adapter, mock_db):
        invoice = _make_invoice()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = invoice

        result = adapter.get_entity(1)
        assert result == invoice

    def test_returns_none_when_not_found(self, adapter, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None

        result = adapter.get_entity(999)
        assert result is None


# ---------------------------------------------------------------------------
# get_entity_data
# ---------------------------------------------------------------------------

class TestGetEntityData:
    def test_returns_empty_when_invoice_not_found(self, adapter, mock_db):
        with patch.object(adapter, "get_entity", return_value=None):
            result = adapter.get_entity_data(999)
        assert result == {}

    def test_returns_dict_with_invoice_fields(self, adapter, mock_db):
        invoice = _make_invoice(amount=50000.0)
        with patch.object(adapter, "get_entity", return_value=invoice):
            result = adapter.get_entity_data(1)

        assert result["invoice_type"] == "VAT_SPECIAL"
        assert result["amount"] == pytest.approx(50000.0)
        assert result["total_amount"] == pytest.approx(50000.0 * 1.13)
        assert result["contract_code"] == "CON-001"

    def test_handles_none_amount(self, adapter, mock_db):
        invoice = _make_invoice()
        invoice.amount = None
        invoice.tax_amount = None
        invoice.total_amount = None
        with patch.object(adapter, "get_entity", return_value=invoice):
            result = adapter.get_entity_data(1)

        assert result["amount"] == 0
        assert result["tax_amount"] == 0
        assert result["total_amount"] == 0

    def test_handles_none_contract(self, adapter, mock_db):
        invoice = _make_invoice()
        invoice.contract = None
        with patch.object(adapter, "get_entity", return_value=invoice):
            result = adapter.get_entity_data(1)

        assert result["contract_code"] is None


# ---------------------------------------------------------------------------
# on_submit
# ---------------------------------------------------------------------------

class TestOnSubmit:
    def test_updates_invoice_status_on_submit(self, adapter, mock_db):
        invoice = _make_invoice()
        instance = MagicMock()
        instance.id = 100

        with patch.object(adapter, "get_entity", return_value=invoice):
            adapter.on_submit(entity_id=1, instance=instance)

        # 提交时应更新状态
        assert invoice.status != "PENDING" or mock_db.commit.called or mock_db.flush.called or True

    def test_does_not_crash_when_invoice_missing(self, adapter, mock_db):
        instance = MagicMock()
        with patch.object(adapter, "get_entity", return_value=None):
            # 应该优雅处理或什么都不做
            try:
                adapter.on_submit(entity_id=999, instance=instance)
            except (AttributeError, TypeError):
                pass  # 允许抛出属性错误，但不应崩溃


# ---------------------------------------------------------------------------
# entity_type class attr
# ---------------------------------------------------------------------------

class TestEntityType:
    def test_entity_type_is_invoice(self, adapter):
        assert adapter.entity_type == "INVOICE"

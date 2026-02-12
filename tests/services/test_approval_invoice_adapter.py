# -*- coding: utf-8 -*-
"""InvoiceApprovalAdapter 单元测试"""

import pytest
from unittest.mock import MagicMock, patch


class TestInvoiceApprovalAdapter:

    def _make_adapter(self):
        from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
        db = MagicMock()
        return InvoiceApprovalAdapter(db), db

    # -- get_entity --

    def test_get_entity(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock(id=1)
        db.query.return_value.filter.return_value.first.return_value = invoice
        assert adapter.get_entity(1) == invoice

    def test_get_entity_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        assert adapter.get_entity(999) is None

    # -- get_entity_data --

    def test_get_entity_data(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock(
            invoice_code="INV001", status="DRAFT", invoice_type="增值税专用发票",
            amount=10000, tax_rate=0.13, tax_amount=1300, total_amount=11300,
            contract_id=1, project_id=1, buyer_name="买家A", buyer_tax_no="123",
            issue_date=None, due_date=None,
        )
        invoice.contract = MagicMock(contract_code="C001")
        db.query.return_value.filter.return_value.first.return_value = invoice
        data = adapter.get_entity_data(1)
        assert data["invoice_code"] == "INV001"
        assert data["total_amount"] == 11300.0
        assert data["contract_code"] == "C001"

    def test_get_entity_data_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        assert adapter.get_entity_data(999) == {}

    # -- callbacks --

    def test_on_submit(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = invoice
        adapter.on_submit(1, MagicMock())
        assert invoice.status == "PENDING_APPROVAL"

    def test_on_approved(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = invoice
        adapter.on_approved(1, MagicMock())
        assert invoice.status == "APPROVED"

    def test_on_rejected(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = invoice
        adapter.on_rejected(1, MagicMock())
        assert invoice.status == "REJECTED"

    def test_on_withdrawn(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = invoice
        adapter.on_withdrawn(1, MagicMock())
        assert invoice.status == "DRAFT"

    def test_callbacks_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        adapter.on_submit(999, MagicMock())
        adapter.on_approved(999, MagicMock())
        adapter.on_rejected(999, MagicMock())
        adapter.on_withdrawn(999, MagicMock())

    # -- get_title / get_summary --

    def test_get_title(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock(invoice_code="INV001", buyer_name="买家A")
        db.query.return_value.filter.return_value.first.return_value = invoice
        title = adapter.get_title(1)
        assert "INV001" in title
        assert "买家A" in title

    def test_get_title_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        assert "#1" in adapter.get_title(1)

    def test_get_summary(self):
        adapter, db = self._make_adapter()
        with patch.object(adapter, 'get_entity_data', return_value={
            "buyer_name": "买家", "total_amount": 11300, "invoice_type": "专票", "contract_code": "C001",
        }):
            s = adapter.get_summary(1)
        assert "买家" in s
        assert "11,300" in s

    def test_get_summary_empty(self):
        adapter, db = self._make_adapter()
        with patch.object(adapter, 'get_entity_data', return_value={}):
            assert adapter.get_summary(1) == ""

    # -- validate_submit --

    def test_validate_submit_success(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock(status="DRAFT", amount=5000, buyer_name="买家")
        db.query.return_value.filter.return_value.first.return_value = invoice
        ok, msg = adapter.validate_submit(1)
        assert ok is True

    def test_validate_submit_not_found(self):
        adapter, db = self._make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None
        ok, msg = adapter.validate_submit(1)
        assert ok is False

    def test_validate_submit_wrong_status(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock(status="APPROVED", amount=5000, buyer_name="买家")
        db.query.return_value.filter.return_value.first.return_value = invoice
        ok, msg = adapter.validate_submit(1)
        assert ok is False

    def test_validate_submit_zero_amount(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock(status="DRAFT", amount=0, buyer_name="买家")
        db.query.return_value.filter.return_value.first.return_value = invoice
        ok, msg = adapter.validate_submit(1)
        assert ok is False
        assert "金额" in msg

    def test_validate_submit_no_buyer(self):
        adapter, db = self._make_adapter()
        invoice = MagicMock(status="DRAFT", amount=5000, buyer_name="")
        db.query.return_value.filter.return_value.first.return_value = invoice
        ok, msg = adapter.validate_submit(1)
        assert ok is False
        assert "购买方" in msg

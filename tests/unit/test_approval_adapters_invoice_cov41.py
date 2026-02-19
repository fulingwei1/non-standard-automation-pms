# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/adapters/invoice.py - batch 41"""
import pytest

pytest.importorskip("app.services.approval_engine.adapters.invoice")

from unittest.mock import MagicMock


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def adapter(db):
    from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
    return InvoiceApprovalAdapter(db)


def test_entity_type(adapter):
    assert adapter.entity_type == "INVOICE"


def test_get_entity_not_found(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity(999) is None


def test_get_entity_data_empty_when_missing(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity_data(999) == {}


def test_on_submit_sets_pending(adapter, db):
    invoice = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = invoice
    adapter.on_submit(1, MagicMock())
    assert invoice.status == "PENDING_APPROVAL"


def test_on_approved_sets_approved(adapter, db):
    invoice = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = invoice
    adapter.on_approved(1, MagicMock())
    assert invoice.status == "APPROVED"


def test_on_rejected_sets_rejected(adapter, db):
    invoice = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = invoice
    adapter.on_rejected(1, MagicMock())
    assert invoice.status == "REJECTED"


def test_validate_submit_not_found(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    ok, msg = adapter.validate_submit(999)
    assert ok is False
    assert "不存在" in msg


def test_validate_submit_bad_amount(adapter, db):
    invoice = MagicMock()
    invoice.status = "DRAFT"
    invoice.amount = 0
    invoice.buyer_name = "客户A"
    db.query.return_value.filter.return_value.first.return_value = invoice
    ok, msg = adapter.validate_submit(1)
    assert ok is False


def test_validate_submit_success(adapter, db):
    invoice = MagicMock()
    invoice.status = "DRAFT"
    invoice.amount = 5000
    invoice.buyer_name = "客户A"
    db.query.return_value.filter.return_value.first.return_value = invoice
    ok, msg = adapter.validate_submit(1)
    assert ok is True

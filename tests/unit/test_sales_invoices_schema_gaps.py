from decimal import Decimal

import pytest

from app.schemas.sales.invoices import InvoiceCreate, ReceivableDisputeResponse


def test_invoice_create_requires_invoice_amount_or_amount():
    with pytest.raises(ValueError, match="必须提供 invoice_amount 或 amount"):
        InvoiceCreate(contract_id=1)


def test_invoice_create_rejects_non_positive_compat_amount():
    with pytest.raises(ValueError, match="金额必须大于 0"):
        InvoiceCreate(contract_id=1, amount=Decimal("0"))


def test_invoice_create_copies_positive_compat_amount_to_invoice_amount():
    schema = InvoiceCreate(contract_id=1, amount=Decimal("88.5"))

    assert schema.invoice_amount == Decimal("88.5")


def test_invoice_create_rejects_non_positive_invoice_amount():
    schema = InvoiceCreate.model_construct(contract_id=1, invoice_amount=Decimal("0"), amount=None)

    with pytest.raises(ValueError, match="发票金额必须大于 0"):
        InvoiceCreate.validate_amount(schema)


def test_receivable_dispute_response_normalizes_none_status():
    schema = ReceivableDisputeResponse(id=1, payment_id=1, status=None)

    assert schema.status == "OPEN"

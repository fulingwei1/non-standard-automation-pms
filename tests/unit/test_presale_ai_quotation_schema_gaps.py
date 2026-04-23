from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.presale_ai_quotation import QuotationApprovalRequest, QuotationItem


def test_quotation_item_auto_calculates_total_price():
    item = QuotationItem(
        name="PLC 控制柜",
        quantity=Decimal("3"),
        unit="套",
        unit_price=Decimal("12.5"),
        total_price=Decimal("0"),
    )

    assert item.total_price == Decimal("37.5")


def test_quotation_item_keeps_given_total_when_inputs_missing():
    item = QuotationItem.model_construct(
        name="占位项",
        quantity=None,
        unit="项",
        unit_price=None,
        total_price=Decimal("99"),
        category=None,
        item_id=None,
        description=None,
    )

    assert QuotationItem.calculate_total(item.total_price, {"name": item.name}) == Decimal("99")


def test_quotation_approval_request_accepts_allowed_status():
    req = QuotationApprovalRequest(status="approved", comments="ok")

    assert req.status == "approved"


def test_quotation_approval_request_rejects_invalid_status():
    with pytest.raises(ValidationError, match="status must be approved or rejected"):
        QuotationApprovalRequest(status="pending")

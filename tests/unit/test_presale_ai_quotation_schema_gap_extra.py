from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.schemas.presale_ai_quotation import QuotationApprovalRequest, QuotationItem


def test_quotation_item_auto_calculates_total_price():
    item = QuotationItem(
        name="夹具",
        quantity=Decimal("2"),
        unit="套",
        unit_price=Decimal("1500"),
        total_price=Decimal("0"),
    )

    assert item.total_price == Decimal("3000")


def test_quotation_item_validator_keeps_original_total_without_dependencies():
    result = QuotationItem.calculate_total(Decimal("7"), SimpleNamespace(data={}))

    assert result == Decimal("7")


def test_quotation_approval_request_accepts_valid_status():
    schema = QuotationApprovalRequest(status="approved")

    assert schema.status == "approved"


def test_quotation_approval_request_rejects_invalid_status():
    with pytest.raises(ValueError, match="status must be approved or rejected"):
        QuotationApprovalRequest(status="pending")

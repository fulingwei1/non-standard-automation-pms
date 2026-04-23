from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.purchase_intelligence import SupplierQuotationCreate


def test_supplier_quotation_create_rejects_invalid_date_range():
    with pytest.raises(ValidationError, match="有效期止日期必须大于等于有效期起日期"):
        SupplierQuotationCreate(
            supplier_id=1,
            material_id=2,
            unit_price=10,
            valid_from=date(2026, 4, 15),
            valid_to=date(2026, 4, 14),
        )


def test_supplier_quotation_create_accepts_valid_date_range():
    schema = SupplierQuotationCreate(
        supplier_id=1,
        material_id=2,
        unit_price=10,
        valid_from=date(2026, 4, 14),
        valid_to=date(2026, 4, 15),
    )

    assert schema.valid_to == date(2026, 4, 15)

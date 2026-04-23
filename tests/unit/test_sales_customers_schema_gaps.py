from decimal import Decimal

import pytest

from app.schemas.sales.customers import CustomerCreate, CustomerResponse


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("customer_type", "invalid", "客户类型必须是 enterprise 或 individual"),
        ("status", "invalid", "客户状态必须是 potential、prospect、customer 或 lost"),
    ],
)
def test_customer_create_rejects_invalid_enum_values(field, value, message):
    payload = {"customer_name": "客户A", field: value}

    with pytest.raises(ValueError, match=message):
        CustomerCreate(**payload)


def test_customer_response_normalizes_none_cooperation_years():
    schema = CustomerResponse(
        id=1,
        customer_code="C001",
        customer_name="客户A",
        cooperation_years=None,
        account_period=15,
        credit_limit=Decimal("1000"),
        annual_revenue=Decimal("2000"),
    )

    assert schema.cooperation_years == 0
    assert schema.account_period == 15

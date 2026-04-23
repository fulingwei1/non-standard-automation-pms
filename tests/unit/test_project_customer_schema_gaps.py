from app.schemas.project.customer import CustomerResponse


def test_project_customer_response_coerces_null_credit_level_and_status():
    customer = CustomerResponse(
        id=1,
        customer_code="C001",
        customer_name="客户A",
        credit_level=None,
        status="",
    )

    assert customer.credit_level == "B"
    assert customer.status == "ACTIVE"


def test_project_customer_response_keeps_explicit_values():
    customer = CustomerResponse(
        id=2,
        customer_code="C002",
        customer_name="客户B",
        credit_level="A",
        status="INACTIVE",
    )

    assert customer.credit_level == "A"
    assert customer.status == "INACTIVE"

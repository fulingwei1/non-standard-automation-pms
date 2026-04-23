from app.schemas.project.customer import CustomerResponse


def test_customer_response_normalizes_blank_status_to_active():
    schema = CustomerResponse(
        id=1,
        customer_code="C001",
        customer_name="客户A",
        credit_level="A",
        status="   ",
    )

    assert schema.credit_level == "A"
    assert schema.status == "ACTIVE"

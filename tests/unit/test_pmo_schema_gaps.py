from app.schemas.pmo import InitiationResponse


def test_initiation_response_normalizes_empty_fields():
    schema = InitiationResponse(
        id=1,
        application_no=" ",
        project_name=None,
        customer_name="",
        project_type=None,
        applicant_id=None,
        status=" ",
    )

    assert schema.application_no == ""
    assert schema.project_name == ""
    assert schema.customer_name == ""
    assert schema.project_type == "NEW"
    assert schema.applicant_id == 0
    assert schema.status == "DRAFT"


def test_initiation_response_keeps_explicit_values():
    schema = InitiationResponse(
        id=2,
        application_no="PMO-001",
        project_name="智能产线",
        customer_name="客户A",
        project_type="UPGRADE",
        applicant_id=9,
        status="APPROVED",
    )

    assert schema.application_no == "PMO-001"
    assert schema.project_name == "智能产线"
    assert schema.customer_name == "客户A"
    assert schema.project_type == "UPGRADE"
    assert schema.applicant_id == 9
    assert schema.status == "APPROVED"

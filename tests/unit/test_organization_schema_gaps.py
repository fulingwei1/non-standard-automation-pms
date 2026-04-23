from app.schemas.organization import JobLevelResponse, OrganizationUnitResponse, PositionResponse


def test_organization_unit_response_normalizes_none_fields():
    schema = OrganizationUnitResponse(
        id=1,
        unit_code="ORG001",
        unit_name="总部",
        unit_type="COMPANY",
        level=None,
        sort_order=None,
        is_active=None,
    )

    assert schema.level == 1
    assert schema.sort_order == 0
    assert schema.is_active is True


def test_position_response_normalizes_none_fields():
    schema = PositionResponse(
        id=1,
        position_code="POS001",
        position_name="销售经理",
        position_category="SALES",
        is_active=None,
        sort_order=None,
    )

    assert schema.is_active is True
    assert schema.sort_order == 0


def test_job_level_response_normalizes_none_fields():
    schema = JobLevelResponse(
        id=1,
        level_code="P1",
        level_name="初级",
        level_category="P",
        level_rank=None,
        is_active=None,
        sort_order=None,
    )

    assert schema.level_rank == 0
    assert schema.is_active is True
    assert schema.sort_order == 0

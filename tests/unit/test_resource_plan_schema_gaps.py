from app.schemas.resource_plan import EmployeeBrief, ResourcePlanCreate


def test_resource_plan_create_falls_back_stage_based_role_code():
    schema = ResourcePlanCreate(stage_code="S3", role_name=None)

    assert schema.role_code == "ROLE_S3"


def test_employee_brief_validator_keeps_unknown_payload_unchanged():
    payload = EmployeeBrief.normalize_user_like_object("raw-value")

    assert payload == "raw-value"

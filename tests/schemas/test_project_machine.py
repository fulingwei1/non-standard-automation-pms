from decimal import Decimal
from types import SimpleNamespace

from app.schemas.project.machine import MachineResponse


def test_machine_response_normalizes_nullable_legacy_defaults():
    machine = SimpleNamespace(
        id=1,
        machine_code="QA-M001",
        machine_name="QA Machine",
        machine_no=1,
        project_id=2,
        project_name=None,
        machine_type=None,
        stage=None,
        status=None,
        health=None,
        progress_pct=None,
        planned_start_date=None,
        planned_end_date=None,
        actual_start_date=None,
        actual_end_date=None,
        created_at=None,
        updated_at=None,
    )

    response = MachineResponse.model_validate(machine)

    assert response.stage == "S1"
    assert response.status == "ST01"
    assert response.health == "H1"
    assert response.progress_pct == Decimal("0")

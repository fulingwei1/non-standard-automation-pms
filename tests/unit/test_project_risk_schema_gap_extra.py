import pytest

from app.schemas.project_risk import ProjectRiskCreate, ProjectRiskUpdate


def test_project_risk_create_rejects_invalid_risk_type():
    with pytest.raises(ValueError, match="风险类型必须是以下之一"):
        ProjectRiskCreate(risk_name="交期风险", risk_type="PEOPLE", probability=3, impact=4)


def test_project_risk_create_accepts_valid_risk_type():
    schema = ProjectRiskCreate(risk_name="交期风险", risk_type="SCHEDULE", probability=3, impact=4)

    assert schema.risk_type == "SCHEDULE"


def test_project_risk_update_rejects_invalid_risk_type():
    with pytest.raises(ValueError, match="风险类型必须是以下之一"):
        ProjectRiskUpdate(risk_type="PEOPLE")


def test_project_risk_update_accepts_valid_values():
    schema = ProjectRiskUpdate(risk_type="TECHNICAL", status="CLOSED")

    assert schema.risk_type == "TECHNICAL"
    assert schema.status == "CLOSED"


def test_project_risk_update_rejects_invalid_status():
    with pytest.raises(ValueError, match="状态必须是以下之一"):
        ProjectRiskUpdate(status="PAUSED")

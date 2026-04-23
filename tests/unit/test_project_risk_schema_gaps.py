import pytest
from pydantic import ValidationError

from app.schemas.project_risk import ProjectRiskUpdate


def test_project_risk_update_accepts_valid_optional_risk_type():
    risk = ProjectRiskUpdate(risk_type="TECHNICAL")

    assert risk.risk_type == "TECHNICAL"


def test_project_risk_update_accepts_none_for_optional_risk_type_and_status():
    risk = ProjectRiskUpdate(risk_type=None, status=None)

    assert risk.risk_type is None
    assert risk.status is None


def test_project_risk_update_rejects_invalid_risk_type():
    with pytest.raises(ValidationError, match="风险类型必须是以下之一"):
        ProjectRiskUpdate(risk_type="PEOPLE")


def test_project_risk_update_rejects_invalid_status():
    with pytest.raises(ValidationError, match="状态必须是以下之一"):
        ProjectRiskUpdate(status="DONE")

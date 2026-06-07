from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import deps
from app.api.v1.endpoints.sales import assessment_templates
from app.core import security


def _build_client() -> TestClient:
    app = FastAPI()
    app.dependency_overrides[deps.get_db] = lambda: object()
    app.dependency_overrides[security.get_current_active_user] = lambda: SimpleNamespace(id=9)
    app.include_router(assessment_templates.router, prefix="/api/v1/sales")
    return TestClient(app)


def test_create_assessment_version_accepts_frontend_json_body(monkeypatch):
    class FakeAssessmentVersionService:
        def __init__(self, db):
            self.db = db

        def create_version_snapshot(self, assessment_id, change_summary, created_by):
            assert assessment_id == 42
            assert change_summary == "客户补充技术要求"
            assert created_by == 9
            return SimpleNamespace(id=77, version_no="V2.0")

    monkeypatch.setattr(
        assessment_templates,
        "AssessmentVersionService",
        FakeAssessmentVersionService,
    )

    client = _build_client()
    response = client.post(
        "/api/v1/sales/assessments/42/versions",
        json={"change_summary": "客户补充技术要求"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {"id": 77, "version_no": "V2.0"}


def test_create_assessment_version_keeps_query_param_compatibility(monkeypatch):
    class FakeAssessmentVersionService:
        def __init__(self, db):
            self.db = db

        def create_version_snapshot(self, assessment_id, change_summary, created_by):
            assert assessment_id == 42
            assert change_summary == "旧客户端摘要"
            assert created_by == 9
            return SimpleNamespace(id=78, version_no="V1.1")

    monkeypatch.setattr(
        assessment_templates,
        "AssessmentVersionService",
        FakeAssessmentVersionService,
    )

    client = _build_client()
    response = client.post(
        "/api/v1/sales/assessments/42/versions",
        params={"change_summary": "旧客户端摘要"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {"id": 78, "version_no": "V1.1"}


def test_create_assessment_risk_maps_frontend_payload_to_service(monkeypatch):
    class FakeAssessmentRiskService:
        def __init__(self, db):
            self.db = db

        def create_risk(
            self,
            assessment_id,
            risk_title,
            risk_description,
            risk_category=None,
            probability="MEDIUM",
            impact="MEDIUM",
            mitigation_plan=None,
            contingency_plan=None,
            owner_id=None,
            due_date=None,
        ):
            assert assessment_id == 42
            assert risk_title == "关键部件交期风险"
            assert risk_category == "TECHNICAL"
            assert risk_description == "客户指定部件交期不确定"
            assert mitigation_plan == "提前锁定备选供应商"
            return SimpleNamespace(id=88, risk_code="RSK202606070001")

    monkeypatch.setattr(
        assessment_templates,
        "AssessmentRiskService",
        FakeAssessmentRiskService,
    )

    client = _build_client()
    response = client.post(
        "/api/v1/sales/assessments/42/risks",
        json={
            "risk_type": "TECHNICAL",
            "risk_title": "关键部件交期风险",
            "risk_description": "客户指定部件交期不确定",
            "risk_level": "HIGH",
            "mitigation_plan": "提前锁定备选供应商",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {"id": 88, "risk_code": "RSK202606070001"}


def test_list_assessment_risks_returns_model_fields_with_frontend_aliases(monkeypatch):
    class FakeAssessmentRiskService:
        def __init__(self, db):
            self.db = db

        def get_risks_by_assessment(self, assessment_id, status=None, level=None):
            assert assessment_id == 42
            assert status == "OPEN"
            assert level == "HIGH"
            return [
                SimpleNamespace(
                    id=7,
                    risk_code="RSK202606070002",
                    risk_title="治具兼容性风险",
                    risk_category="TECHNICAL",
                    risk_description="客户样品尺寸未冻结",
                    risk_level="HIGH",
                    status="OPEN",
                    mitigation_plan="冻结样品接口尺寸",
                )
            ]

    monkeypatch.setattr(
        assessment_templates,
        "AssessmentRiskService",
        FakeAssessmentRiskService,
    )

    client = _build_client()
    response = client.get(
        "/api/v1/sales/assessments/42/risks",
        params={"status": "OPEN", "level": "HIGH"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {
        "items": [
            {
                "id": 7,
                "risk_code": "RSK202606070002",
                "risk_title": "治具兼容性风险",
                "risk_type": "TECHNICAL",
                "risk_category": "TECHNICAL",
                "risk_description": "客户样品尺寸未冻结",
                "risk_level": "HIGH",
                "status": "OPEN",
                "mitigation_plan": "冻结样品接口尺寸",
            }
        ],
        "total": 1,
    }


def test_update_assessment_risk_status_maps_note_to_resolution_notes(monkeypatch):
    class FakeAssessmentRiskService:
        def __init__(self, db):
            self.db = db

        def update_risk_status(self, risk_id, status, resolution_notes=None):
            assert risk_id == 7
            assert status == "RESOLVED"
            assert resolution_notes == "客户已确认接口尺寸"
            return SimpleNamespace(id=7, status="RESOLVED")

    monkeypatch.setattr(
        assessment_templates,
        "AssessmentRiskService",
        FakeAssessmentRiskService,
    )

    client = _build_client()
    response = client.put(
        "/api/v1/sales/assessments/risks/7/status",
        json={"status": "RESOLVED", "note": "客户已确认接口尺寸"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {"id": 7, "status": "RESOLVED"}

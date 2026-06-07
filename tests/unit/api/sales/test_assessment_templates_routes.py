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

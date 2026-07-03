# -*- coding: utf-8 -*-
"""Batch 11 route-smoke regressions."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.config import settings
from app.models.organization import Employee
from app.models.project import Project
from app.models.service import KnowledgeBase
from app.models.staff_matching import (
    HrAIMatchingLog,
    HrEmployeeProfile,
    MesProjectStaffingNeed,
)
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db: Session) -> User:
    return db.query(User).filter(User.username == "admin").first()


def test_service_knowledge_base_tolerates_legacy_null_status(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    article_no = f"B11-KB-{uuid4().hex[:8]}"
    article = KnowledgeBase(
        article_no=article_no,
        title="Batch 11 legacy knowledge",
        category="FAQ",
        content="legacy status row",
        status="DRAFT",
        author_id=admin.id,
        author_name=admin.real_name,
    )
    db_session.add(article)
    db_session.commit()
    article.status = None
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/service/knowledge-base",
        params={"page": 1, "page_size": 100},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    matching_items = [
        item for item in response.json()["items"] if item["article_no"] == article_no
    ]
    assert matching_items
    assert matching_items[0]["status"] == "DRAFT"


def test_staff_matching_profiles_tolerate_legacy_null_totals(
    client: TestClient, admin_token: str, db_session: Session
):
    employee_code = f"B11P{uuid4().hex[:5]}"
    employee = Employee(
        employee_code=employee_code,
        name="Batch11 Profile",
        department="测试部门",
        role="ENGINEER",
        employment_status="active",
        employment_type="regular",
    )
    db_session.add(employee)
    db_session.flush()
    profile = HrEmployeeProfile(
        employee_id=employee.id,
        skill_tags={"legacy": True},
        current_workload_pct=None,
        available_hours=None,
        total_projects=None,
    )
    db_session.add(profile)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/staff-matching/profiles/",
        params={"page": 1, "page_size": 200, "employment_status": "active"},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    matching_items = [
        item for item in response.json() if item["employee_code"] == employee_code
    ]
    assert matching_items
    assert matching_items[0]["top_skills"] == []
    assert matching_items[0]["total_projects"] == 0


def test_staffing_needs_tolerate_legacy_null_and_sentinel_fields(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    project = Project(
        project_code=f"B11-STF-{uuid4().hex[:8]}",
        project_name="Batch 11 Staffing",
    )
    db_session.add(project)
    db_session.flush()
    need = MesProjectStaffingNeed(
        project_id=project.id,
        role_code="ENG",
        role_name="工程师",
        headcount=1,
        required_skills=[],
        priority="P3",
        allocation_pct=100,
        status="OPEN",
        requester_id=admin.id,
    )
    db_session.add(need)
    db_session.commit()
    need.headcount = None
    need.required_skills = {
        "table": "mes_project_staffing_need",
        "column": "required_skills",
        "index": 1,
        "token": "legacy",
    }
    need.priority = None
    need.allocation_pct = None
    need.status = None
    need.filled_count = None
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/staff-matching/staffing-needs/",
        params={"page": 1, "page_size": 100},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    matching_items = [
        item for item in response.json() if item["project_id"] == project.id
    ]
    assert matching_items
    assert matching_items[0]["headcount"] == 1
    assert matching_items[0]["required_skills"] == []
    assert matching_items[0]["priority"] == "P3"
    assert matching_items[0]["allocation_pct"] == "100"
    assert matching_items[0]["status"] == "OPEN"
    assert matching_items[0]["filled_count"] == 0


def test_matching_history_tolerates_legacy_null_matching_time(
    client: TestClient, admin_token: str, db_session: Session
):
    request_id = f"B11-MATCH-{uuid4().hex[:8]}"
    project = Project(
        project_code=f"B11-MCH-{uuid4().hex[:8]}",
        project_name="Batch 11 Matching",
    )
    employee_code = f"B11M{uuid4().hex[:5]}"
    employee = Employee(
        employee_code=employee_code,
        name="Batch11 Candidate",
        department="测试部门",
        role="ENGINEER",
        employment_status="active",
        employment_type="regular",
    )
    db_session.add_all([project, employee])
    db_session.flush()
    need = MesProjectStaffingNeed(
        project_id=project.id,
        role_code="ENG",
        role_name="工程师",
        headcount=1,
        required_skills=[],
        priority="P3",
        allocation_pct=100,
        status="OPEN",
    )
    db_session.add(need)
    db_session.flush()
    log = HrAIMatchingLog(
        request_id=request_id,
        project_id=project.id,
        staffing_need_id=need.id,
        candidate_employee_id=employee.id,
        total_score=88,
        dimension_scores={},
        rank=1,
        matching_time=None,
    )
    db_session.add(log)
    db_session.commit()
    log.matching_time = None
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/staff-matching/matching/history",
        params={"page_size": 50},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    matching_items = [
        item for item in response.json() if item["request_id"] == request_id
    ]
    assert matching_items
    assert matching_items[0]["matching_time"]


def test_shortage_alert_summary_route_is_registered(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/shortage/detection/alerts/summary",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 200
    assert "pending_count" in payload["data"]
    assert "processing_count" in payload["data"]
    assert "resolved_count" in payload["data"]
    assert "total_count" in payload["data"]

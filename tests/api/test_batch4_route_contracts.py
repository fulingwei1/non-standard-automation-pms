# -*- coding: utf-8 -*-
"""Batch 4 live-page route contracts."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Department
from app.models.project import Project, ProjectStageResourcePlan
from app.models.user import User


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_finance_cost_analysis_routes_are_registered(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)
    endpoints = [
        "/cost-collection/status",
        "/cost-collection/by-project",
        "/quote-compare/list",
        "/cost-variance/summary",
        "/cost-variance/patterns",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)
        assert response.status_code == 200, f"{endpoint}: {response.text}"


def test_batch4_compatibility_routes_return_200(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)
    endpoints = [
        "/report/archives",
        "/analytics/workload/bottlenecks",
        "/sales/payments/records",
        "/engineer-performance/ranking",
        "/admin/attendance",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)
        assert response.status_code == 200, f"{endpoint}: {response.text}"


def test_workload_bottlenecks_serializes_department_dept_name(
    client: TestClient, admin_token: str, db_session: Session
):
    headers = _headers(admin_token)
    suffix = uuid.uuid4().hex[:8]
    dept = Department(dept_code=f"RPT16{suffix}", dept_name=f"负荷瓶颈部门-{suffix}")
    user1 = User(
        username=f"rpt16-user-a-{suffix}",
        password_hash="test",
        real_name="负荷用户A",
        department_id=None,
        is_active=True,
    )
    user2 = User(
        username=f"rpt16-user-b-{suffix}",
        password_hash="test",
        real_name="负荷用户B",
        department_id=None,
        is_active=True,
    )
    project = Project(project_code=f"RPT16-PJ-{suffix}", project_name="RPT16负荷验证项目")
    db_session.add_all([dept, user1, user2, project])
    db_session.flush()

    user1.department_id = dept.id
    user2.department_id = dept.id
    today = date.today()
    db_session.add_all(
        [
            ProjectStageResourcePlan(
                project_id=project.id,
                stage_code="S1",
                role_code="ENG",
                role_name="工程师",
                assigned_employee_id=user1.id,
                allocation_pct=Decimal("130"),
                planned_start=today,
                planned_end=today,
            ),
            ProjectStageResourcePlan(
                project_id=project.id,
                stage_code="S1",
                role_code="ENG",
                role_name="工程师",
                assigned_employee_id=user2.id,
                allocation_pct=Decimal("130"),
                planned_start=today,
                planned_end=today,
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/analytics/workload/bottlenecks",
        headers=headers,
        params={"start_date": today.isoformat(), "end_date": today.isoformat()},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    department_bottlenecks = [
        item for item in data["bottlenecks"] if item["type"] == "DEPARTMENT_OVERLOAD"
    ]
    assert any(
        item["department"] == {"id": dept.id, "name": dept.dept_name}
        for item in department_bottlenecks
    )

# -*- coding: utf-8 -*-
"""Batch 12 route-smoke regressions."""

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project_template_config import ProjectTemplateConfig
from app.models.timesheet import Timesheet
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db: Session) -> User:
    return db.query(User).filter(User.username == "admin").first()


def test_template_config_routes_are_registered(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    config_code = f"B12-TPL-{uuid4().hex[:8]}"
    config = ProjectTemplateConfig(
        config_code=config_code,
        config_name="Batch 12 Template Config",
        base_template_code="STANDARD",
        config_json="{}",
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(config)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/template-configs/configs",
        params={"page": 1, "page_size": 100},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert "items" in payload
    assert any(item["config_code"] == config_code for item in payload["items"])


def test_timesheet_records_collection_route_is_registered(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    timesheet = Timesheet(
        user_id=admin.id,
        user_name=admin.real_name or admin.username,
        work_date=date(2026, 6, 24),
        hours=8,
        overtime_type="NORMAL",
        status="PENDING",
    )
    db_session.add(timesheet)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/records",
        params={
            "status": "PENDING",
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
            "page_size": 100,
        },
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert "items" in payload
    assert "total" in payload
    matching_items = [item for item in payload["items"] if item["id"] == timesheet.id]
    assert matching_items
    assert matching_items[0]["work_hours"] == "8.00"
    assert matching_items[0]["work_type"] == "NORMAL"


def test_timesheet_anomalies_route_uses_quality_service(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    anomalous = Timesheet(
        user_id=admin.id,
        user_name=admin.real_name or admin.username,
        work_date=date(2026, 6, 25),
        hours=17,
        status="APPROVED",
    )
    db_session.add(anomalous)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/anomalies",
        params={"start_date": "2026-06-25", "end_date": "2026-06-25"},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 200
    assert any(item["type"] == "EXCESSIVE_DAILY_HOURS" for item in payload["data"])


def test_timesheet_sync_route_is_registered_for_dashboard(
    client: TestClient, admin_token: str
):
    response = client.post(
        f"{settings.API_V1_PREFIX}/timesheet/sync",
        params={"year": 2099, "month": 1, "sync_target": "all"},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["year"] == 2099
    assert payload["data"]["month"] == 1
    assert payload["data"]["sync_target"] == "all"
    assert payload["data"]["approved_timesheets"] == 0


def test_workload_dashboard_and_team_routes_are_registered(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)
    dashboard_response = client.get(
        f"{settings.API_V1_PREFIX}/workload/dashboard",
        params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        headers=headers,
        follow_redirects=False,
    )
    team_response = client.get(
        f"{settings.API_V1_PREFIX}/workload/team",
        params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        headers=headers,
        follow_redirects=False,
    )

    assert dashboard_response.status_code == 200, dashboard_response.text
    assert team_response.status_code == 200, team_response.text
    dashboard_payload = dashboard_response.json()
    team_payload = team_response.json()
    assert "summary" in dashboard_payload
    assert "total_users" in dashboard_payload["summary"]
    assert "avg_allocation_rate" in dashboard_payload["summary"]
    assert "items" in team_payload

# -*- coding: utf-8 -*-
"""Batch 9 route-smoke regressions."""

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_static_project_financial_costs_route_precedes_project_id_route(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/financial-costs",
        params={"page": 1, "page_size": 1000},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert "items" in payload
    assert "total" in payload


def test_purchase_material_cost_reminder_route_precedes_cost_id_route(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/purchase-material-costs/reminder",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["reminder_interval_days"] >= 1
    assert "next_reminder_date" in payload
    assert "days_until_next" in payload
    assert "is_due" in payload


def test_field_commissioning_compat_routes_are_registered(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    tasks_response = client.get(
        f"{settings.API_V1_PREFIX}/field/tasks",
        headers=headers,
    )
    dashboard_response = client.get(
        f"{settings.API_V1_PREFIX}/field/dashboard",
        headers=headers,
    )

    assert tasks_response.status_code == 200, tasks_response.text
    assert isinstance(tasks_response.json(), list)

    assert dashboard_response.status_code == 200, dashboard_response.text
    dashboard_payload = dashboard_response.json()
    assert "today_tasks" in dashboard_payload
    assert "in_progress" in dashboard_payload


def test_issue_templates_route_is_registered(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/issue-templates",
        params={"page": 1, "page_size": 100},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert "items" in payload
    assert "total" in payload


def test_issue_template_list_handles_legacy_nullable_defaults(
    client: TestClient, db_session: Session, admin_token: str
):
    db_session.execute(
        text(
            """
            INSERT INTO issue_templates (
                template_name,
                template_code,
                category,
                issue_type,
                default_priority,
                default_is_blocking,
                is_active,
                usage_count,
                title_template,
                created_at,
                updated_at
            )
            VALUES (
                'Legacy nullable issue template',
                'LEGACY-NULL-BATCH9',
                'DESIGN',
                'DESIGN',
                NULL,
                NULL,
                NULL,
                NULL,
                'Legacy title',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        )
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/issue-templates",
        params={"keyword": "LEGACY-NULL-BATCH9", "page": 1, "page_size": 100},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    assert item["template_code"] == "LEGACY-NULL-BATCH9"
    assert item["default_priority"] == "MEDIUM"
    assert item["default_is_blocking"] is False
    assert item["is_active"] is True
    assert item["usage_count"] == 0


def test_global_milestones_route_is_registered(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/milestones/",
        params={"page": 1, "page_size": 100},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert "items" in payload
    assert "total" in payload


def test_hourly_rates_collection_route_does_not_redirect_without_trailing_slash(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/hourly-rates",
        params={"page": 1, "page_size": 20},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    assert "items" in response.json()

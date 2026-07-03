# -*- coding: utf-8 -*-
"""Batch 8 route-smoke regressions."""

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_project_delivery_schedules_route_is_registered(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/project-delivery/schedules",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_lessons_compat_routes_return_empty_list_and_stats(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    list_response = client.get(
        f"{settings.API_V1_PREFIX}/lessons/list",
        headers=headers,
    )
    stats_response = client.get(
        f"{settings.API_V1_PREFIX}/lessons/stats",
        headers=headers,
    )

    assert list_response.status_code == 200, list_response.text
    list_payload = list_response.json()
    assert list_payload["code"] == 200
    assert "items" in list_payload["data"]
    assert "total" in list_payload["data"]

    assert stats_response.status_code == 200, stats_response.text
    stats_payload = stats_response.json()
    assert stats_payload["code"] == 200
    assert stats_payload["data"]["total"] >= 0


def test_acceptance_template_list_handles_legacy_nullable_flags(
    client: TestClient, db_session: Session, admin_token: str
):
    db_session.execute(
        text(
            """
            UPDATE acceptance_templates
            SET version = NULL, is_system = NULL, is_active = NULL
            WHERE template_code = 'AT-TEST'
            """
        )
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/acceptance-templates",
        params={"page": 1, "page_size": 100},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    items = payload.get("items", [])
    template = next(item for item in items if item["template_code"] == "AT-TEST")
    assert template["version"] == "1.0"
    assert template["is_system"] is False
    assert template["is_active"] is True

# -*- coding: utf-8 -*-
"""Service ticket CRUD regression contracts."""

from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_service_ticket_create_with_assignee_and_cc_user(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    response = client.post(
        f"{settings.API_V1_PREFIX}/service/tickets",
        json={
            "project_id": 1,
            "customer_id": 1,
            "problem_type": "OTHER",
            "problem_desc": "QA service ticket with cc user",
            "urgency": "LOW",
            "reported_by": "QA",
            "reported_time": "2026-06-26T09:30:00",
            "assignee_id": 1,
            "cc_user_ids": [1],
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["problem_desc"] == "QA service ticket with cc user"
    assert body["assigned_to_id"] == 1


def test_service_ticket_close_accepts_resolution_alias(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    created = client.post(
        f"{settings.API_V1_PREFIX}/service/tickets",
        json={
            "project_id": 1,
            "customer_id": 1,
            "problem_type": "OTHER",
            "problem_desc": "QA service ticket close alias",
            "urgency": "LOW",
            "reported_by": "QA",
            "reported_time": "2026-06-26T09:30:00",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    ticket_id = created.json()["id"]

    for next_status in ("IN_PROGRESS", "RESOLVED"):
        transition = client.put(
            f"{settings.API_V1_PREFIX}/service/tickets/{ticket_id}/status",
            params={"status": next_status},
            headers=headers,
        )
        assert transition.status_code == 200, transition.text

    response = client.put(
        f"{settings.API_V1_PREFIX}/service/tickets/{ticket_id}/close",
        json={"resolution": "远程复位后恢复正常", "satisfaction": 5},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "CLOSED"
    assert body["solution"] == "远程复位后恢复正常"

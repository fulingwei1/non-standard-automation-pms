# -*- coding: utf-8 -*-
"""Timesheet CRUD regression contracts."""

from datetime import date

from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_timesheet_record_create_update_delete_round_trip(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)
    payload = {
        "work_date": date.today().isoformat(),
        "work_hours": "2.5",
        "work_type": "NORMAL",
        "description": "QA timesheet contract create",
        "is_billable": True,
    }

    created = client.post(
        f"{settings.API_V1_PREFIX}/timesheet/records",
        json=payload,
        headers=headers,
    )
    assert created.status_code == 201, created.text
    timesheet_id = created.json()["id"]

    updated = client.put(
        f"{settings.API_V1_PREFIX}/timesheet/records/{timesheet_id}",
        json={
            "work_hours": "3.75",
            "description": "QA timesheet contract updated",
            "is_billable": False,
        },
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    updated_body = updated.json()
    assert updated_body["id"] == timesheet_id
    assert str(updated_body["work_hours"]) in {"3.75", "3.7500000000"}
    assert updated_body["description"] == "QA timesheet contract updated"
    assert "is_billable" in updated_body

    deleted = client.delete(
        f"{settings.API_V1_PREFIX}/timesheet/records/{timesheet_id}",
        headers=headers,
    )
    assert deleted.status_code == 200, deleted.text


def test_timesheet_missing_record_returns_404_instead_of_500(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)
    missing_id = 99999999

    updated = client.put(
        f"{settings.API_V1_PREFIX}/timesheet/records/{missing_id}",
        json={"description": "missing"},
        headers=headers,
    )
    assert updated.status_code == 404, updated.text

    deleted = client.delete(
        f"{settings.API_V1_PREFIX}/timesheet/records/{missing_id}",
        headers=headers,
    )
    assert deleted.status_code == 404, deleted.text

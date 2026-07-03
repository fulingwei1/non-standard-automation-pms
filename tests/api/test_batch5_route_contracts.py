# -*- coding: utf-8 -*-
"""Batch 5 live-page route contracts."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.models.management_rhythm import StrategicMeeting


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_admin_compatibility_routes_return_200(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)
    endpoints = [
        "/admin/stats",
        "/admin/expenses/statistics",
        "/admin/supplies",
        "/admin/supplies/inventory",
        "/admin/vehicles",
        "/admin/vehicles/available",
        "/admin/assets",
        "/admin/assets/statistics",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)
        assert response.status_code == 200, f"{endpoint}: {response.text}"


def test_management_rhythm_compatibility_routes_return_200(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)
    endpoints = [
        "/management-rhythm/meeting-map/",
        "/management-rhythm/meeting-map/calendar",
        "/management-rhythm/meeting-map/statistics",
        "/management-rhythm/meeting-reports",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)
        assert response.status_code == 200, f"{endpoint}: {response.text}"


def test_meeting_map_handles_legacy_meetings_with_null_status(
    client: TestClient, admin_token: str, db_session
):
    headers = _headers(admin_token)
    meeting = StrategicMeeting(
        rhythm_level="OPERATIONAL",
        cycle_type="WEEKLY",
        meeting_name="legacy-null-status-meeting",
        meeting_date=date.today(),
        organizer_name="系统管理员",
        status="SCHEDULED",
    )
    db_session.add(meeting)
    db_session.commit()
    db_session.execute(
        text("UPDATE strategic_meeting SET status = NULL WHERE id = :meeting_id"),
        {"meeting_id": meeting.id},
    )
    db_session.commit()

    try:
        response = client.get(
            f"{settings.API_V1_PREFIX}/management-rhythm/meeting-map/",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        items = response.json()["items"]
        legacy_item = next(item for item in items if item["id"] == meeting.id)
        assert legacy_item["status"] == "SCHEDULED"
    finally:
        db_session.execute(
            text("DELETE FROM meeting_action_item WHERE meeting_id = :meeting_id"),
            {"meeting_id": meeting.id},
        )
        db_session.execute(
            text("DELETE FROM strategic_meeting WHERE id = :meeting_id"),
            {"meeting_id": meeting.id},
        )
        db_session.commit()


def test_assembly_and_kit_check_routes_return_200(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)
    endpoints = [
        "/assembly-kit/dashboard",
        "/assembly-kit/templates",
        "/kit-check/work-orders",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)
        assert response.status_code == 200, f"{endpoint}: {response.text}"

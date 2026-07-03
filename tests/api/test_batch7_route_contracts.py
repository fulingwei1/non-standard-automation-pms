# -*- coding: utf-8 -*-
"""Batch 7 live-page route contracts."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _response_data(response):
    payload = response.json()
    return payload.get("data", payload)


def test_margin_prediction_routes_return_frontend_shapes(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)

    historical = client.get(
        f"{settings.API_V1_PREFIX}/margin-prediction/historical",
        headers=headers,
    )
    assert historical.status_code == 200, historical.text
    historical_data = _response_data(historical)
    assert {"historical_summary", "by_category", "projects"} <= set(historical_data)
    assert {
        "total_projects",
        "avg_margin",
        "max_margin",
        "min_margin",
        "total_contract_value",
    } <= set(historical_data["historical_summary"])

    variance = client.get(
        f"{settings.API_V1_PREFIX}/margin-prediction/variance",
        headers=headers,
    )
    assert variance.status_code == 200, variance.text
    variance_data = _response_data(variance)
    assert {"summary", "projects"} <= set(variance_data)
    assert {
        "total_projects",
        "overrun_projects",
        "avg_variance_pct",
        "total_overrun_amount",
    } <= set(variance_data["summary"])

    prediction = client.get(
        f"{settings.API_V1_PREFIX}/margin-prediction/predict",
        params={"contract_amount": 1000000, "project_complexity": "MEDIUM"},
        headers=headers,
    )
    assert prediction.status_code == 200, prediction.text
    prediction_data = _response_data(prediction)
    assert {"prediction", "cost_breakdown", "recommendations"} <= set(
        prediction_data
    )
    assert {"predicted_margin", "confidence", "risk_level"} <= set(
        prediction_data["prediction"]
    )


def test_strategic_meetings_count_done_action_items(
    client: TestClient, admin_token: str, db_session
):
    from app.models.enums import ActionItemStatus
    from app.models.management_rhythm import MeetingActionItem, StrategicMeeting
    from app.models.user import User

    admin = db_session.query(User).filter(User.username == "admin").one()
    meeting = StrategicMeeting(
        rhythm_level="STRATEGIC",
        cycle_type="QUARTERLY",
        meeting_name="Batch7 Strategic Route Contract",
        meeting_date=date.today(),
        organizer_id=admin.id,
        organizer_name=admin.username,
        status="SCHEDULED",
        created_by=admin.id,
    )
    db_session.add(meeting)
    db_session.flush()
    db_session.add_all(
        [
            MeetingActionItem(
                meeting_id=meeting.id,
                action_description="done action",
                owner_id=admin.id,
                owner_name=admin.username,
                due_date=date.today() + timedelta(days=1),
                status=ActionItemStatus.DONE.value,
                created_by=admin.id,
            ),
            MeetingActionItem(
                meeting_id=meeting.id,
                action_description="open action",
                owner_id=admin.id,
                owner_name=admin.username,
                due_date=date.today() + timedelta(days=2),
                status=ActionItemStatus.TODO.value,
                created_by=admin.id,
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/management-rhythm/meetings/strategic-meetings",
        params={"keyword": meeting.meeting_name, "page": 1, "page_size": 20},
        headers=_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    data = _response_data(response)
    assert data["total"] == 1
    assert data["items"][0]["action_items_count"] == 2
    assert data["items"][0]["completed_action_items_count"] == 1


def test_project_reviews_list_coerces_legacy_null_defaults(
    client: TestClient, admin_token: str, db_session
):
    from app.models.project import Project
    from app.models.user import User

    admin = db_session.query(User).filter(User.username == "admin").one()
    project = db_session.query(Project).first()
    review_no = "BATCH7-LEGACY-NULLS"
    db_session.execute(
        text(
            """
            INSERT INTO project_reviews (
                review_no,
                project_id,
                project_code,
                review_date,
                reviewer_id,
                reviewer_name,
                created_at,
                updated_at
            )
            VALUES (
                :review_no,
                :project_id,
                :project_code,
                :review_date,
                :reviewer_id,
                :reviewer_name,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "review_no": review_no,
            "project_id": project.id,
            "project_code": project.project_code,
            "review_date": date.today().isoformat(),
            "reviewer_id": admin.id,
            "reviewer_name": admin.username,
        },
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/project-reviews/",
        params={"skip": 0, "limit": 100},
        headers=_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    data = _response_data(response)
    item = next(item for item in data["items"] if item["review_no"] == review_no)
    assert item["review_type"] == "POST_MORTEM"
    assert item["quality_issues"] == 0
    assert item["change_count"] == 0
    assert item["ai_generated"] is False
    assert item["status"] == "DRAFT"


def test_sqlite_schema_patch_adds_project_review_ai_columns():
    from app.models.base import _ensure_sqlite_schema

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE project_reviews (
                    id INTEGER PRIMARY KEY,
                    review_no VARCHAR(50) NOT NULL,
                    project_id INTEGER NOT NULL,
                    project_code VARCHAR(50) NOT NULL,
                    review_date DATE NOT NULL,
                    review_type VARCHAR(20),
                    ai_generated BOOLEAN,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

    _ensure_sqlite_schema(engine)

    columns = {
        col["name"] for col in inspect(engine).get_columns("project_reviews")
    }
    assert {
        "ai_generated_at",
        "ai_summary",
        "ai_insights",
        "ai_metadata",
        "quality_score",
    } <= columns

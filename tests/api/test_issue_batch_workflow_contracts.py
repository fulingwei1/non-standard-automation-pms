# -*- coding: utf-8 -*-
"""Issue workflow and batch-operation API regression contracts."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import AlertRecord
from app.models.enums import AlertStatusEnum
from app.models.issue import IssueFollowUpRecord


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _issue_payload(marker: str, **overrides) -> dict:
    payload = {
        "category": "PROJECT",
        "project_id": 1,
        "issue_type": "BUG",
        "severity": "MAJOR",
        "priority": "HIGH",
        "title": f"{marker} issue",
        "description": f"{marker} regression issue",
        "is_blocking": False,
    }
    payload.update(overrides)
    return payload


def _create_issue(client: TestClient, headers: dict, marker: str, **overrides) -> dict:
    response = client.post(
        f"{settings.API_V1_PREFIX}/issues/",
        json=_issue_payload(marker, **overrides),
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_issue_workflow_allows_superuser_state_machine_transitions(
    client: TestClient,
    admin_token: str,
):
    headers = _auth_headers(admin_token)
    marker = f"QA-ISSUE-WORKFLOW-{uuid4().hex[:8]}"
    issue = _create_issue(client, headers, marker)
    issue_id = issue["id"]

    assigned = client.post(
        f"{settings.API_V1_PREFIX}/issues/{issue_id}/assign",
        json={"assignee_id": 1, "remark": marker},
        headers=headers,
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["status"] == "IN_PROGRESS"

    resolved = client.post(
        f"{settings.API_V1_PREFIX}/issues/{issue_id}/resolve",
        json={"solution": f"{marker} solution", "root_cause": "OTHER"},
        headers=headers,
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "RESOLVED"

    verified = client.post(
        f"{settings.API_V1_PREFIX}/issues/{issue_id}/verify",
        json={"verified_result": "PASSED", "remark": marker},
        headers=headers,
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["status"] == "CLOSED"


def test_batch_status_logs_previous_issue_status(
    client: TestClient,
    admin_token: str,
    db: Session,
):
    headers = _auth_headers(admin_token)
    marker = f"QA-ISSUE-BATCH-STATUS-{uuid4().hex[:8]}"
    issue_a = _create_issue(client, headers, f"{marker}-A")
    issue_b = _create_issue(client, headers, f"{marker}-B")
    issue_ids = [issue_a["id"], issue_b["id"]]

    response = client.post(
        f"{settings.API_V1_PREFIX}/issues/batch-status",
        json={"issue_ids": issue_ids, "new_status": "IN_PROGRESS", "comment": marker},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["success_count"] == 2

    db.expire_all()
    records = (
        db.query(IssueFollowUpRecord)
        .filter(
            IssueFollowUpRecord.issue_id.in_(issue_ids),
            IssueFollowUpRecord.content == marker,
        )
        .order_by(IssueFollowUpRecord.issue_id)
        .all()
    )
    assert len(records) == 2
    assert {record.old_status for record in records} == {"OPEN"}
    assert {record.new_status for record in records} == {"IN_PROGRESS"}


def test_batch_close_closes_blocking_issue_alert(
    client: TestClient,
    admin_token: str,
    db: Session,
):
    headers = _auth_headers(admin_token)
    marker = f"QA-ISSUE-BATCH-CLOSE-{uuid4().hex[:8]}"
    issue = _create_issue(client, headers, marker, severity="CRITICAL")
    issue_id = issue["id"]

    updated = client.put(
        f"{settings.API_V1_PREFIX}/issues/{issue_id}",
        json={"is_blocking": True},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text

    db.expire_all()
    alert = (
        db.query(AlertRecord)
        .filter(AlertRecord.target_type == "ISSUE", AlertRecord.target_id == issue_id)
        .first()
    )
    assert alert is not None
    assert alert.status == AlertStatusEnum.PENDING.value

    response = client.post(
        f"{settings.API_V1_PREFIX}/issues/batch-close",
        json={"issue_ids": [issue_id], "comment": marker},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["success_count"] == 1

    db.expire_all()
    closed_alert = db.query(AlertRecord).filter(AlertRecord.id == alert.id).first()
    assert closed_alert.status == AlertStatusEnum.RESOLVED.value

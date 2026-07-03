# -*- coding: utf-8 -*-
"""Approval action request validation contract tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "path",
    [
        "/sales/quotes/approval/batch-action",
        "/sales/contracts/approval/batch-action",
        "/acceptance/acceptance-orders/approval/batch-action",
        "/ecns/approval/batch-action",
        "/purchase-orders/workflow/batch-action",
        "/outsourcing-orders/workflow/batch-action",
    ],
)
def test_batch_approval_rejects_unknown_action_before_service_layer(
    client: TestClient,
    admin_token: str,
    path: str,
):
    response = client.post(
        f"{settings.API_V1_PREFIX}{path}",
        headers=_auth_headers(admin_token),
        json={"task_ids": [999999], "action": "escalate", "comment": "invalid action"},
    )

    assert response.status_code == 422, response.text
    body = response.text
    assert "approve" in body
    assert "reject" in body


@pytest.mark.parametrize(
    "path",
    [
        "/sales/quotes/approval/batch-action",
        "/sales/contracts/approval/batch-action",
        "/acceptance/acceptance-orders/approval/batch-action",
        "/ecns/approval/batch-action",
        "/purchase-orders/workflow/batch-action",
        "/outsourcing-orders/workflow/batch-action",
    ],
)
@pytest.mark.parametrize("action", ["approve", "reject"])
def test_batch_approval_accepts_valid_actions(
    client: TestClient,
    admin_token: str,
    path: str,
    action: str,
):
    response = client.post(
        f"{settings.API_V1_PREFIX}{path}",
        headers=_auth_headers(admin_token),
        json={"task_ids": [999999], "action": action, "comment": "valid action"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["errors"]


@pytest.mark.parametrize(
    "path,payload",
    [
        (
            "/timesheet/workflow/tasks/999999/action",
            {"action": "ESCALATE", "comment": "invalid action"},
        ),
        (
            "/timesheet/workflow/batch-action",
            {"task_ids": [999999], "action": "ESCALATE", "comment": "invalid action"},
        ),
    ],
)
def test_timesheet_approval_rejects_unknown_action_before_lookup(
    client: TestClient,
    admin_token: str,
    path: str,
    payload: dict,
):
    response = client.post(
        f"{settings.API_V1_PREFIX}{path}",
        headers=_auth_headers(admin_token),
        json=payload,
    )

    assert response.status_code == 422, response.text
    body = response.text
    assert "APPROVE" in body
    assert "REJECT" in body


@pytest.mark.parametrize(
    "path,payload,expected_status",
    [
        (
            "/timesheet/workflow/tasks/999999/action",
            {"action": "APPROVE", "comment": "valid action"},
            404,
        ),
        (
            "/timesheet/workflow/tasks/999999/action",
            {"action": "REJECT", "comment": "valid action"},
            404,
        ),
        (
            "/timesheet/workflow/batch-action",
            {"task_ids": [999999], "action": "APPROVE", "comment": "valid action"},
            200,
        ),
        (
            "/timesheet/workflow/batch-action",
            {"task_ids": [999999], "action": "REJECT", "comment": "valid action"},
            200,
        ),
    ],
)
def test_timesheet_approval_accepts_valid_actions(
    client: TestClient,
    admin_token: str,
    path: str,
    payload: dict,
    expected_status: int,
):
    response = client.post(
        f"{settings.API_V1_PREFIX}{path}",
        headers=_auth_headers(admin_token),
        json=payload,
    )

    assert response.status_code == expected_status, response.text

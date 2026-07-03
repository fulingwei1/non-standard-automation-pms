# -*- coding: utf-8 -*-
"""Batch 10 route-smoke regressions."""

from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_wbs_template_progress_route_is_registered(
    client: TestClient, admin_token: str
):
    # 2026-07-03 去重：progress_compat 裸挂载（/wbs-templates 顶层别名）已下线，统一走 /progress
    headers = _auth_headers(admin_token)
    progress_response = client.get(
        f"{settings.API_V1_PREFIX}/progress/wbs-templates",
        params={"page": 1, "page_size": 100},
        headers=headers,
        follow_redirects=False,
    )
    root_response = client.get(
        f"{settings.API_V1_PREFIX}/wbs-templates",
        params={"page": 1, "page_size": 100},
        headers=headers,
        follow_redirects=False,
    )

    assert progress_response.status_code == 200, progress_response.text
    assert "items" in progress_response.json()
    assert "total" in progress_response.json()
    assert root_response.status_code == 404, "裸挂载别名应已下线"


def test_batch_material_readiness_kit_rate_route_is_registered(
    client: TestClient, admin_token: str
):
    response = client.post(
        f"{settings.API_V1_PREFIX}/assembly/material-readiness/batch-kit-rate",
        json={"project_ids": []},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"kit_rates": {}}


def test_progress_report_compat_routes_precede_dynamic_report_routes(
    client: TestClient, admin_token: str
):
    # 2026-07-03 去重：报表兼容路由统一走 /progress/reports/*
    headers = _auth_headers(admin_token)
    milestone_response = client.get(
        f"{settings.API_V1_PREFIX}/progress/reports/milestone-rate",
        headers=headers,
        follow_redirects=False,
    )
    delay_response = client.get(
        f"{settings.API_V1_PREFIX}/progress/reports/delay-reasons",
        params={"top_n": 10},
        headers=headers,
        follow_redirects=False,
    )

    assert milestone_response.status_code == 200, milestone_response.text
    milestone_payload = milestone_response.json()
    assert "total_milestones" in milestone_payload
    assert "completion_rate" in milestone_payload
    assert "milestones" in milestone_payload

    assert delay_response.status_code == 200, delay_response.text
    delay_payload = delay_response.json()
    assert "total_delayed_tasks" in delay_payload
    assert "reasons" in delay_payload
    assert "detailed_tasks" in delay_payload


def test_progress_prefixed_report_aliases_are_registered(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/progress/reports/milestone-rate",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    assert "total_milestones" in response.json()


def test_sales_delay_root_cause_uses_current_task_schema(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/analysis/delay/root-cause",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 200
    assert "total_delayed_tasks" in payload["data"]
    assert "root_causes" in payload["data"]

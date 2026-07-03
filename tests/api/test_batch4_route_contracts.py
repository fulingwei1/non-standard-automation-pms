# -*- coding: utf-8 -*-
"""Batch 4 live-page route contracts."""

from fastapi.testclient import TestClient

from app.core.config import settings


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_finance_cost_analysis_routes_are_registered(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)
    endpoints = [
        "/cost-collection/status",
        "/cost-collection/by-project",
        "/quote-compare/list",
        "/cost-variance/summary",
        "/cost-variance/patterns",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)
        assert response.status_code == 200, f"{endpoint}: {response.text}"


def test_batch4_compatibility_routes_return_200(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)
    endpoints = [
        "/report/archives",
        "/analytics/workload/bottlenecks",
        "/sales/payments/records",
        "/engineer-performance/ranking",
        "/admin/attendance",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)
        assert response.status_code == 200, f"{endpoint}: {response.text}"

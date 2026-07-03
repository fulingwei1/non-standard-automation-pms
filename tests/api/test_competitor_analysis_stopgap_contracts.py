# -*- coding: utf-8 -*-
"""Stopgap contracts for the hard-coded competitor-analysis module."""

from fastapi.testclient import TestClient

from app.core.config import settings


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_competitor_analysis_stub_endpoints_are_not_served_as_real_data(
    client: TestClient,
    admin_token: str,
):
    headers = _headers(admin_token)
    endpoints = [
        "/sales/competitor/competitor/overview",
        "/sales/competitor/competitor/1/analysis",
        "/sales/competitor/competitor/strategy-recommendations",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)

        assert response.status_code == 501, f"{endpoint}: {response.text}"
        assert "竞品 A" not in response.text
        assert "宁德时代" not in response.text

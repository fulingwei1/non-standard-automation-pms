# -*- coding: utf-8 -*-
"""Batch 6 live-page route contracts."""

from fastapi.testclient import TestClient

from app.core.config import settings


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_inventory_analysis_routes_return_frontend_shapes(
    client: TestClient, admin_token: str
):
    headers = _headers(admin_token)

    turnover = client.get(
        f"{settings.API_V1_PREFIX}/inventory-analysis/turnover-rate",
        headers=headers,
    )
    assert turnover.status_code == 200, turnover.text
    turnover_data = turnover.json()["data"]
    assert {"summary", "category_breakdown"} <= set(turnover_data)
    assert {
        "total_inventory_value",
        "turnover_rate",
        "turnover_days",
        "total_materials",
    } <= set(turnover_data["summary"])

    stale = client.get(
        f"{settings.API_V1_PREFIX}/inventory-analysis/stale-materials",
        params={"threshold_days": 90},
        headers=headers,
    )
    assert stale.status_code == 200, stale.text
    stale_data = stale.json()["data"]
    assert {"summary", "age_distribution", "stale_materials"} <= set(stale_data)

    safety = client.get(
        f"{settings.API_V1_PREFIX}/inventory-analysis/safety-stock-compliance",
        headers=headers,
    )
    assert safety.status_code == 200, safety.text
    safety_data = safety.json()["data"]
    assert {
        "summary",
        "warning_materials",
        "out_of_stock_materials",
    } <= set(safety_data)
    assert {"total_materials", "compliant_rate", "warning", "out_of_stock"} <= set(
        safety_data["summary"]
    )

    abc = client.get(
        f"{settings.API_V1_PREFIX}/inventory-analysis/abc-analysis",
        headers=headers,
    )
    assert abc.status_code == 200, abc.text
    abc_data = abc.json()["data"]
    assert {"total_materials", "abc_summary"} <= set(abc_data)
    assert {"A", "B", "C"} <= set(abc_data["abc_summary"])

    occupancy = client.get(
        f"{settings.API_V1_PREFIX}/inventory-analysis/cost-occupancy",
        headers=headers,
    )
    assert occupancy.status_code == 200, occupancy.text
    occupancy_data = occupancy.json()["data"]
    assert {"summary", "category_occupancy", "top_materials"} <= set(occupancy_data)
    assert {"total_inventory_value", "total_categories"} <= set(
        occupancy_data["summary"]
    )

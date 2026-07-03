# -*- coding: utf-8 -*-
"""Financial reports API route contract tests."""

from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_financial_report_routes_return_frontend_shapes(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    monthly = client.get(
        f"{settings.API_V1_PREFIX}/finance/monthly-trend",
        params={"period": "month", "year": 2026},
        headers=headers,
    )
    assert monthly.status_code == 200, monthly.text
    monthly_data = monthly.json()
    assert isinstance(monthly_data, list)
    assert {"month", "revenue", "cost", "profit", "cashFlow"} <= set(monthly_data[0])

    costs = client.get(
        f"{settings.API_V1_PREFIX}/finance/cost-analysis",
        params={"period": "month"},
        headers=headers,
    )
    assert costs.status_code == 200, costs.text
    cost_data = costs.json()
    assert isinstance(cost_data, list)
    assert {"category", "amount", "budget", "variance"} <= set(cost_data[0])

    projects = client.get(
        f"{settings.API_V1_PREFIX}/finance/project-profitability",
        params={"limit": 10},
        headers=headers,
    )
    assert projects.status_code == 200, projects.text
    project_data = projects.json()
    assert isinstance(project_data, list)
    assert {"project", "revenue", "cost", "profit", "margin", "status"} <= set(project_data[0])

    cash_flow = client.get(
        f"{settings.API_V1_PREFIX}/finance/cash-flow",
        params={"period": "month"},
        headers=headers,
    )
    assert cash_flow.status_code == 200, cash_flow.text
    cash_flow_data = cash_flow.json()
    assert isinstance(cash_flow_data, list)
    assert {"month", "inflow", "outflow", "net"} <= set(cash_flow_data[0])

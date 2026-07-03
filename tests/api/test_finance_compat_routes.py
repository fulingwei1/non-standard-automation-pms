# -*- coding: utf-8 -*-
"""Finance compatibility route contracts used by live frontend pages."""

from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_multi_currency_routes_return_frontend_shapes(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    rates = client.get(f"{settings.API_V1_PREFIX}/currency/rates", headers=headers)
    assert rates.status_code == 200, rates.text
    rates_data = rates.json()
    assert isinstance(rates_data, list)
    assert {"currency", "rate", "change"} <= set(rates_data[0])

    history = client.get(
        f"{settings.API_V1_PREFIX}/currency/history",
        params={"limit": 20},
        headers=headers,
    )
    assert history.status_code == 200, history.text
    history_data = history.json()
    assert isinstance(history_data, list)
    assert {"currency", "rate", "updated_at"} <= set(history_data[0])

    converted = client.get(
        f"{settings.API_V1_PREFIX}/currency/convert",
        params={"from_currency": "USD", "to_currency": "CNY", "amount": 1000},
        headers=headers,
    )
    assert converted.status_code == 200, converted.text
    converted_data = converted.json()
    assert {
        "from_currency",
        "to_currency",
        "amount",
        "converted_amount",
        "rate",
    } <= set(converted_data)


def test_settlement_routes_return_frontend_shapes(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)

    settlements = client.get(f"{settings.API_V1_PREFIX}/settlements", headers=headers)
    assert settlements.status_code == 200, settlements.text
    settlement_data = settlements.json()
    assert isinstance(settlement_data, list)
    assert {
        "id",
        "settlementNo",
        "projectName",
        "customerName",
        "contractAmount",
        "totalCost",
        "grossProfit",
        "grossMargin",
        "receivedAmount",
        "receivableAmount",
        "status",
        "statusLabel",
    } <= set(settlement_data[0])

    stats = client.get(f"{settings.API_V1_PREFIX}/settlements/statistics", headers=headers)
    assert stats.status_code == 200, stats.text
    stats_data = stats.json()
    assert {
        "totalContractAmount",
        "totalCost",
        "totalProfit",
        "totalReceivable",
        "count",
    } <= set(stats_data)

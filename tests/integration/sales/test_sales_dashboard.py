# -*- coding: utf-8 -*-
"""销售仪表盘接口契约测试。"""

from fastapi.testclient import TestClient


def test_sales_dashboard_returns_frontend_contract(
    client: TestClient, auth_headers: dict
):
    """Dashboard 返回的字段应满足现有前端页面渲染。"""
    response = client.get("/api/v1/sales/dashboard", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]

    personal = data["personal"]
    assert "monthly" in personal
    assert "avg_deal_size" in personal

    pipeline = data["pipeline"]
    assert "weighted_value" in pipeline
    assert "deal_count" in pipeline
    assert "avg_cycle_days" in pipeline
    assert isinstance(pipeline["risks"], list)
    assert all("avg_days" in stage and "health" in stage for stage in pipeline["stages"])

    forecast = data["forecast"]
    assert "total_forecast" in forecast
    assert "total_actual" in forecast
    assert "accuracy" in forecast
    assert isinstance(forecast["quarters"], list)

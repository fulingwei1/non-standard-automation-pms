# -*- coding: utf-8 -*-
"""
销售统计 API 集成测试

覆盖:
- GET /sales/statistics/funnel - 销售漏斗
- GET /sales/statistics/summary - 销售汇总
- GET /sales/statistics/opportunities-by-stage - 按阶段商机统计
- GET /sales/statistics/revenue-forecast - 营收预测
- GET /sales/statistics/prediction - 销售预测
- GET /sales/statistics/prediction/accuracy - 预测准确性
"""

import pytest
from fastapi.testclient import TestClient


class TestSalesFunnel:
    """销售漏斗 API 测试"""

    def test_get_funnel_success(self, client: TestClient, auth_headers: dict):
        """测试获取销售漏斗 - 正常情况"""
        response = client.get("/api/v1/sales/statistics/funnel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "code" in data or "data" in data
        # 验证漏斗数据结构
        result = data.get("data", data)
        # 可能包含 leads, opportunities, quotes, contracts 等字段
        assert isinstance(result, dict)

    def test_get_funnel_with_year_filter(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取销售漏斗 - 年份筛选"""
        response = client.get(
            "/api/v1/sales/statistics/funnel",
            params={"year": 2026},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_funnel_with_customer_filter(
        self, client: TestClient, auth_headers: dict, test_customer: dict
    ):
        """测试获取销售漏斗 - 客户筛选"""
        response = client.get(
            "/api/v1/sales/statistics/funnel",
            params={"customer_id": test_customer["id"]},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_funnel_unauthorized(self, client: TestClient):
        """测试未认证访问销售漏斗"""
        response = client.get("/api/v1/sales/statistics/funnel")
        assert response.status_code in [401, 403]


class TestSalesSummary:
    """销售汇总 API 测试"""

    def test_get_summary_success(self, client: TestClient, auth_headers: dict):
        """测试获取销售汇总 - 正常情况"""
        response = client.get(
            "/api/v1/sales/statistics/summary",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data or "data" in data

    def test_get_summary_with_month_filter(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取销售汇总 - 月份筛选"""
        response = client.get(
            "/api/v1/sales/statistics/summary",
            params={"month": "2026-03"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_summary_with_date_range(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取销售汇总 - 日期范围"""
        response = client.get(
            "/api/v1/sales/statistics/summary",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestOpportunitiesByStage:
    """按阶段商机统计 API 测试"""

    def test_get_opportunities_by_stage_success(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取按阶段商机统计 - 正常情况"""
        response = client.get(
            "/api/v1/sales/statistics/opportunities-by-stage",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        result = data.get("data", data)
        assert isinstance(result, (dict, list))

    def test_get_opportunities_by_stage_with_year(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取按阶段商机统计 - 年份筛选"""
        response = client.get(
            "/api/v1/sales/statistics/opportunities-by-stage",
            params={"year": 2026},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestRevenueForecast:
    """营收预测 API 测试"""

    def test_get_revenue_forecast_success(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取营收预测 - 正常情况"""
        response = client.get(
            "/api/v1/sales/statistics/revenue-forecast",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data or "data" in data

    def test_get_revenue_forecast_with_months(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取营收预测 - 指定月数"""
        response = client.get(
            "/api/v1/sales/statistics/revenue-forecast",
            params={"months": 6},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestSalesPrediction:
    """销售预测 API 测试"""

    def test_get_prediction_success(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取销售预测 - 正常情况"""
        response = client.get(
            "/api/v1/sales/statistics/prediction",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data or "data" in data

    def test_get_prediction_with_months(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取销售预测 - 指定月数"""
        response = client.get(
            "/api/v1/sales/statistics/prediction",
            params={"months": 3},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestPredictionAccuracy:
    """预测准确性 API 测试"""

    def test_get_prediction_accuracy_success(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取预测准确性 - 正常情况"""
        response = client.get(
            "/api/v1/sales/statistics/prediction/accuracy",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data or "data" in data

    def test_get_prediction_accuracy_with_period(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取预测准确性 - 指定时间段"""
        response = client.get(
            "/api/v1/sales/statistics/prediction/accuracy",
            params={"start_date": "2025-01-01", "end_date": "2025-12-31"},
            headers=auth_headers,
        )
        assert response.status_code == 200

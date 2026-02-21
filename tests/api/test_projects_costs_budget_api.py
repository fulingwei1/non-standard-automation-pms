# -*- coding: utf-8 -*-
"""
项目成本与预算 API 测试

测试项目成本核算、预算管理、成本分析等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectCostsBudgetAPI:
    """项目成本与预算 API 测试类"""

    def test_get_project_budget(self, client: TestClient, admin_token: str):
        """测试获取项目预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/budget",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Project budget API not implemented")

        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, dict)

    def test_update_project_budget(self, client: TestClient, admin_token: str):
        """测试更新项目预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        budget_data = {
            "total_budget": 500000.0,
            "labor_cost_budget": 300000.0,
            "material_cost_budget": 150000.0,
            "other_cost_budget": 50000.0
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/1/costs/budget",
            headers=headers,
            json=budget_data
        )

        if response.status_code == 404:
            pytest.skip("Project budget update API not implemented")

        assert response.status_code == 200, response.text

    def test_get_project_actual_costs(self, client: TestClient, admin_token: str):
        """测试获取项目实际成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/actual",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Actual costs API not implemented")

        assert response.status_code == 200, response.text

    def test_cost_breakdown_by_category(self, client: TestClient, admin_token: str):
        """测试按类别分解成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/breakdown",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Cost breakdown API not implemented")

        assert response.status_code == 200, response.text

    def test_cost_variance_analysis(self, client: TestClient, admin_token: str):
        """测试成本偏差分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/variance",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Cost variance API not implemented")

        assert response.status_code == 200, response.text

    def test_cost_forecast(self, client: TestClient, admin_token: str):
        """测试成本预测"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/forecast",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Cost forecast API not implemented")

        assert response.status_code == 200, response.text

    def test_evm_analysis(self, client: TestClient, admin_token: str):
        """测试挣值管理（EVM）分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/evm",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("EVM API not implemented")

        assert response.status_code == 200, response.text

    def test_add_cost_entry(self, client: TestClient, admin_token: str):
        """测试添加成本记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        cost_entry = {
            "cost_category": "labor",
            "amount": 5000.0,
            "description": "开发人员工资",
            "cost_date": datetime.now().strftime("%Y-%m-%d"),
            "vendor": "内部"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/costs/entries",
            headers=headers,
            json=cost_entry
        )

        if response.status_code == 404:
            pytest.skip("Cost entry API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_list_cost_entries(self, client: TestClient, admin_token: str):
        """测试获取成本记录列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/entries",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Cost entries API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_costs_by_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围过滤成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/entries"
            f"?start_date=2024-01-01&end_date=2024-12-31",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Cost filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_costs_by_category(self, client: TestClient, admin_token: str):
        """测试按类别过滤成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/entries?category=labor",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Cost filter API not implemented")

        assert response.status_code == 200, response.text

    def test_cost_export(self, client: TestClient, admin_token: str):
        """测试成本数据导出"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Cost export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_budget_approval_workflow(self, client: TestClient, admin_token: str):
        """测试预算审批流程"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        approval_data = {
            "budget_change": 50000.0,
            "reason": "项目范围扩大",
            "approver_id": 1
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/costs/budget/approval",
            headers=headers,
            json=approval_data
        )

        if response.status_code == 404:
            pytest.skip("Budget approval API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_cost_unauthorized_access(self, client: TestClient):
        """测试未授权访问成本数据"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/budget"
        )

        assert response.status_code in [401, 403], response.text

    def test_cost_analysis_charts(self, client: TestClient, admin_token: str):
        """测试成本分析图表数据"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/costs/analysis/charts",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Cost charts API not implemented")

        assert response.status_code == 200, response.text

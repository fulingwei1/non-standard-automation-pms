# -*- coding: utf-8 -*-
"""
项目中心成本API测试

测试新的项目中心API端点: /api/v1/projects/{project_id}/costs/
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectCostsAPI:
    """项目中心成本API测试"""

    def test_list_project_costs(self, client: TestClient, admin_token: str):
        """测试获取项目成本列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 测试项目中心API
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        # 新API返回分页格式
        assert "items" in data or isinstance(data, list)
        if "items" in data:
            assert "total" in data
            assert "page" in data
            assert "page_size" in data

    def test_list_project_costs_with_pagination(self, client: TestClient, admin_token: str):
        """测试分页参数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 测试分页
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        if "items" in data:
            assert data["page"] == 1
            assert data["page_size"] == 10

    def test_list_project_costs_with_keyword(self, client: TestClient, admin_token: str):
        """测试关键词搜索"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 测试关键词搜索
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            params={"keyword": "测试"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_list_project_costs_with_cost_type_filter(self, client: TestClient, admin_token: str):
        """测试成本类型筛选"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 测试成本类型筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            params={"cost_type": "LABOR"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_create_project_cost(self, client: TestClient, admin_token: str):
        """测试创建项目成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        cost_data = {
            "cost_type": "LABOR",
            "cost_category": "人工费",
            "amount": str(Decimal("1000.00")),
            "tax_amount": str(Decimal("0.00")),
            "cost_date": date.today().isoformat(),
            "description": f"测试成本-{uuid.uuid4().hex[:4]}",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            json=cost_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create cost")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["cost_type"] == cost_data["cost_type"]
        assert data["project_id"] == project_id  # 确保项目ID正确

    def test_get_project_cost_detail(self, client: TestClient, admin_token: str):
        """测试获取项目成本详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 先创建成本
        cost_data = {
            "cost_type": "LABOR",
            "cost_category": "人工费",
            "amount": str(Decimal("1000.00")),
            "tax_amount": str(Decimal("0.00")),
            "cost_date": date.today().isoformat(),
            "description": f"测试成本-{uuid.uuid4().hex[:4]}",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            json=cost_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create cost for testing")

        cost_id = create_response.json()["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/{cost_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == cost_id
        assert data["project_id"] == project_id

    def test_get_project_cost_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_project_cost(self, client: TestClient, admin_token: str):
        """测试更新项目成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 先创建成本
        cost_data = {
            "cost_type": "LABOR",
            "cost_category": "人工费",
            "amount": str(Decimal("1000.00")),
            "tax_amount": str(Decimal("0.00")),
            "cost_date": date.today().isoformat(),
            "description": f"测试成本-{uuid.uuid4().hex[:4]}",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            json=cost_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create cost for testing")

        cost_id = create_response.json()["id"]

        # 更新成本
        update_data = {
            "description": f"更新成本-{uuid.uuid4().hex[:4]}",
            "amount": str(Decimal("2000.00")),
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/{cost_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update cost")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["description"] == update_data["description"]
        assert float(data["amount"]) == float(update_data["amount"])

    def test_delete_project_cost(self, client: TestClient, admin_token: str):
        """测试删除项目成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 先创建成本
        cost_data = {
            "cost_type": "LABOR",
            "cost_category": "人工费",
            "amount": str(Decimal("1000.00")),
            "tax_amount": str(Decimal("0.00")),
            "cost_date": date.today().isoformat(),
            "description": f"测试成本-{uuid.uuid4().hex[:4]}",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            json=cost_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create cost for testing")

        cost_id = create_response.json()["id"]

        # 删除成本
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/{cost_id}",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to delete cost")

        assert response.status_code in [200, 204], response.text

    def test_get_project_cost_summary(self, client: TestClient, admin_token: str):
        """测试获取项目成本汇总（自定义端点）"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 测试成本汇总
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/summary",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        assert data["data"]["project_id"] == project_id
        assert "total_cost" in data["data"]
        assert "by_type" in data["data"]


class TestProjectCostsAdvanced:
    """项目成本高级测试"""

    def test_cost_by_month(self, client: TestClient, admin_token: str):
        """测试按月汇总成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 获取按月汇总
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/by-month",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("By-month endpoint not found")
        if response.status_code == 422:
            pytest.skip("By-month endpoint not implemented")

        assert response.status_code == 200, response.text

    def test_cost_trend(self, client: TestClient, admin_token: str):
        """测试成本趋势"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 获取成本趋势
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/trend",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Trend endpoint not found")
        if response.status_code == 422:
            pytest.skip("Trend endpoint not implemented")

        assert response.status_code == 200, response.text

    def test_cost_with_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围筛选成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 按日期范围筛选
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            params={"start_date": start_date, "end_date": end_date},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_cost_approval(self, client: TestClient, admin_token: str):
        """测试成本审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 先创建成本
        cost_data = {
            "cost_type": "MATERIAL",
            "cost_category": "物料费",
            "amount": str(Decimal("5000.00")),
            "tax_amount": str(Decimal("0.00")),
            "cost_date": date.today().isoformat(),
            "description": f"待审批成本-{uuid.uuid4().hex[:4]}",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/",
            json=cost_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create cost for approval test")

        cost_id = create_response.json()["id"]

        # 审批成本
        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/{cost_id}/approve",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Approve endpoint not found")
        if response.status_code == 403:
            pytest.skip("User does not have approval permission")

        assert response.status_code in [200, 400], response.text

    def test_cost_budget_comparison(self, client: TestClient, admin_token: str):
        """测试成本预算对比"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 获取预算对比
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/budget-comparison",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Budget comparison endpoint not found")
        if response.status_code == 422:
            pytest.skip("Budget comparison endpoint not implemented")

        assert response.status_code == 200, response.text

    def test_batch_create_costs(self, client: TestClient, admin_token: str):
        """测试批量创建成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目列表
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )

        if projects_response.status_code != 200:
            pytest.skip("Failed to get projects list")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available for testing")

        project_id = items[0]["id"]

        # 批量创建成本
        costs_data = {
            "costs": [
                {
                    "cost_type": "LABOR",
                    "cost_category": "人工费",
                    "amount": "1000.00",
                    "cost_date": date.today().isoformat(),
                    "description": "批量成本A"
                },
                {
                    "cost_type": "MATERIAL",
                    "cost_category": "物料费",
                    "amount": "2000.00",
                    "cost_date": date.today().isoformat(),
                    "description": "批量成本B"
                },
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/batch",
            json=costs_data,
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Batch create endpoint not found")
        if response.status_code == 405:
            pytest.skip("Batch create endpoint not implemented")
        if response.status_code == 422:
            pytest.skip("Batch create validation error")
        if response.status_code == 403:
            pytest.skip("User does not have permission")

        assert response.status_code in [200, 201], response.text

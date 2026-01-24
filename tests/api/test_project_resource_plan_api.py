# -*- coding: utf-8 -*-
"""
项目中心资源计划API测试

测试新的项目中心API端点: /api/v1/projects/{project_id}/resource-plan/
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectResourcePlanAPI:
    """项目中心资源计划API测试"""

    def test_list_project_resource_plans(self, client: TestClient, admin_token: str):
        """测试获取项目资源计划列表"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

    def test_list_project_resource_plans_with_stage_filter(self, client: TestClient, admin_token: str):
        """测试阶段筛选"""
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

        # 测试阶段筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            params={"stage_code": "S1"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_get_project_resource_plan_detail(self, client: TestClient, admin_token: str):
        """测试获取资源计划详情"""
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

        # 先获取资源计划列表
        plans_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/",
            headers=headers
        )

        if plans_response.status_code != 200:
            pytest.skip("Failed to get resource plans list")

        plans = plans_response.json()
        if not plans:
            pytest.skip("No resource plans available for testing")

        plan_id = plans[0]["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/{plan_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == plan_id
        assert data["project_id"] == project_id

    def test_get_project_resource_plan_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的资源计划"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_get_resource_plan_summary(self, client: TestClient, admin_token: str):
        """测试获取资源计划汇总（自定义端点）"""
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

        # 测试汇总
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/resource-plan/summary",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "project_id" in data
        assert "stages" in data
        assert "overall_fill_rate" in data

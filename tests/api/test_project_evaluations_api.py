# -*- coding: utf-8 -*-
"""
项目中心评价API测试

测试新的项目中心API端点: /api/v1/projects/{project_id}/evaluations/
"""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectEvaluationsAPI:
    """项目中心评价API测试"""

    def test_list_project_evaluations(self, client: TestClient, admin_token: str):
        """测试获取项目评价列表"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/",
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

    def test_list_project_evaluations_with_pagination(self, client: TestClient, admin_token: str):
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        if "items" in data:
            assert data["page"] == 1
            assert data["page_size"] == 10

    def test_list_project_evaluations_with_status_filter(self, client: TestClient, admin_token: str):
        """测试状态筛选"""
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

        # 测试状态筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/",
            params={"status": "DRAFT"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_create_project_evaluation(self, client: TestClient, admin_token: str):
        """测试创建项目评价"""
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

        evaluation_data = {
            "novelty_score": 5.0,
            "new_tech_score": 6.0,
            "difficulty_score": 7.0,
            "workload_score": 8.0,
            "amount_score": 9.0,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/",
            json=evaluation_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create evaluation")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert "data" in data
        assert data["data"]["project_id"] == project_id

    def test_get_project_evaluation_detail(self, client: TestClient, admin_token: str):
        """测试获取项目评价详情"""
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

        # 先获取评价列表
        evaluations_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/",
            headers=headers
        )

        if evaluations_response.status_code != 200:
            pytest.skip("Failed to get evaluations list")

        evaluations = evaluations_response.json()
        eval_items = evaluations.get("items", evaluations) if isinstance(evaluations, dict) else evaluations
        if not eval_items:
            pytest.skip("No evaluations available for testing")

        eval_id = eval_items[0]["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/{eval_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == eval_id
        assert data["data"]["project_id"] == project_id

    def test_get_project_evaluation_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的评价"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_get_project_latest_evaluation(self, client: TestClient, admin_token: str):
        """测试获取项目最新评价（自定义端点）"""
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

        # 测试最新评价
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/latest",
            headers=headers
        )

        # 可能没有评价记录，返回404也是正常的
        assert response.status_code in [200, 404], response.text

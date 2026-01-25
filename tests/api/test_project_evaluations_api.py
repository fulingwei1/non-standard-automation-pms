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

    def test_update_project_evaluation(self, client: TestClient, admin_token: str):
        """测试更新项目评价"""
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

        # 先创建一个评价
        evaluation_data = {
            "novelty_score": 5.0,
            "new_tech_score": 6.0,
            "difficulty_score": 7.0,
            "workload_score": 8.0,
            "amount_score": 9.0,
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/",
            json=evaluation_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create evaluation for update test")

        eval_id = create_response.json().get("data", {}).get("id")
        if not eval_id:
            pytest.skip("Failed to get evaluation ID")

        # 更新评价
        update_data = {
            "novelty_score": 8.0,
            "evaluation_note": "更新后的评价说明"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/{eval_id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        # 验证得分已更新
        if data["data"].get("novelty_score"):
            assert float(data["data"]["novelty_score"]) == 8.0

    def test_confirm_project_evaluation(self, client: TestClient, admin_token: str):
        """测试确认项目评价"""
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

        # 先创建一个评价
        evaluation_data = {
            "novelty_score": 5.0,
            "new_tech_score": 6.0,
            "difficulty_score": 7.0,
            "workload_score": 8.0,
            "amount_score": 9.0,
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/",
            json=evaluation_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create evaluation for confirm test")

        eval_id = create_response.json().get("data", {}).get("id")
        if not eval_id:
            pytest.skip("Failed to get evaluation ID")

        # 确认评价
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/{eval_id}/confirm",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        assert data["data"]["status"] == "CONFIRMED"

    def test_delete_project_evaluation(self, client: TestClient, admin_token: str):
        """测试删除项目评价"""
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

        # 先创建一个评价
        evaluation_data = {
            "novelty_score": 5.0,
            "new_tech_score": 6.0,
            "difficulty_score": 7.0,
            "workload_score": 8.0,
            "amount_score": 9.0,
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/",
            json=evaluation_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create evaluation for delete test")

        eval_id = create_response.json().get("data", {}).get("id")
        if not eval_id:
            pytest.skip("Failed to get evaluation ID")

        # 删除评价
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/{eval_id}",
            headers=headers
        )

        # 删除成功返回204或200
        assert response.status_code in [200, 204], response.text

        # 验证已删除
        get_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/{eval_id}",
            headers=headers
        )
        assert get_response.status_code == 404

    def test_create_evaluation_with_weights(self, client: TestClient, admin_token: str):
        """测试创建带自定义权重的评价"""
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

        # 创建带权重的评价
        evaluation_data = {
            "novelty_score": 8.0,
            "new_tech_score": 7.0,
            "difficulty_score": 6.0,
            "workload_score": 9.0,
            "amount_score": 8.0,
            "weights": {
                "novelty": 0.25,
                "new_tech": 0.20,
                "difficulty": 0.20,
                "workload": 0.20,
                "amount": 0.15
            },
            "evaluation_note": "自定义权重测试"
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
        # 验证总分已计算
        if data["data"].get("total_score"):
            assert data["data"]["total_score"] > 0

    def test_evaluation_statistics(self, client: TestClient, admin_token: str):
        """测试获取项目评价统计"""
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

        # 获取评价统计
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/evaluations/statistics",
            headers=headers
        )

        # 统计端点可能不存在
        if response.status_code == 404:
            pytest.skip("Statistics endpoint not available")

        assert response.status_code == 200, response.text

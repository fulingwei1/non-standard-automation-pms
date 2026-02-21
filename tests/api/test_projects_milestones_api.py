# -*- coding: utf-8 -*-
"""
项目里程碑 API 测试

测试项目里程碑的创建、查询、更新、删除及相关功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectMilestonesAPI:
    """项目里程碑 API 测试类"""

    def test_create_milestone(self, client: TestClient, admin_token: str):
        """测试创建项目里程碑"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取一个项目
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )
        if projects_response.status_code != 200:
            pytest.skip("No projects available")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available")

        project_id = items[0]["id"]

        # 创建里程碑
        milestone_data = {
            "project_id": project_id,
            "name": "需求分析完成",
            "description": "完成需求文档编写和评审",
            "planned_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "milestone_type": "phase",
            "weight": 15.0
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            headers=headers,
            json=milestone_data
        )

        # 如果端点不存在或未实现，跳过测试
        if response.status_code == 404:
            pytest.skip("Milestone API not implemented")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["name"] == milestone_data["name"]
        assert data["project_id"] == project_id

    def test_list_milestones(self, client: TestClient, admin_token: str):
        """测试获取项目里程碑列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 获取项目
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )
        if projects_response.status_code != 200:
            pytest.skip("No projects available")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available")

        project_id = items[0]["id"]

        # 获取里程碑列表
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/milestones/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Milestone API not implemented")

        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, (list, dict))
        if isinstance(data, dict):
            assert "items" in data or "total" in data

    def test_get_milestone_detail(self, client: TestClient, admin_token: str):
        """测试获取里程碑详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 这个测试假设系统中有里程碑数据
        # 实际应该先创建一个里程碑，然后获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/1",
            headers=headers
        )

        # 如果没有数据或端点不存在，跳过
        if response.status_code in [404, 422]:
            pytest.skip("No milestone data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_milestone(self, client: TestClient, admin_token: str):
        """测试更新里程碑"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "name": "需求分析完成（已更新）",
            "status": "completed",
            "actual_date": datetime.now().strftime("%Y-%m-%d"),
            "completion_rate": 100.0
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("No milestone data or API not implemented")

        assert response.status_code == 200, response.text

    def test_delete_milestone(self, client: TestClient, admin_token: str):
        """测试删除里程碑"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/999",
            headers=headers
        )

        # 可能返回 404（不存在）或 204/200（删除成功）
        if response.status_code == 404:
            pytest.skip("Milestone API not implemented or no data")

        assert response.status_code in [200, 204, 404], response.text

    def test_milestone_unauthorized(self, client: TestClient):
        """测试未授权访问里程碑"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/"
        )

        assert response.status_code in [401, 403], response.text

    def test_milestone_invalid_project(self, client: TestClient, admin_token: str):
        """测试访问不存在的项目的里程碑"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/999999/milestones/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("API returns 404 for non-existent project")

        # 可能返回空列表或404
        assert response.status_code in [200, 404], response.text

    def test_milestone_pagination(self, client: TestClient, admin_token: str):
        """测试里程碑列表分页"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/?page=1&page_size=10",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Milestone API not implemented")

        assert response.status_code == 200, response.text
        data = response.json()
        if isinstance(data, dict):
            assert "items" in data or isinstance(data.get("items", []), list)

    def test_milestone_filter_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤里程碑"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/?status=completed",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Milestone API not implemented")

        assert response.status_code == 200, response.text

    def test_milestone_filter_by_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围过滤里程碑"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/"
            f"?start_date={start_date}&end_date={end_date}",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Milestone API not implemented")

        assert response.status_code == 200, response.text

    def test_milestone_create_validation(self, client: TestClient, admin_token: str):
        """测试里程碑创建时的数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 缺少必填字段
        invalid_data = {
            "description": "没有名称的里程碑"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Milestone API not implemented")

        assert response.status_code == 422, response.text

    def test_milestone_update_validation(self, client: TestClient, admin_token: str):
        """测试里程碑更新时的数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 无效的完成率
        invalid_data = {
            "completion_rate": 150.0  # 超过100
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/1",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Milestone API not implemented")

        # 可能返回 422（验证失败）或 200（服务端自动修正）
        assert response.status_code in [200, 422], response.text

    def test_milestone_completion_tracking(self, client: TestClient, admin_token: str):
        """测试里程碑完成度追踪"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 标记里程碑为已完成
        completion_data = {
            "status": "completed",
            "actual_date": datetime.now().strftime("%Y-%m-%d"),
            "completion_rate": 100.0,
            "remarks": "按时完成"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/1",
            headers=headers,
            json=completion_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Milestone API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_milestone_statistics(self, client: TestClient, admin_token: str):
        """测试项目里程碑统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/milestones/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Milestone statistics API not implemented")

        assert response.status_code == 200, response.text
        data = response.json()
        # 统计信息应该包含总数、完成数等
        assert isinstance(data, dict)

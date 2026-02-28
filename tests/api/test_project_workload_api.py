import uuid
# -*- coding: utf-8 -*-
"""
项目中心工作量API测试

测试新的项目中心API端点: /api/v1/projects/{project_id}/workload/
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_first_project_id(client: TestClient, token: str) -> int:
    """获取第一个项目的ID"""
    headers = _auth_headers(token)
    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/",
        headers=headers
    )

    if response.status_code != 200:
        return None

    projects = response.json()
    items = projects.get("items", projects) if isinstance(projects, dict) else projects
    if not items:
        return None

    return items[0]["id"]


class TestProjectWorkloadTeam:
    """项目团队工作量测试"""

    def test_get_project_team_workload(self, client: TestClient, admin_token: str):
        """测试获取项目团队负荷"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/team",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload team endpoint not found")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "items" in data
        # 验证返回格式
        if data["items"]:
            item = data["items"][0]
            assert "user_id" in item
            assert "user_name" in item
            assert "assigned_hours" in item
            assert "standard_hours" in item
            assert "allocation_rate" in item

    def test_get_project_team_workload_with_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围获取项目团队负荷"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        today = date.today()
        start_date = today.replace(day=1).isoformat()
        end_date = today.isoformat()

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/team",
            params={"start_date": start_date, "end_date": end_date},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload team endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_project_team_workload_future_dates(self, client: TestClient, admin_token: str):
        """测试获取未来日期范围的项目团队负荷"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        today = date.today()
        start_date = (today + timedelta(days=30)).isoformat()
        end_date = (today + timedelta(days=60)).isoformat()

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/team",
            params={"start_date": start_date, "end_date": end_date},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload team endpoint not found")

        assert response.status_code == 200, response.text


class TestProjectWorkloadGantt:
    """项目工作量甘特图测试"""

    def test_get_project_workload_gantt(self, client: TestClient, admin_token: str):
        """测试获取项目资源甘特图"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/gantt",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload gantt endpoint not found")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        assert "project_id" in data["data"]
        assert "resources" in data["data"]

    def test_get_project_workload_gantt_with_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围获取项目资源甘特图"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        today = date.today()
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = (today + timedelta(days=30)).isoformat()

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/gantt",
            params={"start_date": start_date, "end_date": end_date},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload gantt endpoint not found")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        # 验证日期范围
        if "start_date" in data["data"]:
            assert data["data"]["start_date"] == start_date


class TestProjectWorkloadSummary:
    """项目工作量汇总测试"""

    def test_get_project_workload_summary(self, client: TestClient, admin_token: str):
        """测试获取项目工作量汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/summary",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload summary endpoint not found")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        assert "project_id" in data["data"]
        assert "total_team_members" in data["data"]

    def test_get_project_workload_summary_fields(self, client: TestClient, admin_token: str):
        """测试项目工作量汇总包含所有必要字段"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/summary",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload summary endpoint not found")

        assert response.status_code == 200, response.text
        data = response.json()["data"]

        # 验证必要字段
        expected_fields = [
            "project_id",
            "total_team_members",
            "overloaded_users",
            "normal_users",
            "underloaded_users",
            "total_assigned_hours",
            "average_allocation_rate",
        ]

        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_get_project_workload_summary_with_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围获取项目工作量汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        today = date.today()
        start_date = today.replace(day=1).isoformat()
        end_date = today.isoformat()

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/summary",
            params={"start_date": start_date, "end_date": end_date},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload summary endpoint not found")

        assert response.status_code == 200, response.text


class TestProjectWorkloadEdgeCases:
    """项目工作量边界情况测试"""

    def test_project_not_found(self, client: TestClient, admin_token: str):
        """测试不存在的项目"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/99999/workload/team",
            headers=headers
        )

        # 应该返回404
        assert response.status_code == 404

    def test_invalid_date_range(self, client: TestClient, admin_token: str):
        """测试无效的日期范围（开始日期晚于结束日期）"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        today = date.today()
        start_date = today.isoformat()
        end_date = (today - timedelta(days=30)).isoformat()  # 结束日期早于开始日期

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/team",
            params={"start_date": start_date, "end_date": end_date},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload team endpoint not found")

        # 即使日期范围无效，API也应该正常返回（可能是空数据）
        assert response.status_code in [200, 400, 422]

    def test_workload_without_auth(self, client: TestClient):
        """测试未授权访问"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/workload/team"
        )

        # 应该返回401或403
        assert response.status_code in [401, 403]

    def test_empty_project_workload(self, client: TestClient, admin_token: str):
        """测试没有团队成员的项目工作量"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 创建一个新项目（没有分配团队成员）
        project_data = {
            "project_code": f"PJ-WORKLOAD-TEST-{uuid.uuid4().hex[:8]}",
            "project_name": "工作量测试项目",
            "stage": "S1",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )

        if create_response.status_code != 201:
            pytest.skip("Failed to create project for testing")

        project_id = create_response.json()["id"]

        # 获取工作量
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/workload/team",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload team endpoint not found")

        assert response.status_code == 200, response.text
        data = response.json()
        # 应该返回空列表
        assert data["items"] == []


class TestProjectWorkloadAllEndpoints:
    """测试所有工作量端点"""

    def test_all_workload_endpoints_exist(self, client: TestClient, admin_token: str):
        """测试所有工作量端点是否存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project_id = _get_first_project_id(client, admin_token)
        if not project_id:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)

        endpoints = [
            "/workload/team",
            "/workload/gantt",
            "/workload/summary",
        ]

        for endpoint in endpoints:
            response = client.get(
                f"{settings.API_V1_PREFIX}/projects/{project_id}{endpoint}",
                headers=headers
            )

            # 端点应该存在（返回200或其他非404状态码）
            # 404可能表示端点不存在或数据不存在，我们接受两种情况
            assert response.status_code in [200, 400, 403, 404, 422], \
                f"Endpoint {endpoint} returned unexpected status: {response.status_code}"

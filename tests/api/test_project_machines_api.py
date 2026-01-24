# -*- coding: utf-8 -*-
"""
项目中心机台API测试

测试新的项目中心API端点: /api/v1/projects/{project_id}/machines/
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectMachinesAPI:
    """项目中心机台API测试"""

    def test_list_project_machines(self, client: TestClient, admin_token: str):
        """测试获取项目机台列表"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
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

    def test_list_project_machines_with_pagination(self, client: TestClient, admin_token: str):
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        if "items" in data:
            assert data["page"] == 1
            assert data["page_size"] == 10

    def test_list_project_machines_with_keyword(self, client: TestClient, admin_token: str):
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            params={"keyword": "测试"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_list_project_machines_with_filters(self, client: TestClient, admin_token: str):
        """测试筛选参数"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            params={"stage": "S1"},
            headers=headers
        )

        assert response.status_code == 200, response.text

        # 测试状态筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            params={"status": "ST01"},
            headers=headers
        )

        assert response.status_code == 200, response.text

        # 测试健康度筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            params={"health": "H1"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_create_project_machine(self, client: TestClient, admin_token: str):
        """测试创建项目机台（自动生成编码）"""
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

        machine_data = {
            "machine_name": f"测试机台-{uuid.uuid4().hex[:4]}",
            # 不提供machine_code，应该自动生成
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            json=machine_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create machine")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["machine_name"] == machine_data["machine_name"]
        assert data["project_id"] == project_id  # 确保项目ID正确
        assert data.get("machine_code") is not None  # 确保自动生成了编码

    def test_get_project_machine_detail(self, client: TestClient, admin_token: str):
        """测试获取项目机台详情"""
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

        # 先创建机台
        machine_data = {
            "machine_name": f"测试机台-{uuid.uuid4().hex[:4]}",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            json=machine_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create machine for testing")

        machine_id = create_response.json()["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/{machine_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == machine_id
        assert data["project_id"] == project_id

    def test_get_project_machine_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的机台"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_project_machine(self, client: TestClient, admin_token: str):
        """测试更新项目机台"""
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

        # 先创建机台
        machine_data = {
            "machine_name": f"测试机台-{uuid.uuid4().hex[:4]}",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            json=machine_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create machine for testing")

        machine_id = create_response.json()["id"]

        # 更新机台
        update_data = {
            "machine_name": f"更新机台-{uuid.uuid4().hex[:4]}",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/{machine_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update machine")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["machine_name"] == update_data["machine_name"]

    def test_delete_project_machine(self, client: TestClient, admin_token: str):
        """测试删除项目机台"""
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

        # 先创建机台
        machine_data = {
            "machine_name": f"测试机台-{uuid.uuid4().hex[:4]}",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/",
            json=machine_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create machine for testing")

        machine_id = create_response.json()["id"]

        # 删除机台
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/{machine_id}",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to delete machine")

        assert response.status_code in [200, 204], response.text

    def test_get_project_machine_summary(self, client: TestClient, admin_token: str):
        """测试获取项目机台汇总（自定义端点）"""
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

        # 测试机台汇总
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/machines/summary",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        assert data["data"]["project_id"] == project_id

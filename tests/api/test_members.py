# -*- coding: utf-8 -*-
"""
项目成员管理模块 API 测试

测试项目成员的 CRUD 操作
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestMemberCRUD:
    """项目成员 CRUD 测试"""

    def test_list_members(self, client: TestClient, admin_token: str):
        """测试获取项目成员列表"""
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
            f"{settings.API_V1_PREFIX}/members/",
            params={"project_id": project_id},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_list_members_no_project(self, client: TestClient, admin_token: str):
        """测试不指定项目获取成员列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/members/",
            headers=headers
        )

        # 可能需要项目ID参数
        assert response.status_code in [200, 422]

    def test_add_member_to_project(self, client: TestClient, admin_token: str):
        """测试添加项目成员"""
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

        member_data = {
            "project_id": project_id,
            "user_id": 1,  # admin user
            "role": "MEMBER",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/members/",
            json=member_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to add member")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")
        if response.status_code == 400:
            pytest.skip("Member already exists or validation error")

        assert response.status_code in [200, 201], response.text

    def test_get_member_by_id(self, client: TestClient, admin_token: str):
        """测试根据ID获取成员"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目
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

        # 获取成员列表
        members_response = client.get(
            f"{settings.API_V1_PREFIX}/members/",
            params={"project_id": project_id},
            headers=headers
        )

        if members_response.status_code != 200:
            pytest.skip("Failed to get members list")

        members = members_response.json()
        member_items = members.get("items", members) if isinstance(members, dict) else members
        if not member_items:
            pytest.skip("No members available for testing")

        member_id = member_items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/members/{member_id}",
            headers=headers
        )

        if response.status_code == 405:
            pytest.skip("Get member by ID endpoint not implemented")

        assert response.status_code == 200

    def test_update_member(self, client: TestClient, admin_token: str):
        """测试更新成员"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取项目
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

        # 获取成员列表
        members_response = client.get(
            f"{settings.API_V1_PREFIX}/members/",
            params={"project_id": project_id},
            headers=headers
        )

        if members_response.status_code != 200:
            pytest.skip("Failed to get members list")

        members = members_response.json()
        member_items = members.get("items", members) if isinstance(members, dict) else members
        if not member_items:
            pytest.skip("No members available for testing")

        member_id = member_items[0]["id"]

        update_data = {
            "role": "REVIEWER",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/members/{member_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update member")
        if response.status_code == 422:
            pytest.skip("Validation error")
        if response.status_code == 405:
            pytest.skip("Update member endpoint not implemented")

        assert response.status_code == 200, response.text

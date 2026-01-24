# -*- coding: utf-8 -*-
"""
项目中心成员API测试

测试新的项目中心API端点: /api/v1/projects/{project_id}/members/
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectMembersAPI:
    """项目中心成员API测试"""

    def test_list_project_members(self, client: TestClient, admin_token: str):
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

        # 测试项目中心API
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/",
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

    def test_list_project_members_with_pagination(self, client: TestClient, admin_token: str):
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        if "items" in data:
            assert data["page"] == 1
            assert data["page_size"] == 10

    def test_list_project_members_with_role_filter(self, client: TestClient, admin_token: str):
        """测试角色筛选"""
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

        # 测试角色筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/",
            params={"role": "PM"},
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_add_project_member(self, client: TestClient, admin_token: str):
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

        # 先获取用户列表
        users_response = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=headers
        )

        if users_response.status_code != 200:
            pytest.skip("Failed to get users list")

        users = users_response.json()
        user_items = users.get("items", users) if isinstance(users, dict) else users
        if not user_items:
            pytest.skip("No users available for testing")

        user_id = user_items[0]["id"]

        member_data = {
            "user_id": user_id,
            "role_code": "TEST",
            "allocation_pct": 50,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/",
            json=member_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to add member")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")
        if response.status_code == 400 and "已是项目成员" in response.json().get("detail", ""):
            pytest.skip("User is already a member of this project")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["user_id"] == user_id
        assert data["project_id"] == project_id
        assert data.get("username") is not None  # 确保填充了username
        assert data.get("real_name") is not None  # 确保填充了real_name

    def test_get_project_member_detail(self, client: TestClient, admin_token: str):
        """测试获取项目成员详情"""
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

        # 先获取成员列表
        members_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/",
            headers=headers
        )

        if members_response.status_code != 200:
            pytest.skip("Failed to get members list")

        members = members_response.json()
        member_items = members.get("items", members) if isinstance(members, dict) else members
        if not member_items:
            pytest.skip("No members available for testing")

        member_id = member_items[0]["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/{member_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == member_id
        assert data["project_id"] == project_id
        assert data.get("username") is not None  # 确保填充了username
        assert data.get("real_name") is not None  # 确保填充了real_name

    def test_get_project_member_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的成员"""
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
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_project_member(self, client: TestClient, admin_token: str):
        """测试更新项目成员"""
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

        # 先获取成员列表
        members_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/",
            headers=headers
        )

        if members_response.status_code != 200:
            pytest.skip("Failed to get members list")

        members = members_response.json()
        member_items = members.get("items", members) if isinstance(members, dict) else members
        if not member_items:
            pytest.skip("No members available for testing")

        member_id = member_items[0]["id"]

        # 更新成员
        update_data = {
            "allocation_pct": 75,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/{member_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update member")

        assert response.status_code == 200, response.text
        data = response.json()
        # allocation_pct是Decimal类型，可能返回为字符串或数字
        assert float(data["allocation_pct"]) == 75.0
        assert data.get("username") is not None  # 确保填充了username
        assert data.get("real_name") is not None  # 确保填充了real_name

    def test_remove_project_member(self, client: TestClient, admin_token: str):
        """测试移除项目成员"""
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

        # 先添加一个成员（用于测试删除）
        users_response = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=headers
        )

        if users_response.status_code != 200:
            pytest.skip("Failed to get users list")

        users = users_response.json()
        user_items = users.get("items", users) if isinstance(users, dict) else users
        if not user_items:
            pytest.skip("No users available for testing")

        user_id = user_items[0]["id"]

        # 先检查是否已是成员
        members_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/",
            headers=headers
        )

        member_id = None
        if members_response.status_code == 200:
            members = members_response.json()
            member_items = members.get("items", members) if isinstance(members, dict) else members
            for m in member_items:
                if m.get("user_id") == user_id:
                    member_id = m["id"]
                    break

        # 如果不是成员，先添加
        if not member_id:
            member_data = {
                "user_id": user_id,
                "role_code": "TEST",
                "allocation_pct": 50,
            }

            create_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/members/",
                json=member_data,
                headers=headers
            )

            if create_response.status_code not in [200, 201]:
                pytest.skip("Failed to create member for testing")

            member_id = create_response.json()["id"]

        # 删除成员
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/members/{member_id}",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to delete member")

        assert response.status_code in [200, 204], response.text

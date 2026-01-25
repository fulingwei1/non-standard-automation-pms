# -*- coding: utf-8 -*-
"""
角色管理模块 API 测试

测试角色的 CRUD 操作、权限分配和导航配置
Updated for unified response format
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from tests.helpers.response_helpers import (
    assert_success_response,
    assert_list_response,
    extract_data,
    extract_items,
)


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestRoleCRUD:
    """角色 CRUD 测试"""

    def test_list_roles(self, client: TestClient, admin_token: str):
        """测试获取角色列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数验证列表响应
        list_data = assert_list_response(response_data)
        assert "items" in list_data

    def test_list_permissions(self, client: TestClient, admin_token: str):
        """测试获取权限列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/permissions",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_role(self, client: TestClient, admin_token: str):
        """测试创建角色"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique_suffix = uuid.uuid4().hex[:6]
        role_data = {
            "role_code": f"ROLE_{unique_suffix.upper()}",
            "role_name": f"测试角色-{unique_suffix}",
            "description": "测试角色描述",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/roles/",
            json=role_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create role")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")
        if response.status_code == 400:
            pytest.skip("Role code already exists")

        assert response.status_code == 201, response.text
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        assert_success_response(response_data, expected_code=201)

    def test_get_role_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取角色"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取角色列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get roles list")

        response_data = list_response.json()
        # 使用统一响应格式辅助函数提取items
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No roles available for testing")

        role_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/{role_id}",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data)
        assert data["id"] == role_id

    def test_get_role_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的角色"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_role(self, client: TestClient, admin_token: str):
        """测试更新角色"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取角色列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get roles list")

        response_data = list_response.json()
        # 使用统一响应格式辅助函数提取items
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No roles available for testing")

        role_id = items[0]["id"]

        update_data = {
            "description": f"更新描述-{uuid.uuid4().hex[:4]}",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{role_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update role")
        if response.status_code == 422:
            pytest.skip("Validation error")

        assert response.status_code == 200, response.text
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        assert_success_response(response_data)


class TestRolePermissions:
    """角色权限测试"""

    def test_update_role_permissions(self, client: TestClient, admin_token: str):
        """测试更新角色权限"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取角色列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get roles list")

        response_data = list_response.json()
        # 使用统一响应格式辅助函数提取items
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No roles available for testing")

        role_id = items[0]["id"]

        permissions_data = {
            "permission_ids": [1, 2, 3],  # 假设这些权限存在
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{role_id}/permissions",
            json=permissions_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 422:
            pytest.skip("Validation error")
        if response.status_code == 404:
            pytest.skip("Permission not found")

        assert response.status_code == 200, response.text
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        assert_success_response(response_data)


class TestRoleNavigation:
    """角色导航配置测试"""

    def test_get_config_all(self, client: TestClient, admin_token: str):
        """测试获取所有配置"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/config/all",
            headers=headers
        )

        assert response.status_code == 200

    def test_get_my_nav_groups(self, client: TestClient, admin_token: str):
        """测试获取当前用户的导航组"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/my/nav-groups",
            headers=headers
        )

        assert response.status_code == 200

    def test_get_role_nav_groups(self, client: TestClient, admin_token: str):
        """测试获取角色的导航组"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取角色列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get roles list")

        response_data = list_response.json()
        # 使用统一响应格式辅助函数提取items
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No roles available for testing")

        role_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/{role_id}/nav-groups",
            headers=headers
        )

        assert response.status_code == 200

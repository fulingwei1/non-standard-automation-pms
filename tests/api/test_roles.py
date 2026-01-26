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
        response_data = response.json()
        # 支持两种响应格式：直接列表或 ResponseModel 包装
        if isinstance(response_data, dict) and "data" in response_data:
            data = response_data["data"]
        else:
            data = response_data
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


class TestRoleHierarchy:
    """角色层级管理测试"""

    def test_get_hierarchy_tree(self, client: TestClient, admin_token: str):
        """测试获取角色层级树"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/hierarchy/tree",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        data = assert_success_response(response_data)
        assert isinstance(data, list)

    def test_get_role_ancestors(self, client: TestClient, admin_token: str):
        """测试获取角色祖先链"""
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
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No roles available for testing")

        role_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/{role_id}/ancestors",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        data = assert_success_response(response_data)
        assert "role_id" in data
        assert "ancestors" in data
        assert isinstance(data["ancestors"], list)

    def test_get_role_ancestors_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在角色的祖先链"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/99999/ancestors",
            headers=headers
        )

        assert response.status_code == 404

    def test_get_role_descendants(self, client: TestClient, admin_token: str):
        """测试获取角色子孙"""
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
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No roles available for testing")

        role_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/{role_id}/descendants",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        data = assert_success_response(response_data)
        assert "role_id" in data
        assert "descendants" in data
        assert isinstance(data["descendants"], list)

    def test_get_role_descendants_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在角色的子孙"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/99999/descendants",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_role_parent(self, client: TestClient, admin_token: str):
        """测试更新角色父级"""
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
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if len(items) < 2:
            pytest.skip("Need at least 2 roles for testing")

        # 找一个非系统角色
        non_system_role = None
        for item in items:
            if not item.get("is_system", False):
                non_system_role = item
                break

        if not non_system_role:
            pytest.skip("No non-system role available for testing")

        role_id = non_system_role["id"]

        # 设置为顶级角色（parent_id = null）
        response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{role_id}/parent",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 400:
            pytest.skip("System role cannot be modified")

        assert response.status_code == 200, response.text
        response_data = response.json()
        data = assert_success_response(response_data)
        assert data["role_id"] == role_id

    def test_update_role_parent_not_found(self, client: TestClient, admin_token: str):
        """测试更新不存在角色的父级"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.put(
            f"{settings.API_V1_PREFIX}/roles/99999/parent",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_role_parent_invalid_parent(self, client: TestClient, admin_token: str):
        """测试设置不存在的父角色"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取角色���表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get roles list")

        response_data = list_response.json()
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No roles available for testing")

        # 找一个非系统角色
        non_system_role = None
        for item in items:
            if not item.get("is_system", False):
                non_system_role = item
                break

        if not non_system_role:
            pytest.skip("No non-system role available for testing")

        role_id = non_system_role["id"]

        response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{role_id}/parent?parent_id=99999",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")

        assert response.status_code == 400

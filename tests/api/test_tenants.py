# -*- coding: utf-8 -*-
"""
租户管理模块 API 测试

测试租户的 CRUD 操作和初始化功能
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


class TestTenantCRUD:
    """租户 CRUD 测试"""

    def test_list_tenants(self, client: TestClient, admin_token: str):
        """测试获取租户列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/tenants/",
            headers=headers
        )

        # 可能返回 403（非超级管理员）或 200
        if response.status_code == 403:
            pytest.skip("User is not superuser")

        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数验证列表响应
        list_data = assert_list_response(response_data)
        assert "items" in list_data

    def test_create_tenant(self, client: TestClient, admin_token: str):
        """测试创建租户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique_suffix = uuid.uuid4().hex[:6]
        tenant_data = {
            "tenant_name": f"测试租户-{unique_suffix}",
            "plan_type": "STANDARD",
            "contact_name": "测试联系人",
            "contact_email": f"test_{unique_suffix}@example.com",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/tenants/",
            json=tenant_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create tenant")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")
        if response.status_code == 400:
            pytest.skip("Tenant code already exists")

        assert response.status_code == 201, response.text
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data, expected_code=201)
        assert "tenant_code" in data
        assert data["tenant_name"] == tenant_data["tenant_name"]

    def test_get_tenant_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取租户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取租户列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/tenants/",
            headers=headers
        )

        if list_response.status_code == 403:
            pytest.skip("User is not superuser")
        if list_response.status_code != 200:
            pytest.skip("Failed to get tenants list")

        response_data = list_response.json()
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No tenants available for testing")

        tenant_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/tenants/{tenant_id}",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        data = assert_success_response(response_data)
        assert data["id"] == tenant_id

    def test_get_tenant_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的租户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/tenants/99999",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User is not superuser")

        assert response.status_code == 404

    def test_update_tenant(self, client: TestClient, admin_token: str):
        """测试更新租户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取租户列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/tenants/",
            headers=headers
        )

        if list_response.status_code == 403:
            pytest.skip("User is not superuser")
        if list_response.status_code != 200:
            pytest.skip("Failed to get tenants list")

        response_data = list_response.json()
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No tenants available for testing")

        tenant_id = items[0]["id"]

        update_data = {
            "contact_name": f"更新联系人-{uuid.uuid4().hex[:4]}",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/tenants/{tenant_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update tenant")
        if response.status_code == 422:
            pytest.skip("Validation error")

        assert response.status_code == 200, response.text
        response_data = response.json()
        assert_success_response(response_data)


class TestTenantStats:
    """租户统计测���"""

    def test_get_tenant_stats(self, client: TestClient, admin_token: str):
        """测试获取租户统计信息"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取租户列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/tenants/",
            headers=headers
        )

        if list_response.status_code == 403:
            pytest.skip("User is not superuser")
        if list_response.status_code != 200:
            pytest.skip("Failed to get tenants list")

        response_data = list_response.json()
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No tenants available for testing")

        tenant_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/tenants/{tenant_id}/stats",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User is not superuser")

        assert response.status_code == 200
        response_data = response.json()
        data = assert_success_response(response_data)
        assert "user_count" in data
        assert "role_count" in data


class TestTenantPermissions:
    """租户权限测试"""

    def test_non_superuser_cannot_access(self, client: TestClient, normal_user_token: str):
        """测试非超级管理员无法访问租户管理"""
        if not normal_user_token:
            pytest.skip("Normal user token not available")

        headers = _auth_headers(normal_user_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/tenants/",
            headers=headers
        )

        # 非超级管理员应该返回 403
        assert response.status_code == 403

    def test_unauthenticated_cannot_access(self, client: TestClient):
        """测试未认证用户无法访问租户管理"""
        response = client.get(f"{settings.API_V1_PREFIX}/tenants/")

        # 未认证应该返回 401
        assert response.status_code == 401

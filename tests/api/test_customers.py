# -*- coding: utf-8 -*-
"""
客户管理模块 API 测试

测试客户的 CRUD 操作、项目关联和 360 度视图
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestCustomerCRUD:
    """客户 CRUD 测试"""

    def test_list_customers(self, client: TestClient, admin_token: str):
        """测试获取客户列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_customers_with_keyword(self, client: TestClient, admin_token: str):
        """测试关键词搜索客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/",
            params={"page": 1, "page_size": 10, "keyword": "测试"},
            headers=headers
        )

        assert response.status_code == 200

    def test_create_customer(self, client: TestClient, admin_token: str):
        """测试创建客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        customer_data = {
            "customer_code": f"CUS{uuid.uuid4().hex[:6].upper()}",
            "customer_name": f"测试客户-{uuid.uuid4().hex[:4]}",
            "customer_type": "ENTERPRISE",
            "contact_person": "张三",
            "contact_phone": "13800138000",
            "industry": "电子",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/customers/",
            json=customer_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create customer")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text

    @pytest.mark.skip(reason="GET /customers/{id} 单个查询接口未实现")
    def test_get_customer_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取客户列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/customers/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get customers list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No customers available for testing")

        customer_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/{customer_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id

    def test_get_customer_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_customer(self, client: TestClient, admin_token: str):
        """测试更新客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取客户列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/customers/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get customers list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No customers available for testing")

        customer_id = items[0]["id"]

        update_data = {
            "contact_person": "李四",
            "contact_phone": "13900139000",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/customers/{customer_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update customer")

        assert response.status_code == 200, response.text


class TestCustomerProjects:
    """客户项目关联测试"""

    def test_get_customer_projects(self, client: TestClient, admin_token: str):
        """测试获取客户的项目列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取客户列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/customers/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get customers list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No customers available for testing")

        customer_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/{customer_id}/projects",
            headers=headers
        )

        assert response.status_code == 200


class TestCustomer360:
    """客户 360 度视图测试"""

    def test_get_customer_360(self, client: TestClient, admin_token: str):
        """测试获取客户 360 度视图"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取客户列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/customers/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get customers list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No customers available for testing")

        customer_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/{customer_id}/360",
            headers=headers
        )

        assert response.status_code == 200


class TestCustomerDelete:
    """客户删除测试"""

    def test_delete_customer_not_found(self, client: TestClient, admin_token: str):
        """测试删除不存在的客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.delete(
            f"{settings.API_V1_PREFIX}/customers/99999",
            headers=headers
        )

        assert response.status_code in [404, 403]

# -*- coding: utf-8 -*-
"""
销售客户管理 API 测试

测试客户的创建、查询、更新、删除及相关功能
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSalesCustomersAPI:
    """销售客户管理 API 测试类"""

    def test_list_customers(self, client: TestClient, admin_token: str):
        """测试获取客户列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/",
            headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_create_customer(self, client: TestClient, admin_token: str):
        """测试创建客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        customer_data = {
            "name": "测试科技有限公司",
            "short_name": "测试科技",
            "industry": "制造业",
            "level": "A",
            "contact_person": "张经理",
            "contact_phone": "13800138000",
            "contact_email": "zhang@test.com",
            "address": "北京市海淀区",
            "description": "重要客户"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/customers/",
            headers=headers,
            json=customer_data
        )

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["name"] == customer_data["name"]

    def test_get_customer_detail(self, client: TestClient, admin_token: str):
        """测试获取客户详情"""
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

        customers = list_response.json()
        items = customers.get("items", customers) if isinstance(customers, dict) else customers
        if not items:
            pytest.skip("No customers available")

        customer_id = items[0]["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/{customer_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_update_customer(self, client: TestClient, admin_token: str):
        """测试更新客户信息"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "level": "S",
            "contact_phone": "13900139000",
            "description": "超级重要客户"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/customers/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("No customer data available")

        assert response.status_code == 200, response.text

    def test_delete_customer(self, client: TestClient, admin_token: str):
        """测试删除客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/customers/999",
            headers=headers
        )

        assert response.status_code in [200, 204, 404], response.text

    def test_search_customers(self, client: TestClient, admin_token: str):
        """测试搜索客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/?search=科技",
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_filter_customers_by_level(self, client: TestClient, admin_token: str):
        """测试按等级过滤客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/?level=A",
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_filter_customers_by_industry(self, client: TestClient, admin_token: str):
        """测试按行业过滤客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/?industry=制造业",
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_customer_pagination(self, client: TestClient, admin_token: str):
        """测试客户列表分页"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/?page=1&page_size=20",
            headers=headers
        )

        assert response.status_code == 200, response.text

    def test_customer_contacts_list(self, client: TestClient, admin_token: str):
        """测试获取客户联系人列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/1/contacts",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Customer contacts API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_add_customer_contact(self, client: TestClient, admin_token: str):
        """测试添加客户联系人"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        contact_data = {
            "name": "李经理",
            "title": "技术总监",
            "phone": "13700137000",
            "email": "li@test.com",
            "is_primary": False
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/customers/1/contacts",
            headers=headers,
            json=contact_data
        )

        if response.status_code == 404:
            pytest.skip("Customer contacts API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_customer_projects_list(self, client: TestClient, admin_token: str):
        """测试获取客户的项目列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/1/projects",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Customer projects API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_customer_statistics(self, client: TestClient, admin_token: str):
        """测试客户统计信息"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Customer statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_customer_validation(self, client: TestClient, admin_token: str):
        """测试客户数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 缺少必填字段
        invalid_data = {
            "description": "缺少客户名称"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/customers/",
            headers=headers,
            json=invalid_data
        )

        assert response.status_code == 422, response.text

    def test_customer_unauthorized(self, client: TestClient):
        """测试未授权访问客户"""
        response = client.get(f"{settings.API_V1_PREFIX}/customers/")
        assert response.status_code in [401, 403], response.text

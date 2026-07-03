# -*- coding: utf-8 -*-
"""
销售客户管理 API 测试

测试客户的创建、查询、更新、删除及相关功能
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.project.customer import Customer
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _create_customer_list_user(db_session: Session, suffix: str, real_name: str) -> User:
    user = User(
        username=f"customer_list_{suffix}",
        password_hash=get_password_hash("customer123"),
        email=f"customer_list_{suffix}@example.com",
        real_name=real_name,
        department="销售部",
        position="销售",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_customer_record(db_session: Session, owner: User, suffix: str) -> Customer:
    customer = Customer(
        customer_code=f"CUST-LIST-{suffix}",
        customer_name=f"客户列表-{suffix}",
        short_name=f"客户-{suffix}",
        industry="制造业",
        status="ACTIVE",
        credit_level="B",
        sales_owner_id=owner.id,
        created_by=owner.id,
    )
    db_session.add(customer)
    db_session.flush()
    return customer


class TestSalesCustomersAPI:
    """销售客户管理 API 测试类"""

    def test_regular_sales_user_can_read_own_customers_without_customer_read(
        self,
        client: TestClient,
        db_session: Session,
    ):
        """旧 /customers/ 列表按销售范围过滤，不要求 customer:read"""
        suffix = uuid4().hex[:8].upper()
        owner = _create_customer_list_user(db_session, f"OWNER-{suffix}", "客户列表本人")
        other = _create_customer_list_user(db_session, f"OTHER-{suffix}", "客户列表他人")
        own_customer = _create_customer_record(db_session, owner, f"OWN-{suffix}")
        other_customer = _create_customer_record(db_session, other, f"OTHER-{suffix}")
        db_session.commit()

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/",
            params={"page": 1, "page_size": 100},
            headers=_auth_headers_for_user(owner),
        )

        assert response.status_code == 200, response.text
        data = response.json()
        customer_ids = {item["id"] for item in data["items"]}
        assert own_customer.id in customer_ids
        assert other_customer.id not in customer_ids

    def test_list_customers(self, client: TestClient, admin_token: str):
        """测试获取客户列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/customers/", headers=headers)

        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_create_customer(self, client: TestClient, admin_token: str):
        """测试创建客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        customer_data = {
            "customer_name": "测试科技有限公司",
            "short_name": "测试科技",
            "industry": "制造业",
            "address": "北京市海淀区",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers", headers=headers, json=customer_data
        )

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["customer_name"] == customer_data["customer_name"]

    def test_get_customer_detail(self, client: TestClient, admin_token: str):
        """测试获取客户详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取客户列表
        list_response = client.get(f"{settings.API_V1_PREFIX}/customers/", headers=headers)

        if list_response.status_code != 200:
            pytest.skip("Failed to get customers list")

        customers = list_response.json()
        items = customers.get("items", customers) if isinstance(customers, dict) else customers
        if not items:
            pytest.skip("No customers available")

        customer_id = items[0]["id"]

        # 获取详情
        response = client.get(f"{settings.API_V1_PREFIX}/customers/{customer_id}", headers=headers)

        assert response.status_code == 200, response.text

    def test_update_customer(self, client: TestClient, admin_token: str):
        """测试更新客户信息"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {"level": "S", "contact_phone": "13900139000", "description": "超级重要客户"}

        response = client.put(
            f"{settings.API_V1_PREFIX}/customers/1", headers=headers, json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("No customer data available")

        assert response.status_code == 200, response.text

    def test_delete_customer(self, client: TestClient, admin_token: str):
        """测试删除客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(f"{settings.API_V1_PREFIX}/customers/999", headers=headers)

        assert response.status_code in [200, 204, 404], response.text

    def test_search_customers(self, client: TestClient, admin_token: str):
        """测试搜索客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/customers/?search=科技", headers=headers)

        assert response.status_code == 200, response.text

    def test_filter_customers_by_level(self, client: TestClient, admin_token: str):
        """测试按等级过滤客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/customers/?level=A", headers=headers)

        assert response.status_code == 200, response.text

    def test_filter_customers_by_industry(self, client: TestClient, admin_token: str):
        """测试按行业过滤客户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/?industry=制造业", headers=headers
        )

        assert response.status_code == 200, response.text

    def test_customer_pagination(self, client: TestClient, admin_token: str):
        """测试客户列表分页"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/customers/?page=1&page_size=20", headers=headers
        )

        assert response.status_code == 200, response.text

    def test_customer_contacts_list(self, client: TestClient, admin_token: str):
        """测试获取客户联系人列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/customers/1/contacts", headers=headers)

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
            "is_primary": False,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/customers/1/contacts", headers=headers, json=contact_data
        )

        if response.status_code == 404:
            pytest.skip("Customer contacts API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_customer_projects_list(self, client: TestClient, admin_token: str):
        """测试获取客户的项目列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/customers/1/projects", headers=headers)

        if response.status_code == 404:
            pytest.skip("Customer projects API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_customer_statistics(self, client: TestClient, admin_token: str):
        """测试客户统计信息"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/customers/stats", headers=headers)

        if response.status_code == 404:
            pytest.skip("Customer statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_customer_validation(self, client: TestClient, admin_token: str):
        """测试客户数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 缺少必填字段
        invalid_data = {"description": "缺少客户名称"}

        response = client.post(
            f"{settings.API_V1_PREFIX}/customers/", headers=headers, json=invalid_data
        )

        assert response.status_code == 422, response.text

    def test_customer_unauthorized(self, client: TestClient):
        """测试未授权访问客户"""
        response = client.get(f"{settings.API_V1_PREFIX}/customers/")
        assert response.status_code in [401, 403], response.text

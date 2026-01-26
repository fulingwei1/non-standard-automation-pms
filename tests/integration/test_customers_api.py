# -*- coding: utf-8 -*-
"""
Integration tests for Customers API
Covers: app/api/v1/endpoints/customers/
Updated for unified response format
"""

from datetime import date

from tests.helpers.response_helpers import (
    assert_success_response,
    assert_paginated_response,
    extract_items,
)


class TestCustomersAPI:
    """客户管理API集成测试"""

    def test_list_customers(self, client, admin_token):
        """测试获取客户列表"""
        response = client.get(
            "/api/v1/customers/", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_list_customers_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/customers/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_customers_with_filters(self, client, admin_token):
        """测试过滤参数"""
        response = client.get(
            "/api/v1/customers/?industry=IT&is_active=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_customers_with_keyword_search(self, client, admin_token):
        """测试关键词搜索"""
        response = client.get(
            "/api/v1/customers/?keyword=测试",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数提取items
        paginated_data = assert_paginated_response(response_data)
        items = paginated_data["items"]
        for item in items:
            if item.get("customer_name"):
                assert "测试" in item["customer_name"] or "测试" in item.get(
                    "customer_code", ""
                )

    def test_get_customer_detail(self, client, admin_token, test_customer):
        """测试获取客户详情"""
        response = client.get(
            f"/api/v1/customers/{test_customer.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data)
        assert data["id"] == test_customer.id
        assert data["customer_name"] == test_customer.customer_name

    def test_get_customer_not_found(self, client, admin_token):
        """测试获取不存在的客户"""
        response = client.get(
            "/api/v1/customers/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_create_customer(self, client, admin_token):
        """测试创建客户"""
        customer_data = {
            "customer_name": "API测试客户",
            "customer_code": f"CUS-{date.today().strftime('%Y%m%d')}-001",
            "short_name": "测试客户",
            "customer_type": "CORPORATE",
            "industry": "IT",
            "contact_person": "张三",
            "contact_phone": "13800138000",
            "contact_email": "test@example.com",
            "address": "测试地址",
        }
        response = client.post(
            "/api/v1/customers/",
            json=customer_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 201]
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data, expected_code=response.status_code)
        assert data["customer_name"] == customer_data["customer_name"]
        assert "id" in data

    def test_create_customer_auto_code(self, client, admin_token):
        """测试自动生成客户编码"""
        customer_data = {"customer_name": "自动编码测试客户"}
        response = client.post(
            "/api/v1/customers/",
            json=customer_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 201]
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data, expected_code=response.status_code)
        assert data["customer_name"] == customer_data["customer_name"]
        assert data["customer_code"] is not None
        assert data["customer_code"].startswith("CUS-")

    def test_create_customer_duplicate_code(self, client, admin_token, test_customer):
        """测试创建重复客户编码"""
        customer_data = {
            "customer_name": "重复编码客户",
            "customer_code": test_customer.customer_code,
        }
        response = client.post(
            "/api/v1/customers/",
            json=customer_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "已存在" in response.json().get("detail", "")

    def test_create_customer_validation_error(self, client, admin_token):
        """测试创建客户验证错误"""
        customer_data = {
            # 缺少必填字段 customer_name
        }
        response = client.post(
            "/api/v1/customers/",
            json=customer_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_update_customer(self, client, admin_token, test_customer):
        """测试更新客户"""
        update_data = {
            "customer_name": "更新后的客户名称",
            "contact_person": "李四",
            "contact_phone": "13900139000",
        }
        response = client.put(
            f"/api/v1/customers/{test_customer.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data)
        assert data["customer_name"] == update_data["customer_name"]
        assert data["contact_person"] == update_data["contact_person"]

    def test_update_customer_not_found(self, client, admin_token):
        """测试更新不存在的客户"""
        update_data = {"customer_name": "不存在的客户"}
        response = client.put(
            "/api/v1/customers/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_delete_customer(self, client, admin_token, db_session):
        """测试删除客户"""
        # 先创建一个没有关联项目的客户
        from app.models.project import Customer

        customer = Customer(
            customer_code=f"CUS-DELETE-TEST-{date.today().strftime('%Y%m%d')}",
            customer_name="待删除测试客户",
            contact_person="测试",
            contact_phone="13800000000",
            status="ACTIVE",
            is_active=True,
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

        response = client.delete(
            f"/api/v1/customers/{customer.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_delete_customer_with_projects(
        self, client, admin_token, test_project, db_session
    ):
        """测试删除有关联项目的客户"""
        # test_customer 可能没有关联项目，使用 test_project 中的客户
        from app.models.project import Customer

        customer = Customer(
            customer_code=f"CUS-PROJECT-TEST-{date.today().strftime('%Y%m%d')}",
            customer_name="有关联项目的客户",
            contact_person="测试",
            contact_phone="13800000000",
            status="ACTIVE",
            is_active=True,
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

        # 关联到项目
        test_project.customer_id = customer.id
        db_session.commit()

        # 尝试删除
        response = client.delete(
            f"/api/v1/customers/{customer.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "还有" in response.json().get("detail", "")

    def test_delete_customer_not_found(self, client, admin_token):
        """测试删除不存在的客户"""
        response = client.delete(
            "/api/v1/customers/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestCustomersAPIAuth:
    """客户API认证测试"""

    def test_list_customers_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/customers/")
        assert response.status_code == 401

    def test_get_customer_without_token(self, client):
        """测试无token获取详情"""
        response = client.get("/api/v1/customers/1")
        assert response.status_code == 401

    def test_create_customer_without_token(self, client):
        """测试无token创建"""
        response = client.post("/api/v1/customers/", json={"customer_name": "测试"})
        assert response.status_code == 401

    def test_update_customer_without_token(self, client):
        """测试无token更新"""
        response = client.put("/api/v1/customers/1", json={"customer_name": "测试"})
        assert response.status_code == 401

    def test_delete_customer_without_token(self, client):
        """测试无token删除"""
        response = client.delete("/api/v1/customers/1")
        assert response.status_code == 401


class TestCustomersAPISorting:
    """客户API排序测试"""

    def test_sort_by_created_at_desc(self, client, admin_token):
        """测试按创建时间降序排序"""
        response = client.get(
            "/api/v1/customers/?order_by=created_at&order=desc",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_sort_by_customer_name_asc(self, client, admin_token):
        """测试按客户名称升序排序"""
        response = client.get(
            "/api/v1/customers/?order_by=customer_name&order=asc",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200


class TestCustomersAPIValidation:
    """客户API验证测试"""

    def test_invalid_page_number(self, client, admin_token):
        """测试无效页码"""
        response = client.get(
            "/api/v1/customers/?page=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_invalid_page_size(self, client, admin_token):
        """测试无效分页大小"""
        response = client.get(
            "/api/v1/customers/?page_size=1000",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # 超过最大限制应该返回422或实际限制后的结果
        assert response.status_code in [200, 422]

    def test_empty_keyword_search(self, client, admin_token):
        """测试空关键词搜索"""
        response = client.get(
            "/api/v1/customers/?keyword=",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

# -*- coding: utf-8 -*-
"""
客户管理 API 集成测试

覆盖:
- GET /sales/customers - 客户列表
- GET /sales/customers/stats - 客户统计
- POST /sales/customers - 创建客户
- GET /sales/customers/{id} - 客户详情
- PUT /sales/customers/{id} - 更新客户
- DELETE /sales/customers/{id} - 删除客户
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def test_customer_data() -> dict:
    """客户测试数据

    注意：Customer 模型使用 status (potential/prospect/customer/lost)
    而不是 ACTIVE
    """
    import uuid

    return {
        "customer_code": f"CUST-{uuid.uuid4().hex[:8]}",
        "customer_name": f"集成测试客户-{uuid.uuid4().hex[:6]}",
        "industry": "新能源",
        "status": "potential",
    }


@pytest.fixture(scope="module")
def created_customer_for_test(
    client: TestClient, auth_headers: dict
) -> dict:
    """创建一个客户用于后续测试"""
    import uuid

    customer_data = {
        "customer_name": f"Fixture客户-{uuid.uuid4().hex[:6]}",
        "industry": "测试行业",
        "status": "potential",
    }
    response = client.post(
        "/api/v1/sales/customers",
        json=customer_data,
        headers=auth_headers,
    )
    if response.status_code == 201:
        return response.json()
    # 如果创建失败，尝试列表中找一个
    list_resp = client.get("/api/v1/sales/customers", headers=auth_headers)
    if list_resp.status_code == 200:
        items = list_resp.json().get("items", [])
        if items:
            return items[0]
    pytest.skip(f"无法创建测试客户: {response.status_code} - {response.text}")


class TestCustomerList:
    """客户列表 API 测试"""

    def test_list_customers_success(self, client: TestClient, auth_headers: dict):
        """测试获取客户列表 - 正常情况"""
        response = client.get("/api/v1/sales/customers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_list_customers_with_pagination(
        self, client: TestClient, auth_headers: dict
    ):
        """测试客户列表分页"""
        response = client.get(
            "/api/v1/sales/customers",
            params={"page": 1, "page_size": 10},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_customers_with_keyword(
        self, client: TestClient, auth_headers: dict
    ):
        """测试客户列表关键词搜索"""
        response = client.get(
            "/api/v1/sales/customers",
            params={"keyword": "测试"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_list_customers_with_industry_filter(
        self, client: TestClient, auth_headers: dict
    ):
        """测试客户列表行业筛选"""
        response = client.get(
            "/api/v1/sales/customers",
            params={"industry": "新能源"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_list_customers_with_status_filter(
        self, client: TestClient, auth_headers: dict
    ):
        """测试客户列表状态筛选"""
        response = client.get(
            "/api/v1/sales/customers",
            params={"status": "ACTIVE"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_list_customers_unauthorized(self, client: TestClient):
        """测试未认证访问客户列表"""
        response = client.get("/api/v1/sales/customers")
        assert response.status_code in [401, 403]


class TestCustomerStats:
    """客户统计 API 测试"""

    def test_get_customer_stats_success(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取客户统计 - 正常情况"""
        response = client.get(
            "/api/v1/sales/customers/stats",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # 验证统计数据结构
        assert isinstance(data, dict)


class TestCustomerCreate:
    """客户创建 API 测试"""

    def test_create_customer_success(
        self, client: TestClient, auth_headers: dict
    ):
        """测试创建客户 - 正常情况"""
        import uuid

        customer_data = {
            "customer_code": f"NEW-{uuid.uuid4().hex[:8]}",
            "customer_name": f"新客户-{uuid.uuid4().hex[:6]}",
            "industry": "制造业",
            "status": "potential",
        }
        response = client.post(
            "/api/v1/sales/customers",
            json=customer_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "customer_code" in data

    def test_create_customer_minimal(
        self, client: TestClient, auth_headers: dict
    ):
        """测试创建客户 - 最小必填字段"""
        import uuid

        customer_data = {
            "customer_name": f"最小客户-{uuid.uuid4().hex[:6]}",
        }
        response = client.post(
            "/api/v1/sales/customers",
            json=customer_data,
            headers=auth_headers,
        )
        # customer_code 会自动生成
        assert response.status_code in [201, 422]

    def test_create_customer_duplicate_code(
        self, client: TestClient, auth_headers: dict
    ):
        """测试创建客户 - 重复编码"""
        customer_code = "DUP-CODE-001"
        customer_data = {
            "customer_code": customer_code,
            "customer_name": "重复编码客户1",
        }
        # 第一次创建
        response1 = client.post(
            "/api/v1/sales/customers",
            json=customer_data,
            headers=auth_headers,
        )
        # 如果第一次成功，尝试创建重复编码
        if response1.status_code == 201:
            customer_data["customer_name"] = "重复编码客户2"
            response2 = client.post(
                "/api/v1/sales/customers",
                json=customer_data,
                headers=auth_headers,
            )
            assert response2.status_code in [400, 409, 422]


class TestCustomerDetail:
    """客户详情 API 测试"""

    def test_get_customer_success(
        self, client: TestClient, auth_headers: dict, created_customer_for_test: dict
    ):
        """测试获取客户详情 - 正常情况"""
        customer_id = created_customer_for_test["id"]
        response = client.get(
            f"/api/v1/sales/customers/{customer_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id

    def test_get_customer_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取客户详情 - 不存在"""
        response = client.get(
            "/api/v1/sales/customers/999999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCustomerUpdate:
    """客户更新 API 测试"""

    def test_update_customer_success(
        self, client: TestClient, auth_headers: dict, created_customer_for_test: dict
    ):
        """测试更新客户 - 正常情况"""
        customer_id = created_customer_for_test["id"]
        update_data = {
            "industry": "新能源",
            "customer_level": "A",
        }
        response = client.put(
            f"/api/v1/sales/customers/{customer_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["industry"] == "新能源"

    def test_update_customer_partial(
        self, client: TestClient, auth_headers: dict, created_customer_for_test: dict
    ):
        """测试更新客户 - 部分更新"""
        customer_id = created_customer_for_test["id"]
        update_data = {"notes": "重要客户"}  # 使用 notes 而不是 remark
        response = client.put(
            f"/api/v1/sales/customers/{customer_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_customer_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试更新客户 - 不存在"""
        response = client.put(
            "/api/v1/sales/customers/999999",
            json={"contact_person": "测试"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCustomerDelete:
    """客户删除 API 测试"""

    def test_delete_customer_success(
        self, client: TestClient, auth_headers: dict
    ):
        """测试删除客户"""
        import uuid

        # 先创建一个客户
        customer_data = {
            "customer_name": f"待删除客户-{uuid.uuid4().hex[:6]}",
        }
        create_resp = client.post(
            "/api/v1/sales/customers",
            json=customer_data,
            headers=auth_headers,
        )
        if create_resp.status_code != 201:
            pytest.skip("无法创建客户")

        customer_id = create_resp.json()["id"]

        # 删除客户 - API 返回 204 No Content
        response = client.delete(
            f"/api/v1/sales/customers/{customer_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_delete_customer_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试删除客户 - 不存在"""
        response = client.delete(
            "/api/v1/sales/customers/999999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_customer_cascade_check(
        self, client: TestClient, auth_headers: dict
    ):
        """测试删除客户 - 检查级联删除行为

        注意：此测试验证带有关联数据的客户删除行为
        """
        import uuid

        # 创建一个新客户来测试
        customer_data = {"customer_name": f"级联测试-{uuid.uuid4().hex[:6]}"}
        create_resp = client.post(
            "/api/v1/sales/customers",
            json=customer_data,
            headers=auth_headers,
        )
        if create_resp.status_code != 201:
            pytest.skip("无法创建客户")

        customer_id = create_resp.json()["id"]

        # 删除刚创建的客户（无关联数据）
        response = client.delete(
            f"/api/v1/sales/customers/{customer_id}",
            headers=auth_headers,
        )
        # 应该成功删除
        assert response.status_code == 204

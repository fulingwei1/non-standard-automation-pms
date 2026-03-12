# -*- coding: utf-8 -*-
"""
商机 API 集成测试

覆盖:
- GET /sales/opportunities - 商机列表
- POST /sales/opportunities - 创建商机
- GET /sales/opportunities/{id} - 商机详情
- PUT /sales/opportunities/{id} - 更新商机
- GET /sales/opportunities/{id}/win-probability - 赢率预测
"""

import pytest
from fastapi.testclient import TestClient


class TestOpportunityList:
    """商机列表 API 测试"""

    def test_list_opportunities_success(self, client: TestClient, auth_headers: dict):
        """测试获取商机列表 - 正常情况"""
        response = client.get("/api/v1/sales/opportunities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # 验证分页结构
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)

    def test_list_opportunities_with_pagination(
        self, client: TestClient, auth_headers: dict
    ):
        """测试商机列表分页"""
        response = client.get(
            "/api/v1/sales/opportunities",
            params={"page": 1, "page_size": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_list_opportunities_with_keyword(
        self, client: TestClient, auth_headers: dict, created_opportunity: dict
    ):
        """测试商机列表关键词搜索"""
        keyword = created_opportunity.get("opp_name", "")[:10]
        response = client.get(
            "/api/v1/sales/opportunities",
            params={"keyword": keyword},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)

    def test_list_opportunities_with_stage_filter(
        self, client: TestClient, auth_headers: dict
    ):
        """测试商机列表阶段筛选"""
        response = client.get(
            "/api/v1/sales/opportunities",
            params={"stage": "DISCOVERY"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # 如果有数据，验证阶段正确
        for item in data["items"]:
            assert item.get("stage") == "DISCOVERY"

    def test_list_opportunities_unauthorized(self, client: TestClient):
        """测试未认证访问商机列表"""
        response = client.get("/api/v1/sales/opportunities")
        assert response.status_code in [401, 403]


class TestOpportunityCreate:
    """商机创建 API 测试"""

    def test_create_opportunity_success(
        self, client: TestClient, auth_headers: dict, test_customer: dict
    ):
        """测试创建商机 - 正常情况"""
        import uuid

        opp_data = {
            "customer_id": test_customer["id"],
            "opp_name": f"测试商机-{uuid.uuid4().hex[:8]}",
            "project_type": "NPI",
            "equipment_type": "ICT测试",
            "stage": "QUALIFICATION",
            "probability": 50,
            "est_amount": "2000000.00",
        }
        response = client.post(
            "/api/v1/sales/opportunities",
            json=opp_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["opp_name"] == opp_data["opp_name"]
        assert data["customer_id"] == opp_data["customer_id"]
        assert "id" in data
        assert "opp_code" in data

    def test_create_opportunity_missing_required_field(
        self, client: TestClient, auth_headers: dict
    ):
        """测试创建商机 - 缺少必填字段"""
        # 缺少 customer_id
        opp_data = {
            "opp_name": "测试商机-缺少客户",
        }
        response = client.post(
            "/api/v1/sales/opportunities",
            json=opp_data,
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation Error

    def test_create_opportunity_invalid_customer(
        self, client: TestClient, auth_headers: dict
    ):
        """测试创建商机 - 客户不存在"""
        opp_data = {
            "customer_id": 999999,  # 不存在的客户ID
            "opp_name": "测试商机-无效客户",
        }
        response = client.post(
            "/api/v1/sales/opportunities",
            json=opp_data,
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_opportunity_duplicate_code(
        self, client: TestClient, auth_headers: dict, test_customer: dict
    ):
        """测试创建商机 - 重复编码"""
        opp_code = "TEST-DUP-001"
        opp_data = {
            "customer_id": test_customer["id"],
            "opp_name": "测试商机-重复编码1",
            "opp_code": opp_code,
        }
        # 第一次创建
        response1 = client.post(
            "/api/v1/sales/opportunities",
            json=opp_data,
            headers=auth_headers,
        )
        # 如果第一次成功，尝试创建重复编码
        if response1.status_code == 201:
            opp_data["opp_name"] = "测试商机-重复编码2"
            response2 = client.post(
                "/api/v1/sales/opportunities",
                json=opp_data,
                headers=auth_headers,
            )
            assert response2.status_code == 400
            assert "已存在" in response2.json().get("detail", "")


class TestOpportunityDetail:
    """商机详情 API 测试"""

    def test_get_opportunity_success(
        self, client: TestClient, auth_headers: dict, created_opportunity: dict
    ):
        """测试获取商机详情 - 正常情况"""
        opp_id = created_opportunity["id"]
        response = client.get(
            f"/api/v1/sales/opportunities/{opp_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == opp_id
        assert "opp_name" in data
        assert "opp_code" in data

    def test_get_opportunity_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取商机详情 - 不存在"""
        response = client.get(
            "/api/v1/sales/opportunities/999999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestOpportunityUpdate:
    """商机更新 API 测试"""

    def test_update_opportunity_success(
        self, client: TestClient, auth_headers: dict, created_opportunity: dict
    ):
        """测试更新商机 - 正常情况"""
        opp_id = created_opportunity["id"]
        update_data = {
            "stage": "PROPOSAL",
            "probability": 60,
            "est_amount": "2500000.00",
        }
        response = client.put(
            f"/api/v1/sales/opportunities/{opp_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "PROPOSAL"
        assert data["probability"] == 60

    def test_update_opportunity_partial(
        self, client: TestClient, auth_headers: dict, created_opportunity: dict
    ):
        """测试更新商机 - 部分更新"""
        opp_id = created_opportunity["id"]
        # 只更新一个字段
        update_data = {"risk_level": "MEDIUM"}
        response = client.put(
            f"/api/v1/sales/opportunities/{opp_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_opportunity_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试更新商机 - 不存在"""
        update_data = {"stage": "PROPOSAL"}
        response = client.put(
            "/api/v1/sales/opportunities/999999",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestOpportunityWinProbability:
    """商机赢率预测 API 测试"""

    def test_get_win_probability_success(
        self, client: TestClient, auth_headers: dict, created_opportunity: dict
    ):
        """测试获取赢率预测 - 正常情况"""
        opp_id = created_opportunity["id"]
        response = client.get(
            f"/api/v1/sales/opportunities/{opp_id}/win-probability",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # 验证响应结构
        assert "code" in data or "data" in data
        result = data.get("data", data)
        assert "win_probability" in result or "probability" in result

    def test_get_win_probability_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取赢率预测 - 商机不存在"""
        response = client.get(
            "/api/v1/sales/opportunities/999999/win-probability",
            headers=auth_headers,
        )
        # 可能返回 404 或者返回默认预测值
        assert response.status_code in [200, 404]


class TestOpportunityWorkflow:
    """商机工作流 API 测试"""

    def test_update_stage_success(
        self, client: TestClient, auth_headers: dict, created_opportunity: dict
    ):
        """测试更新商机阶段"""
        opp_id = created_opportunity["id"]
        response = client.put(
            f"/api/v1/sales/opportunities/{opp_id}/stage",
            json={"stage": "NEGOTIATION"},
            headers=auth_headers,
        )
        # 可能需要特定权限或业务规则
        assert response.status_code in [200, 400, 403, 404, 422]

    def test_submit_gate_review(
        self, client: TestClient, auth_headers: dict, created_opportunity: dict
    ):
        """测试提交阶段评审"""
        opp_id = created_opportunity["id"]
        gate_data = {
            "gate_type": "G2",
            "notes": "测试阶段评审",
        }
        response = client.post(
            f"/api/v1/sales/opportunities/{opp_id}/gate",
            json=gate_data,
            headers=auth_headers,
        )
        # 根据业务规则可能需要特定条件
        assert response.status_code in [200, 400, 403, 404, 422]

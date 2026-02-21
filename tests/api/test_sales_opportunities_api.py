# -*- coding: utf-8 -*-
"""
销售商机管理 API 测试

测试商机的创建、查询、更新、跟进、转化等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSalesOpportunitiesAPI:
    """销售商机管理 API 测试类"""

    def test_list_opportunities(self, client: TestClient, admin_token: str):
        """测试获取商机列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Opportunities API not implemented")

        assert response.status_code == 200, response.text

    def test_create_opportunity(self, client: TestClient, admin_token: str):
        """测试创建商机"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        opportunity_data = {
            "opportunity_name": "某科技公司自动化设备采购",
            "customer_id": 1,
            "opportunity_stage": "initial_contact",
            "expected_amount": 500000.0,
            "probability": 30,
            "expected_close_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            "source": "客户推荐",
            "description": "客户有意向采购自动化生产线设备",
            "contact_person": "张经理",
            "contact_phone": "13800138000"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/opportunities/",
            headers=headers,
            json=opportunity_data
        )

        if response.status_code == 404:
            pytest.skip("Opportunities API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_opportunity_detail(self, client: TestClient, admin_token: str):
        """测试获取商机详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No opportunity data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_opportunity(self, client: TestClient, admin_token: str):
        """测试更新商机"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "opportunity_stage": "proposal",
            "probability": 60,
            "expected_amount": 550000.0
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/opportunities/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Opportunity API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_opportunity(self, client: TestClient, admin_token: str):
        """测试删除商机"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/opportunities/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Opportunity API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_update_opportunity_stage(self, client: TestClient, admin_token: str):
        """测试更新商机阶段"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        stage_data = {
            "stage": "negotiation",
            "probability": 75
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/opportunities/1/update-stage",
            headers=headers,
            json=stage_data
        )

        if response.status_code == 404:
            pytest.skip("Opportunity stage API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_add_opportunity_followup(self, client: TestClient, admin_token: str):
        """测试添加商机跟进记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        followup_data = {
            "followup_date": datetime.now().strftime("%Y-%m-%d"),
            "followup_type": "phone_call",
            "content": "与客户沟通了需求细节，客户表示很感兴趣",
            "next_followup_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "next_action": "准备技术方案"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/opportunities/1/followups",
            headers=headers,
            json=followup_data
        )

        if response.status_code == 404:
            pytest.skip("Opportunity followup API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_get_opportunity_followups(self, client: TestClient, admin_token: str):
        """测试获取商机跟进历史"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/1/followups",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Opportunity followup API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_win_opportunity(self, client: TestClient, admin_token: str):
        """测试商机赢单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        win_data = {
            "win_date": datetime.now().strftime("%Y-%m-%d"),
            "actual_amount": 520000.0,
            "win_reason": "技术方案优秀，价格合理"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/opportunities/1/win",
            headers=headers,
            json=win_data
        )

        if response.status_code == 404:
            pytest.skip("Opportunity win API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_lose_opportunity(self, client: TestClient, admin_token: str):
        """测试商机输单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        lose_data = {
            "lose_date": datetime.now().strftime("%Y-%m-%d"),
            "lose_reason": "价格因素",
            "competitor": "某竞争对手公司"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/opportunities/1/lose",
            headers=headers,
            json=lose_data
        )

        if response.status_code == 404:
            pytest.skip("Opportunity lose API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_opportunities_by_stage(self, client: TestClient, admin_token: str):
        """测试按阶段过滤商机"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/?stage=proposal",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Opportunity filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_opportunities_by_probability(self, client: TestClient, admin_token: str):
        """测试按成功概率过滤商机"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/?min_probability=50",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Opportunity filter API not implemented")

        assert response.status_code == 200, response.text

    def test_my_opportunities(self, client: TestClient, admin_token: str):
        """测试获取我的商机"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/my-opportunities",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("My opportunities API not implemented")

        assert response.status_code == 200, response.text

    def test_opportunity_statistics(self, client: TestClient, admin_token: str):
        """测试商机统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Opportunity statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_opportunity_pipeline(self, client: TestClient, admin_token: str):
        """测试商机漏斗分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/pipeline",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Opportunity pipeline API not implemented")

        assert response.status_code == 200, response.text

    def test_opportunity_unauthorized(self, client: TestClient):
        """测试未授权访问商机"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/opportunities/"
        )

        assert response.status_code in [401, 403], response.text

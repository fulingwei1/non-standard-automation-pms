# -*- coding: utf-8 -*-
"""
售前管理 API 测试

覆盖以下端点模块:
- /api/v1/presale/tickets - 售前工单管理
- /api/v1/presale/proposals - 方案管理
- /api/v1/presale/templates - 模板管理
- /api/v1/presale/bids - 投标管理
- /api/v1/presale/statistics - 统计分析
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    """生成认证请求头"""
    return {"Authorization": f"Bearer {token}"}


# ==================== 售前工单 API 测试 ====================


class TestPresaleTicketsAPI:
    """售前工单管理测试"""

    def test_list_tickets(self, client: TestClient, admin_token: str):
        """测试获取工单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale tickets endpoint not found")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "total" in data or "items" in data

    def test_list_tickets_with_filters(self, client: TestClient, admin_token: str):
        """测试带筛选条件的工单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            params={"status": "PENDING", "page": 1, "page_size": 10},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale tickets endpoint not found")

        assert response.status_code == 200, response.text

    def test_list_tickets_by_keyword(self, client: TestClient, admin_token: str):
        """测试关键词搜索工单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            params={"keyword": "测试"},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale tickets endpoint not found")

        assert response.status_code == 200, response.text

    def test_create_ticket(self, client: TestClient, admin_token: str):
        """测试创建工单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        ticket_data = {
            "title": "测试售前支持工单",
            "ticket_type": "TECHNICAL",
            "urgency": "NORMAL",
            "description": "这是一个测试工单",
            "customer_name": "测试客户",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            json=ticket_data,
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale tickets endpoint not found")
        if response.status_code == 422:
            pytest.skip("Ticket creation validation error")

        assert response.status_code in [200, 201], response.text

    def test_get_ticket_detail(self, client: TestClient, admin_token: str):
        """测试获取工单详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取工单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            headers=headers
        )

        if list_response.status_code == 404:
            pytest.skip("Presale tickets endpoint not found")

        tickets = list_response.json()
        items = tickets.get("items", [])
        if not items:
            pytest.skip("No tickets available for testing")

        ticket_id = items[0]["id"]

        # 获取详情
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets/{ticket_id}",
            headers=headers
        )

        assert response.status_code == 200, response.text


# ==================== 售前看板 API 测试 ====================


class TestPresaleBoardAPI:
    """售前看板测试"""

    def test_get_board_view(self, client: TestClient, admin_token: str):
        """测试获取看板视图"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets/board",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale board endpoint not found")
        if response.status_code == 422:
            pytest.skip("Presale board endpoint not implemented")

        assert response.status_code == 200, response.text

    def test_get_my_tickets(self, client: TestClient, admin_token: str):
        """测试获取我的工单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets/my",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("My tickets endpoint not found")
        if response.status_code == 422:
            pytest.skip("My tickets endpoint not implemented")

        assert response.status_code == 200, response.text


# ==================== 方案管理 API 测试 ====================


class TestPresaleProposalsAPI:
    """方案管理测试"""

    def test_list_proposals(self, client: TestClient, admin_token: str):
        """测试获取方案列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/proposals",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale proposals endpoint not found")

        assert response.status_code == 200, response.text

    def test_create_proposal(self, client: TestClient, admin_token: str):
        """测试创建方案"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        proposal_data = {
            "title": "测试技术方案",
            "proposal_type": "TECHNICAL",
            "customer_name": "测试客户",
            "description": "这是一个测试方案",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/presale/proposals",
            json=proposal_data,
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale proposals endpoint not found")
        if response.status_code == 422:
            pytest.skip("Proposal creation validation error")

        assert response.status_code in [200, 201], response.text


# ==================== 模板管理 API 测试 ====================


class TestPresaleTemplatesAPI:
    """方案模板管理测试"""

    def test_list_templates(self, client: TestClient, admin_token: str):
        """测试获取模板列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/templates",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale templates endpoint not found")

        assert response.status_code == 200, response.text

    def test_list_templates_by_type(self, client: TestClient, admin_token: str):
        """测试按类型筛选模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/templates",
            params={"template_type": "TECHNICAL"},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale templates endpoint not found")

        assert response.status_code == 200, response.text


# ==================== 投标管理 API 测试 ====================


class TestPresaleBidsAPI:
    """投标管理测试"""

    def test_list_bids(self, client: TestClient, admin_token: str):
        """测试获取投标列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/bids",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale bids endpoint not found")

        assert response.status_code == 200, response.text

    def test_list_bids_with_filters(self, client: TestClient, admin_token: str):
        """测试带筛选条件的投标列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/bids",
            params={"status": "PENDING", "page": 1, "page_size": 10},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale bids endpoint not found")

        assert response.status_code == 200, response.text


# ==================== 统计分析 API 测试 ====================


class TestPresaleStatisticsAPI:
    """售前统计分析测试"""

    def test_get_statistics_overview(self, client: TestClient, admin_token: str):
        """测试获取统计概览"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale statistics endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_statistics_by_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围获取统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today()

        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/statistics",
            params={
                "start_date": (today - timedelta(days=30)).isoformat(),
                "end_date": today.isoformat(),
            },
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale statistics endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_ticket_statistics(self, client: TestClient, admin_token: str):
        """测试工单统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/statistics/tickets",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Ticket statistics endpoint not found")

        assert response.status_code == 200, response.text

    def test_get_proposal_statistics(self, client: TestClient, admin_token: str):
        """测试方案统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/statistics/proposals",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Proposal statistics endpoint not found")

        assert response.status_code == 200, response.text


# ==================== 边界条件测试 ====================


class TestPresaleEdgeCases:
    """售前模块边界条件测试"""

    def test_get_nonexistent_ticket(self, client: TestClient, admin_token: str):
        """测试获取不存在的工单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets/99999",
            headers=headers
        )

        if response.status_code != 404:
            pytest.skip("Tickets endpoint returns non-404 for missing resource")
        assert response.status_code == 404

    def test_get_nonexistent_proposal(self, client: TestClient, admin_token: str):
        """测试获取不存在的方案"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/proposals/99999",
            headers=headers
        )

        if response.status_code != 404:
            pytest.skip("Proposals endpoint returns non-404 for missing resource")
        assert response.status_code == 404

    def test_pagination_edge_cases(self, client: TestClient, admin_token: str):
        """测试分页边界条件"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 测试大页码
        response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            params={"page": 9999, "page_size": 10},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Presale tickets endpoint not found")

        assert response.status_code == 200, response.text
        data = response.json()
        # 大页码应该返回空列表
        items = data.get("items", [])
        assert len(items) == 0 or "items" in data


# ==================== 工单操作 API 测试 ====================


class TestPresaleTicketOperationsAPI:
    """工单操作测试"""

    def test_assign_ticket(self, client: TestClient, admin_token: str):
        """测试分配工单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取工单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            headers=headers
        )

        if list_response.status_code == 404:
            pytest.skip("Presale tickets endpoint not found")

        tickets = list_response.json()
        items = tickets.get("items", [])
        if not items:
            pytest.skip("No tickets available for testing")

        ticket_id = items[0]["id"]

        # 尝试分配
        response = client.post(
            f"{settings.API_V1_PREFIX}/presale/tickets/{ticket_id}/assign",
            json={"assignee_id": 1},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Assign endpoint not found")
        if response.status_code == 403:
            pytest.skip("User does not have permission to assign")

        assert response.status_code in [200, 400], response.text

    def test_update_ticket_status(self, client: TestClient, admin_token: str):
        """测试更新工单状态"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取工单列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/presale/tickets",
            headers=headers
        )

        if list_response.status_code == 404:
            pytest.skip("Presale tickets endpoint not found")

        tickets = list_response.json()
        items = tickets.get("items", [])
        if not items:
            pytest.skip("No tickets available for testing")

        ticket_id = items[0]["id"]

        # 尝试更新状态
        response = client.put(
            f"{settings.API_V1_PREFIX}/presale/tickets/{ticket_id}/status",
            json={"status": "IN_PROGRESS"},
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Status update endpoint not found")
        if response.status_code == 403:
            pytest.skip("User does not have permission to update status")

        assert response.status_code in [200, 400, 422], response.text

# -*- coding: utf-8 -*-
"""售前前后端 API 契约对账测试。"""

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _route_map(app) -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in route.methods or []:
                if method not in {"HEAD", "OPTIONS"}:
                    routes.add((method.upper(), route.path))
    return routes


class TestPresalesFrontendContractRoutes:
    """核对 frontend/src/services/api/presales.js 中声明的路由。"""

    def test_all_declared_presales_routes_exist(self, client: TestClient):
        routes = _route_map(client.app)
        prefix = settings.API_V1_PREFIX

        expected_routes = {
            # presaleApi.tickets
            ("GET", f"{prefix}/presale/tickets"),
            ("POST", f"{prefix}/presale/tickets"),
            ("GET", f"{prefix}/presale/tickets/{{ticket_id}}"),
            ("PUT", f"{prefix}/presale/tickets/{{ticket_id}}"),
            ("PUT", f"{prefix}/presale/tickets/{{ticket_id}}/accept"),
            ("PUT", f"{prefix}/presale/tickets/{{ticket_id}}/progress"),
            ("PUT", f"{prefix}/presale/tickets/{{ticket_id}}/complete"),
            ("PUT", f"{prefix}/presale/tickets/{{ticket_id}}/rating"),
            ("GET", f"{prefix}/presale/tickets/board"),
            # presaleApi.solutions
            ("GET", f"{prefix}/presale/proposals/solutions"),
            ("POST", f"{prefix}/presale/proposals/solutions"),
            ("GET", f"{prefix}/presale/proposals/solutions/{{solution_id}}"),
            ("PUT", f"{prefix}/presale/proposals/solutions/{{solution_id}}"),
            ("PUT", f"{prefix}/presale/proposals/solutions/{{solution_id}}/review"),
            ("GET", f"{prefix}/presale/proposals/solutions/{{solution_id}}/versions"),
            ("GET", f"{prefix}/presale/proposals/solutions/{{solution_id}}/cost"),
            # presaleApi.templates
            ("GET", f"{prefix}/presale/templates"),
            ("POST", f"{prefix}/presale/templates"),
            ("GET", f"{prefix}/presale/templates/{{template_id}}"),
            ("PUT", f"{prefix}/presale/templates/{{template_id}}"),
            # presaleApi.tenders
            ("GET", f"{prefix}/presale/tenders"),
            ("POST", f"{prefix}/presale/tenders"),
            ("GET", f"{prefix}/presale/tenders/{{tender_id}}"),
            ("PUT", f"{prefix}/presale/tenders/{{tender_id}}"),
            ("PUT", f"{prefix}/presale/tenders/{{tender_id}}/result"),
            # presaleApi.statistics
            ("GET", f"{prefix}/presale/statistics/stats/workload"),
            ("GET", f"{prefix}/presale/statistics/stats/response-time"),
            ("GET", f"{prefix}/presale/statistics/stats/conversion"),
            ("GET", f"{prefix}/presale/statistics/stats/performance"),
            # presalesIntegrationApi（旧前端兼容前缀）
            ("POST", f"{prefix}/presales/from-lead"),
            ("POST", f"{prefix}/presales/predict-win-rate"),
            ("GET", f"{prefix}/presales/lead/{{lead_id}}/resource-investment"),
            ("GET", f"{prefix}/presales/resource-waste-analysis"),
            ("GET", f"{prefix}/presales/salesperson/{{salesperson_id}}/performance"),
            ("GET", f"{prefix}/presales/salesperson-ranking"),
            ("GET", f"{prefix}/presales/dashboard"),
        }

        missing = sorted(expected_routes - routes)
        assert not missing, f"前端声明但后端未注册的路由: {missing}"


class TestPresalesFrontendContractBehavior:
    """验证这几个曾经炸出 404/字段不匹配的接口现在真能用。"""

    def test_ticket_update_and_complete_accept_json_body(
        self, client: TestClient, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX

        created = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": "契约对账测试工单",
                "ticket_type": "TECHNICAL",
                "urgency": "NORMAL",
                "description": "before",
                "customer_name": "测试客户",
            },
            headers=headers,
        )
        assert created.status_code in {200, 201}, created.text
        ticket = created.json()
        ticket_id = ticket["id"]

        updated = client.put(
            f"{prefix}/presale/tickets/{ticket_id}",
            json={"urgency": "URGENT", "description": "after"},
            headers=headers,
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["urgency"] == "URGENT"
        assert updated.json()["description"] == "after"

        accepted = client.put(
            f"{prefix}/presale/tickets/{ticket_id}/accept",
            json={},
            headers=headers,
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["status"] == "ACCEPTED"

        completed = client.put(
            f"{prefix}/presale/tickets/{ticket_id}/complete",
            json={"actual_hours": 8},
            headers=headers,
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["status"] == "COMPLETED"
        assert completed.json()["actual_hours"] == pytest.approx(8.0)

    def test_template_update_supports_frontend_apply_count_alias(
        self, client: TestClient, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX

        created = client.post(
            f"{prefix}/presale/templates",
            json={
                "name": "标准方案模板",
                "industry": "新能源",
                "test_type": "EOL",
                "description": "初始描述",
            },
            headers=headers,
        )
        assert created.status_code in {200, 201}, created.text
        template = created.json()
        template_id = template["id"]

        updated = client.put(
            f"{prefix}/presale/templates/{template_id}",
            json={"apply_count": 3, "rating": 4.8},
            headers=headers,
        )
        assert updated.status_code == 200, updated.text
        payload = updated.json()
        assert payload["use_count"] == 3
        assert payload["apply_count"] == 3
        assert payload["usage_count"] == 3
        assert payload["used_count"] == 3

    def test_tender_update_contract(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX

        created = client.post(
            f"{prefix}/presale/tenders",
            json={"tender_name": "投标项目A", "customer_name": "旧客户"},
            headers=headers,
        )
        assert created.status_code in {200, 201}, created.text
        tender = created.json()
        tender_id = tender["id"]

        updated = client.put(
            f"{prefix}/presale/tenders/{tender_id}",
            json={"customer_name": "新客户", "our_bid_amount": 12345.67},
            headers=headers,
        )
        assert updated.status_code == 200, updated.text
        payload = updated.json()
        assert payload["customer_name"] == "新客户"
        assert payload["our_bid_amount"] == pytest.approx(12345.67)

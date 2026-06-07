# -*- coding: utf-8 -*-
"""售前前后端 API 契约对账测试。"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


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
            ("POST", f"{prefix}/presale/tickets/{{ticket_id}}/deliverables"),
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
            # technicalParameterApi
            ("GET", f"{prefix}/presale/technical-parameters/templates"),
            ("POST", f"{prefix}/presale/technical-parameters/templates"),
            ("GET", f"{prefix}/presale/technical-parameters/templates/match"),
            ("GET", f"{prefix}/presale/technical-parameters/templates/{{template_id}}"),
            ("PUT", f"{prefix}/presale/technical-parameters/templates/{{template_id}}"),
            ("DELETE", f"{prefix}/presale/technical-parameters/templates/{{template_id}}"),
            ("POST", f"{prefix}/presale/technical-parameters/estimate-cost"),
            ("POST", f"{prefix}/presale/technical-parameters/batch-estimate-cost"),
            ("GET", f"{prefix}/presale/technical-parameters/statistics"),
            ("GET", f"{prefix}/presale/technical-parameters/statistics/industries"),
            ("GET", f"{prefix}/presale/technical-parameters/statistics/test-types"),
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

        progressed = client.put(
            f"{prefix}/presale/tickets/{ticket_id}/progress",
            json={"progress_note": "方案边界已澄清", "progress_percent": 60},
            headers=headers,
        )
        assert progressed.status_code == 200, progressed.text
        assert progressed.json()["status"] == "IN_PROGRESS"
        assert progressed.json()["progress_percent"] == 60
        assert progressed.json()["progress_note"] == "方案边界已澄清"

        deliverable = client.post(
            f"{prefix}/presale/tickets/{ticket_id}/deliverables",
            json={
                "deliverable_name": "初版技术方案",
                "deliverable_type": "SOLUTION",
                "file_path": "/files/solution-v1.pdf",
                "file_url": "https://files.example.com/solution-v1.pdf",
                "description": "方案初稿",
            },
            headers=headers,
        )
        assert deliverable.status_code == 201, deliverable.text
        deliverable_payload = deliverable.json()
        assert deliverable_payload["ticket_id"] == ticket_id
        assert deliverable_payload["deliverable_name"] == "初版技术方案"
        assert deliverable_payload["deliverable_type"] == "SOLUTION"
        assert deliverable_payload["file_path"] == "/files/solution-v1.pdf"
        assert deliverable_payload["file_url"] == "https://files.example.com/solution-v1.pdf"
        assert deliverable_payload["description"] == "方案初稿"

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

    def test_technical_parameter_routes_match_frontend_contract(
        self, client: TestClient, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX

        created = client.post(
            f"{prefix}/presale/technical-parameters/templates",
            json={
                "name": "FCT 标准测试模板",
                "code": "FCT-CONTRACT-001",
                "industry": "CONSUMER",
                "test_type": "FCT",
                "description": "用于前后端契约对账",
                "parameters": {
                    "test_station_count": {
                        "label": "测试工位数",
                        "type": "number",
                        "default": 4,
                        "unit": "个",
                    }
                },
                "cost_factors": {
                    "base_cost": 50000,
                    "factors": {
                        "test_station_count": {
                            "type": "linear",
                            "coefficient": 8000,
                        }
                    },
                    "category_ratios": {
                        "MECHANICAL": 0.35,
                        "ELECTRICAL": 0.30,
                        "SOFTWARE": 0.20,
                        "LABOR": 0.15,
                    },
                },
                "typical_labor_hours": {
                    "design_hours": 80,
                    "assembly_hours": 120,
                },
            },
            headers=headers,
        )
        assert created.status_code in {200, 201}, created.text
        template = created.json()
        template_id = template["id"]

        listed = client.get(
            f"{prefix}/presale/technical-parameters/templates",
            params={"industry": "CONSUMER", "test_type": "FCT"},
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert any(item["id"] == template_id for item in listed.json()["items"])

        matched = client.get(
            f"{prefix}/presale/technical-parameters/templates/match",
            params={"industry": "CONSUMER", "test_type": "FCT"},
            headers=headers,
        )
        assert matched.status_code == 200, matched.text
        assert any(item["id"] == template_id for item in matched.json())

        estimated = client.post(
            f"{prefix}/presale/technical-parameters/estimate-cost",
            json={"template_id": template_id, "parameters": {"test_station_count": 4}},
            headers=headers,
        )
        assert estimated.status_code == 200, estimated.text
        assert estimated.json()["total_cost"] == pytest.approx(82000.0)

        stats = client.get(
            f"{prefix}/presale/technical-parameters/statistics",
            headers=headers,
        )
        assert stats.status_code == 200, stats.text
        assert "industries" in stats.json()
        assert "test_types" in stats.json()

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

    def test_presales_compat_analytics_use_timesheets(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8]
        source_lead_id = f"XS26{unique[:6].upper()}"
        project_code = f"PJ26{unique[:6].upper()}"

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        project = Project(
            project_code=project_code,
            project_name="售前工时契约项目",
            customer_name="契约测试客户",
            contract_amount=Decimal("120000"),
            source_lead_id=source_lead_id,
            outcome=LeadOutcomeEnum.LOST.value,
            loss_reason="PRICE",
            salesperson_id=admin_user.id,
            is_active=True,
        )
        db_session.add(project)
        db_session.flush()

        timesheet = Timesheet(
            user_id=admin_user.id,
            user_name=admin_user.real_name or admin_user.username,
            project_id=project.id,
            project_code=project.project_code,
            project_name=project.project_name,
            work_date=date.today(),
            hours=Decimal("6.50"),
            status="APPROVED",
        )
        db_session.add(timesheet)
        db_session.commit()

        try:
            dashboard = client.get(f"{prefix}/presales/dashboard", headers=headers)
            assert dashboard.status_code == 200, dashboard.text
            dashboard_data = dashboard.json()["data"]
            assert dashboard_data["total_wasted_hours"] >= 6.5

            investment = client.get(
                f"{prefix}/presales/lead/{source_lead_id}/resource-investment",
                headers=headers,
            )
            assert investment.status_code == 200, investment.text
            investment_data = investment.json()["data"]
            assert investment_data["lead_name"] == "售前工时契约项目"
            assert investment_data["total_hours"] == pytest.approx(6.5)
            assert investment_data["engineer_count"] == 1

            waste = client.get(
                f"{prefix}/presales/resource-waste-analysis",
                params={"period": str(date.today().year)},
                headers=headers,
            )
            assert waste.status_code == 200, waste.text
            waste_data = waste.json()["data"]
            assert waste_data["total_investment_hours"] >= 6.5
            assert waste_data["wasted_hours"] >= 6.5

            performance = client.get(
                f"{prefix}/presales/salesperson/{admin_user.id}/performance",
                headers=headers,
            )
            assert performance.status_code == 200, performance.text
            performance_data = performance.json()["data"]
            assert performance_data["total_resource_hours"] >= 6.5
            assert performance_data["wasted_hours"] >= 6.5
        finally:
            db_session.query(Timesheet).filter(Timesheet.project_id == project.id).delete()
            db_session.query(Project).filter(Project.id == project.id).delete()
            db_session.commit()

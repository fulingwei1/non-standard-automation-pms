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
from app.models.enums import AssessmentStatusEnum, LeadOutcomeEnum
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Customer, Machine, Project
from app.models.sales import Opportunity
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

    def test_completing_opportunity_ticket_updates_sales_assessment_status(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8]

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PS-{unique}",
            customer_name=f"售前闭环客户-{unique}",
            industry="电子制造",
            contact_person="王工",
            contact_phone="021-88888888",
            created_by=admin_user.id,
        )
        db_session.add(customer)
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPP{unique[:6].upper()}",
            customer_id=customer.id,
            opp_name=f"售前闭环商机-{unique}",
            stage="QUALIFICATION",
            probability=60,
            owner_id=admin_user.id,
            updated_by=admin_user.id,
            assessment_status=AssessmentStatusEnum.PENDING.value,
            requirement_maturity=2,
        )
        db_session.add(opportunity)
        db_session.commit()

        created = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": "商机技术方案支持",
                "ticket_type": "TECHNICAL_EXCHANGE",
                "urgency": "NORMAL",
                "description": "完成后应反写商机技术评估状态",
                "customer_id": customer.id,
                "customer_name": customer.customer_name,
                "opportunity_id": opportunity.id,
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        ticket_id = created.json()["id"]

        completed = client.put(
            f"{prefix}/presale/tickets/{ticket_id}/complete",
            json={"actual_hours": 6.5},
            headers=headers,
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["status"] == "COMPLETED"

        refreshed = client.get(
            f"{prefix}/sales/opportunities/{opportunity.id}",
            headers=headers,
        )
        assert refreshed.status_code == 200, refreshed.text
        assert refreshed.json()["assessment_status"] == AssessmentStatusEnum.COMPLETED.value

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

        updated = client.put(
            f"{prefix}/presale/technical-parameters/templates/{template_id}",
            json={
                "name": "FCT 标准测试模板-编辑后",
                "industry": "AUTOMOTIVE",
                "test_type": "EOL",
                "description": "前端编辑表单会提交完整分类字段",
            },
            headers=headers,
        )
        assert updated.status_code == 200, updated.text
        updated_payload = updated.json()
        assert updated_payload["name"] == "FCT 标准测试模板-编辑后"
        assert updated_payload["industry"] == "AUTOMOTIVE"
        assert updated_payload["test_type"] == "EOL"
        assert updated_payload["description"] == "前端编辑表单会提交完整分类字段"

        listed = client.get(
            f"{prefix}/presale/technical-parameters/templates",
            params={"industry": "AUTOMOTIVE", "test_type": "EOL"},
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert any(item["id"] == template_id for item in listed.json()["items"])

        matched = client.get(
            f"{prefix}/presale/technical-parameters/templates/match",
            params={"industry": "AUTOMOTIVE", "test_type": "EOL"},
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

    def test_solution_list_filters_by_opportunity_and_project(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        project_a = Project(
            project_code=f"PSFA{unique[:6]}",
            project_name=f"方案过滤项目A-{unique}",
            customer_name=f"方案过滤客户A-{unique}",
            is_active=True,
        )
        project_b = Project(
            project_code=f"PSFB{unique[:6]}",
            project_name=f"方案过滤项目B-{unique}",
            customer_name=f"方案过滤客户B-{unique}",
            is_active=True,
        )
        db_session.add_all([project_a, project_b])
        db_session.flush()

        target_solution = PresaleSolution(
            solution_no=f"SOL-OPP-{unique}",
            name=f"目标商机方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=None,
            project_id=project_a.id,
            opportunity_id=9001,
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        other_solution = PresaleSolution(
            solution_no=f"SOL-OTHER-{unique}",
            name=f"其他项目方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=None,
            project_id=project_b.id,
            opportunity_id=9002,
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add_all([target_solution, other_solution])
        db_session.commit()

        try:
            by_opportunity = client.get(
                f"{prefix}/presale/proposals/solutions",
                params={"opportunity_id": 9001},
                headers=headers,
            )
            assert by_opportunity.status_code == 200, by_opportunity.text
            opportunity_items = by_opportunity.json()["items"]
            assert [item["id"] for item in opportunity_items] == [target_solution.id]
            assert opportunity_items[0]["opportunity_id"] == 9001

            by_project = client.get(
                f"{prefix}/presale/proposals/solutions",
                params={"project_id": project_b.id},
                headers=headers,
            )
            assert by_project.status_code == 200, by_project.text
            project_items = by_project.json()["items"]
            assert [item["id"] for item in project_items] == [other_solution.id]
            assert project_items[0]["project_id"] == project_b.id
        finally:
            db_session.query(PresaleSolution).filter(
                PresaleSolution.solution_no.in_(
                    [f"SOL-OPP-{unique}", f"SOL-OTHER-{unique}"]
                )
            ).delete(synchronize_session=False)
            db_session.query(Project).filter(
                Project.project_code.in_([f"PSFA{unique[:6]}", f"PSFB{unique[:6]}"])
            ).delete(synchronize_session=False)
            db_session.commit()

    def test_solution_created_from_ticket_inherits_project_context(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PST-{unique}",
            customer_name=f"方案继承客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        db_session.add(customer)
        db_session.flush()

        project = Project(
            project_code=f"PST{unique[:6]}",
            project_name=f"方案继承项目-{unique}",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            is_active=True,
        )
        db_session.add(project)
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPPT{unique[:6]}",
            customer_id=customer.id,
            opp_name=f"方案继承商机-{unique}",
            stage="QUALIFICATION",
            probability=60,
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add(opportunity)
        db_session.commit()

        created_ticket = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": f"方案继承工单-{unique}",
                "ticket_type": "SOLUTION",
                "urgency": "NORMAL",
                "customer_id": customer.id,
                "customer_name": customer.customer_name,
                "opportunity_id": opportunity.id,
                "project_id": project.id,
            },
            headers=headers,
        )
        assert created_ticket.status_code == 201, created_ticket.text
        ticket_id = created_ticket.json()["id"]

        created_solution = client.post(
            f"{prefix}/presale/proposals/solutions",
            json={
                "name": f"方案继承测试-{unique}",
                "solution_type": "CUSTOM",
                "ticket_id": ticket_id,
            },
            headers=headers,
        )
        assert created_solution.status_code == 201, created_solution.text
        solution = created_solution.json()

        try:
            assert solution["ticket_id"] == ticket_id
            assert solution["project_id"] == project.id
            assert solution["opportunity_id"] == opportunity.id
            assert solution["customer_id"] == customer.id

            by_project = client.get(
                f"{prefix}/presale/proposals/solutions",
                params={"project_id": project.id},
                headers=headers,
            )
            assert by_project.status_code == 200, by_project.text
            assert any(item["id"] == solution["id"] for item in by_project.json()["items"])

            by_opportunity = client.get(
                f"{prefix}/presale/proposals/solutions",
                params={"opportunity_id": opportunity.id},
                headers=headers,
            )
            assert by_opportunity.status_code == 200, by_opportunity.text
            assert any(item["id"] == solution["id"] for item in by_opportunity.json()["items"])
        finally:
            db_session.query(PresaleSolution).filter(
                PresaleSolution.id == solution["id"]
            ).delete(synchronize_session=False)
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket_id
            ).delete(synchronize_session=False)
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete()
            db_session.query(Project).filter(Project.id == project.id).delete()
            db_session.query(Customer).filter(Customer.id == customer.id).delete()
            db_session.commit()

    def test_solution_submit_review_moves_out_of_draft(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        created = client.post(
            f"{prefix}/presale/proposals/solutions",
            json={
                "name": f"提交审核方案-{unique}",
                "solution_type": "CUSTOM",
                "requirement_summary": "用于验证方案审核状态流",
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        solution_id = created.json()["id"]

        try:
            submitted = client.put(
                f"{prefix}/presale/proposals/solutions/{solution_id}/review",
                json={"review_status": "REVIEW", "review_comment": "提交审核"},
                headers=headers,
            )
            assert submitted.status_code == 200, submitted.text
            submitted_payload = submitted.json()
            assert submitted_payload["review_status"] == "REVIEW"
            assert submitted_payload["status"] == "REVIEW"

            update_after_submit = client.put(
                f"{prefix}/presale/proposals/solutions/{solution_id}",
                json={"requirement_summary": "审核中不应继续按草稿修改"},
                headers=headers,
            )
            assert update_after_submit.status_code == 400, update_after_submit.text
        finally:
            db_session.query(PresaleSolution).filter(PresaleSolution.id == solution_id).delete(
                synchronize_session=False
            )
            db_session.commit()

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

    def test_presales_from_lead_creates_current_project_models(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()
        lead_id = f"XS26{unique[:6]}"
        project_code = f"PJ26{unique[:6]}"

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        response = client.post(
            f"{prefix}/presales/from-lead",
            json={
                "lead_id": lead_id,
                "lead_name": f"售前转项目-{unique}",
                "customer_name": f"售前转项目客户-{unique}",
                "customer_industry": "电子制造",
                "customer_contact": "王工",
                "customer_phone": "021-88888888",
                "salesperson_id": admin_user.id,
                "salesperson_name": admin_user.real_name or admin_user.username,
                "decision": "GO",
                "evaluation_score": 82,
                "dimension_scores": {
                    "requirement_maturity": 85,
                    "technical_feasibility": 80,
                    "business_feasibility": 78,
                    "delivery_risk": 82,
                    "customer_relationship": 86,
                },
                "estimated_amount": "250000",
                "expected_delivery_date": "2026-09-30",
                "machine_count": 2,
                "requirement_summary": "测试站自动化产线",
                "predicted_win_rate": 0.72,
            },
            headers=headers,
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["success"] is True
        assert payload["data"]["project_code"] == project_code

        project = db_session.query(Project).filter(Project.project_code == project_code).first()
        try:
            assert project is not None
            assert project.project_name == f"售前转项目-{unique}"
            assert project.customer_name == f"售前转项目客户-{unique}"
            assert project.source_lead_id == lead_id
            assert project.salesperson_id == admin_user.id
            assert project.stage == "S1"
            assert project.health == "H1"
            assert float(project.contract_amount) == pytest.approx(250000.0)
            assert float(project.predicted_win_rate) == pytest.approx(0.72)

            machines = (
                db_session.query(Machine)
                .filter(Machine.project_id == project.id)
                .order_by(Machine.machine_no)
                .all()
            )
            assert [machine.machine_no for machine in machines] == [1, 2]
            assert machines[0].machine_name == f"售前转项目-{unique}-设备1"
        finally:
            if project is not None:
                db_session.query(Machine).filter(Machine.project_id == project.id).delete()
                db_session.query(Project).filter(Project.id == project.id).delete()
                db_session.query(Customer).filter(
                    Customer.customer_name == f"售前转项目客户-{unique}"
                ).delete()
                db_session.commit()

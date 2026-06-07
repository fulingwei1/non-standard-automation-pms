# -*- coding: utf-8 -*-
"""项目工作台前后端契约与交接上下文测试。"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Customer, Project
from app.models.sales import Contract, Opportunity, Quote, QuoteVersion
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


class TestProjectWorkspaceFrontendContractRoutes:
    """核对 frontend/src/services/api/projects.js 中声明的项目工作台路由。"""

    def test_declared_project_workspace_routes_exist(self, client: TestClient):
        routes = _route_map(client.app)
        prefix = settings.API_V1_PREFIX

        expected_routes = {
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/workspace"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/workspace/context"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/bonuses"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/meetings"),
            (
                "POST",
                f"{prefix}/project-workspace/projects/{{project_id}}/meetings/{{meeting_id}}/link",
            ),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/issues"),
            ("GET", f"{prefix}/project-workspace/projects/{{project_id}}/solutions"),
        }

        missing = sorted(expected_routes - routes)
        assert not missing, f"前端声明但后端未注册的项目工作台路由: {missing}"


class TestProjectWorkspaceHandoverContext:
    """验证销售/售前交接信息进入项目工作台。"""

    def test_project_workspace_context_includes_sales_presale_and_cost_baseline(
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
            customer_code=f"CUST-PW-{unique}",
            customer_name=f"项目交接客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPPW{unique[:6]}",
            customer=customer,
            opp_name=f"项目交接商机-{unique}",
            project_type="FCT",
            equipment_type="EOL",
            stage="WON",
            probability=95,
            est_amount=Decimal("580000"),
            est_margin=Decimal("35.50"),
            expected_close_date=date.today(),
            acceptance_basis="按冻结需求和终验清单验收",
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QTPW{unique[:6]}",
            opportunity=opportunity,
            customer=customer,
            status="APPROVED",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, opportunity, quote])
        db_session.flush()

        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("580000"),
            cost_total=Decimal("360000"),
            gross_margin=Decimal("37.93"),
            binding_status="valid",
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id

        contract = Contract(
            contract_code=f"CTPW{unique[:6]}",
            contract_name=f"项目交接合同-{unique}",
            contract_type="sales",
            customer=customer,
            opportunity=opportunity,
            quote_id=quote_version.id,
            total_amount=Decimal("580000"),
            signing_date=date.today(),
            delivery_terms="90天交付",
            payment_terms="30/60/10",
            status="signed",
            sales_owner_id=admin_user.id,
        )
        project = Project(
            project_code=f"PRJPW{unique[:6]}",
            project_name=f"项目交接项目-{unique}",
            customer=customer,
            customer_name=customer.customer_name,
            opportunity=opportunity,
            contract=contract,
            project_type="FCT",
            product_category="测试设备",
            industry="电子制造",
            contract_amount=Decimal("580000"),
            budget_amount=Decimal("360000"),
            stage="S1",
            status="ST01",
            health="H1",
            pm_id=admin_user.id,
            pm_name=admin_user.real_name or admin_user.username,
            created_by=admin_user.id,
        )
        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-PW-{unique}",
            title=f"项目交接售前工单-{unique}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            customer_id=None,
            customer_name=customer.customer_name,
            opportunity_id=opportunity.id,
            project_id=None,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            actual_hours=Decimal("18.5"),
            created_by=admin_user.id,
        )
        db_session.add_all([contract, project, ticket])
        db_session.flush()
        contract.project_id = project.id
        ticket.customer_id = customer.id
        ticket.project_id = project.id

        solution = PresaleSolution(
            solution_no=f"SOL-PW-{unique}",
            name=f"项目交接方案-{unique}",
            solution_type="CUSTOM",
            industry="电子制造",
            test_type="FCT",
            ticket_id=ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            requirement_summary="冻结需求摘要",
            solution_overview="设备方案概要",
            technical_spec="关键技术规格",
            estimated_cost=Decimal("355000"),
            suggested_price=Decimal("580000"),
            estimated_hours=120,
            estimated_duration=45,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add(solution)
        db_session.commit()

        response = client.get(
            f"{prefix}/project-workspace/projects/{project.id}/workspace/context",
            headers=headers,
        )
        assert response.status_code == 200, response.text

        payload = response.json()
        assert payload["project"]["id"] == project.id
        assert payload["contract"]["contract_code"] == contract.contract_code
        assert payload["opportunity"]["opp_code"] == opportunity.opp_code
        assert payload["quote"]["quote_code"] == quote.quote_code
        assert payload["quote"]["version"]["cost_total"] == 360000.0
        assert payload["baseline_cost"]["quote_cost_total"] == 360000.0
        assert payload["baseline_cost"]["presale_estimated_cost"] == 355000.0
        assert payload["presale_solutions"][0]["solution_no"] == solution.solution_no
        assert payload["handover_status"]["ready"] is True
        assert payload["handover_status"]["missing"] == []

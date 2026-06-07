# -*- coding: utf-8 -*-
"""售前前后端 API 契约对账测试。"""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import AssessmentStatusEnum, LeadOutcomeEnum
from app.models.presale import (
    PresaleSolution,
    PresaleSolutionTemplate,
    PresaleSupportTicket,
    PresaleTenderRecord,
    PresaleTicketProgress,
    TechnicalParameterTemplate,
)
from app.models.project import Customer, Machine, Project
from app.models.sales import (
    AssessmentTemplate,
    Lead,
    Opportunity,
    Quote,
    QuoteVersion,
    TechnicalAssessment,
)
from app.models.sales.technical_assessment import LeadRequirementDetail
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
            # presaleWorkbenchApi
            ("GET", f"{prefix}/presale/workbench/overview"),
            ("GET", f"{prefix}/presale/workbench/context"),
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

    def test_presale_ai_dashboard_and_cost_routes_exist(self, client: TestClient):
        """售前 AI 工作台和成本估算服务应暴露前端使用的共享 /api/v1 路由。"""
        routes = _route_map(client.app)
        prefix = settings.API_V1_PREFIX

        expected_routes = {
            ("GET", f"{prefix}/presale/ai/dashboard/stats"),
            ("POST", f"{prefix}/presale/ai/estimate-cost"),
            ("GET", f"{prefix}/presale/ai/historical-accuracy"),
            ("POST", f"{prefix}/presale/ai/update-actual-cost"),
            ("POST", f"{prefix}/presale/ai/workflow/start"),
            ("GET", f"{prefix}/presale/ai/health-check"),
            ("POST", f"{prefix}/presale/ai/predict-win-rate"),
        }

        missing = sorted(expected_routes - routes)
        assert not missing, f"售前 AI 前端依赖但后端未注册的路由: {missing}"

    def test_presale_ai_requirement_and_quotation_routes_use_single_api_prefix(
        self, client: TestClient
    ):
        """售前 AI 需求分析和报价生成不能注册成 /api/v1/api/v1 双前缀。"""
        routes = _route_map(client.app)
        prefix = settings.API_V1_PREFIX

        expected_routes = {
            ("POST", f"{prefix}/presale/ai/analyze-requirement"),
            ("POST", f"{prefix}/presale/ai/generate-quotation"),
        }
        forbidden_routes = {
            ("POST", f"{prefix}{prefix}/presale/ai/analyze-requirement"),
            ("POST", f"{prefix}{prefix}/presale/ai/generate-quotation"),
        }

        missing = sorted(expected_routes - routes)
        doubled = sorted(forbidden_routes & routes)
        assert not missing, f"售前 AI 单前缀路由未注册: {missing}"
        assert not doubled, f"售前 AI 路由仍然存在双 /api/v1 前缀: {doubled}"

    def test_presale_ai_solution_knowledge_and_emotion_routes_exist(
        self, client: TestClient
    ):
        """售前 AI 方案、知识库和情绪模块应注册到主 /api/v1 路由树。"""
        routes = _route_map(client.app)
        prefix = settings.API_V1_PREFIX

        expected_routes = {
            ("POST", f"{prefix}/presale/ai/generate-solution"),
            ("GET", f"{prefix}/presale/ai/solution/{{solution_id}}"),
            ("GET", f"{prefix}/presale/ai/knowledge-base/search"),
            ("POST", f"{prefix}/presale/ai/search-similar-cases"),
            ("POST", f"{prefix}/presale/ai/analyze-emotion"),
            ("POST", f"{prefix}/presale/ai/recommend-follow-up"),
        }
        forbidden_routes = {
            ("POST", f"{prefix}{prefix}/presale/ai/generate-solution"),
            ("GET", f"{prefix}{prefix}/presale/ai/knowledge-base/search"),
            ("POST", f"{prefix}{prefix}/presale/ai/analyze-emotion"),
        }

        missing = sorted(expected_routes - routes)
        doubled = sorted(forbidden_routes & routes)
        assert not missing, f"售前 AI 后续模块路由未注册: {missing}"
        assert not doubled, f"售前 AI 后续模块仍存在双 /api/v1 前缀: {doubled}"


class TestPresalesFrontendContractBehavior:
    """验证这几个曾经炸出 404/字段不匹配的接口现在真能用。"""

    def test_presale_workbench_overview_aggregates_presale_and_funnel_context(
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
            customer_code=f"CUST-WBO-{unique}",
            customer_name=f"工作台概览客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPWBO{unique[:6]}",
            customer=customer,
            opp_name=f"工作台概览商机-{unique}",
            stage="QUALIFICATION",
            probability=70,
            est_amount=Decimal("320000"),
            expected_close_date=date.today(),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-WBO-{unique}",
            title=f"工作台概览工单-{unique}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            customer_name=customer.customer_name,
            lead_id=930001,
            opportunity_id=None,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PROCESSING",
            created_by=admin_user.id,
        )
        assessment_template = AssessmentTemplate(
            template_code=f"AT-WBO-{unique}",
            template_name=f"概览评估模板-{unique}",
            category="CUSTOM",
            is_active=True,
            created_by=admin_user.id,
        )
        technical_template = TechnicalParameterTemplate(
            code=f"TP-WBO-{unique}",
            name=f"概览技术模板-{unique}",
            industry="NEW_ENERGY",
            test_type="FCT",
            is_active=True,
            created_by=admin_user.id,
        )
        db_session.add_all(
            [customer, opportunity, ticket, assessment_template, technical_template]
        )
        db_session.flush()
        ticket.customer_id = customer.id
        ticket.opportunity_id = opportunity.id
        solution = PresaleSolution(
            solution_no=f"SOL-WBO-{unique}",
            name=f"工作台概览方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
            status="DRAFT",
        )
        tender = PresaleTenderRecord(
            ticket_id=ticket.id,
            opportunity_id=opportunity.id,
            tender_no=f"TENDER-WBO-{unique}",
            tender_name=f"工作台概览投标-{unique}",
            customer_name=customer.customer_name,
            deadline=datetime.now(),
            budget_amount=Decimal("360000"),
            result="PENDING",
            leader_id=admin_user.id,
        )
        db_session.add_all([solution, tender])
        db_session.commit()

        try:
            response = client.get(f"{prefix}/presale/workbench/overview", headers=headers)
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload["success"] is True
            data = payload["data"]

            assert any(
                item["ticket_no"] == ticket.ticket_no
                for item in data["tickets"]["items"]
            )
            assert any(
                item["solution_no"] == solution.solution_no
                for item in data["solutions"]["items"]
            )
            overview_solution = next(
                item
                for item in data["solutions"]["items"]
                if item["solution_no"] == solution.solution_no
            )
            assert overview_solution["lead_id"] == ticket.lead_id
            assert any(
                item["tender_no"] == tender.tender_no
                for item in data["tenders"]["items"]
            )
            assert any(
                item["id"] == opportunity.id
                for item in data["opportunities"]["items"]
            )
            assert any(
                item["template_code"] == assessment_template.template_code
                for item in data["templates"]["assessment"]["items"]
            )
            assert any(
                item["code"] == technical_template.code
                for item in data["templates"]["technical"]["items"]
            )
            assert data["funnel"]["summary"]["opportunities"] >= 1
            assert data["meta"]["failures"] == []
        finally:
            db_session.query(PresaleTenderRecord).filter(
                PresaleTenderRecord.id == tender.id
            ).delete(synchronize_session=False)
            db_session.query(PresaleSolution).filter(PresaleSolution.id == solution.id).delete(
                synchronize_session=False
            )
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket.id
            ).delete(synchronize_session=False)
            db_session.query(TechnicalParameterTemplate).filter(
                TechnicalParameterTemplate.id == technical_template.id
            ).delete(synchronize_session=False)
            db_session.query(AssessmentTemplate).filter(
                AssessmentTemplate.id == assessment_template.id
            ).delete(synchronize_session=False)
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete()
            db_session.query(Customer).filter(Customer.id == customer.id).delete()
            db_session.commit()

    def test_ticket_list_accepts_comma_separated_ticket_types_for_requirement_survey(
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
            customer_code=f"CUST-SUR-{unique}",
            customer_name=f"需求调研客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        db_session.add(customer)
        db_session.flush()

        matching_research = PresaleSupportTicket(
            ticket_no=f"TICKET-SUR-REQ-{unique}",
            title=f"需求调研-{unique}",
            ticket_type="REQUIREMENT_RESEARCH",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PENDING",
            created_by=admin_user.id,
        )
        matching_exchange = PresaleSupportTicket(
            ticket_no=f"TICKET-SUR-EXC-{unique}",
            title=f"技术交流-{unique}",
            ticket_type="TECHNICAL_EXCHANGE",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PENDING",
            created_by=admin_user.id,
        )
        noise_solution = PresaleSupportTicket(
            ticket_no=f"TICKET-SUR-SOL-{unique}",
            title=f"方案设计-{unique}",
            ticket_type="SOLUTION_DESIGN",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PENDING",
            created_by=admin_user.id,
        )
        db_session.add_all([matching_research, matching_exchange, noise_solution])
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/tickets",
                params={
                    "customer_id": customer.id,
                    "ticket_type": "REQUIREMENT_RESEARCH,TECHNICAL_EXCHANGE,SITE_VISIT",
                },
                headers=headers,
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            ticket_types = {item["ticket_type"] for item in payload["items"]}

            assert payload["total"] == 2
            assert ticket_types == {"REQUIREMENT_RESEARCH", "TECHNICAL_EXCHANGE"}
        finally:
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.customer_id == customer.id
            ).delete(synchronize_session=False)
            db_session.query(Customer).filter(Customer.id == customer.id).delete()
            db_session.commit()

    def test_presale_workbench_context_returns_opportunity_assessment_ticket_solution_and_g2(
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
            customer_code=f"CUST-WBC-{unique}",
            customer_name=f"工作台上下文客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPWBC{unique[:6]}",
            customer=customer,
            opp_name=f"工作台上下文商机-{unique}",
            stage="QUALIFICATION",
            probability=75,
            est_amount=Decimal("420000"),
            expected_close_date=date.today(),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
            assessment_status=AssessmentStatusEnum.COMPLETED.value,
            requirement_maturity=4,
        )
        db_session.add_all([customer, opportunity])
        db_session.flush()

        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-WBC-{unique}",
            title=f"工作台上下文工单-{unique}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            opportunity_id=opportunity.id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            assessment_status=AssessmentStatusEnum.COMPLETED.value,
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()

        assessment = TechnicalAssessment(
            source_type="OPPORTUNITY",
            source_id=opportunity.id,
            evaluator_id=admin_user.id,
            status=AssessmentStatusEnum.COMPLETED.value,
            total_score=86,
            decision="推荐立项",
            presale_ticket_id=ticket.id,
        )
        solution = PresaleSolution(
            solution_no=f"SOL-WBC-{unique}",
            name=f"工作台上下文方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            estimated_cost=Decimal("260000"),
            suggested_price=Decimal("420000"),
            cost_breakdown={
                "mechanical": 120000,
                "electrical": 80000,
                "software": 40000,
                "standard": 15000,
                "labor": 5000,
                "other": 0,
                "notes": "项目管理成本基线",
            },
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
            status="APPROVED",
        )
        tender = PresaleTenderRecord(
            ticket_id=ticket.id,
            opportunity_id=opportunity.id,
            tender_no=f"TENDER-WBC-{unique}",
            tender_name=f"工作台上下文投标-{unique}",
            customer_name=customer.customer_name,
            deadline=datetime.now(),
            budget_amount=Decimal("450000"),
            our_bid_amount=Decimal("420000"),
            result="PENDING",
            leader_id=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QWBC{unique[:6]}",
            opportunity_id=opportunity.id,
            customer_id=customer.id,
            status="DRAFT",
            owner_id=admin_user.id,
        )
        db_session.add_all([assessment, solution, tender, quote])
        db_session.flush()
        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("420000"),
            cost_total=Decimal("260000"),
            gross_margin=Decimal("38.10"),
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id
        opportunity.assessment_id = assessment.id
        ticket.current_assessment_id = assessment.id
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/workbench/context",
                params={
                    "source_type": "opportunity",
                    "source_id": opportunity.id,
                    "presale_ticket_id": ticket.id,
                },
                headers=headers,
            )
            assert response.status_code == 200, response.text
            data = response.json()["data"]

            assert data["source"] == {"type": "opportunity", "id": opportunity.id}
            assert data["ticket"]["id"] == ticket.id
            assert data["assessment"]["current"]["id"] == assessment.id
            assert data["assessment"]["current"]["status"] == AssessmentStatusEnum.COMPLETED.value
            assert data["solutions"]["items"][0]["id"] == solution.id
            assert data["costing"]["baseline"]["estimated_cost"] == 260000.0
            assert data["costing"]["baseline"]["suggested_price"] == 420000.0
            assert data["costing"]["baseline"]["cost_breakdown"] == {
                "mechanical": 120000,
                "electrical": 80000,
                "software": 40000,
                "standard": 15000,
                "labor": 5000,
                "other": 0,
                "notes": "项目管理成本基线",
            }
            assert data["costing"]["baseline"]["gross_margin_rate"] == pytest.approx(0.380952, rel=1e-4)
            assert data["quotes"]["items"][0]["quote_code"] == quote.quote_code
            assert data["quotes"]["items"][0]["current_version"]["total_price"] == 420000.0
            assert data["tenders"]["items"][0]["tender_no"] == tender.tender_no
            assert data["tenders"]["items"][0]["our_bid_amount"] == 420000.0
            assert data["funnel"]["entityType"] == "OPPORTUNITY"
            assert data["funnel"]["entityId"] == opportunity.id
            assert data["funnel"]["gateStatus"]["gate_type"] == "G2"
            assert data["funnel"]["gateStatus"]["is_valid"] is True
            assert "技术评估通过" in data["funnel"]["gateStatus"]["checked_items"]
            assert data["meta"]["failures"] == []
        finally:
            db_session.query(QuoteVersion).filter(QuoteVersion.id == quote_version.id).delete(
                synchronize_session=False
            )
            db_session.query(Quote).filter(Quote.id == quote.id).delete(synchronize_session=False)
            db_session.query(PresaleTenderRecord).filter(
                PresaleTenderRecord.id == tender.id
            ).delete(synchronize_session=False)
            db_session.query(PresaleSolution).filter(PresaleSolution.id == solution.id).delete(
                synchronize_session=False
            )
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket.id
            ).update(
                {"current_assessment_id": None},
                synchronize_session=False,
            )
            db_session.query(TechnicalAssessment).filter(
                TechnicalAssessment.id == assessment.id
            ).delete(synchronize_session=False)
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket.id
            ).delete(synchronize_session=False)
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete()
            db_session.query(Customer).filter(Customer.id == customer.id).delete()
            db_session.commit()

    def test_presale_workbench_context_reuses_lead_requirement_detail_for_opportunity(
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
            customer_code=f"CUST-WBR-{unique}",
            customer_name=f"需求包复用客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        lead = Lead(
            lead_code=f"LDWBR{unique[:6]}",
            source="展会",
            customer_name=customer.customer_name,
            industry=customer.industry,
            demand_summary="FCT 测试线，客户已提供 SOW",
            owner_id=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPWBR{unique[:6]}",
            lead=lead,
            customer=customer,
            opp_name=f"需求包复用商机-{unique}",
            stage="QUALIFICATION",
            probability=70,
            est_amount=Decimal("520000"),
            expected_close_date=date.today(),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        requirement_detail = LeadRequirementDetail(
            lead=lead,
            target_object_type="FCT治具",
            application_scenario="整线终测",
            requirement_maturity=4,
            has_sow=True,
            cycle_time_seconds=Decimal("12.5"),
            requirement_version="REQ-V1",
        )
        db_session.add_all([customer, lead, opportunity, requirement_detail])
        db_session.flush()
        lead.requirement_detail_id = requirement_detail.id
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/workbench/context",
                params={
                    "source_type": "opportunity",
                    "source_id": opportunity.id,
                },
                headers=headers,
            )
            assert response.status_code == 200, response.text
            requirement = response.json()["data"]["assessment"]["requirementDetail"]

            assert requirement["lead_id"] == lead.id
            assert requirement["target_object_type"] == "FCT治具"
            assert requirement["application_scenario"] == "整线终测"
            assert requirement["requirement_maturity"] == 4
            assert requirement["has_sow"] is True
            assert requirement["cycle_time_seconds"] == 12.5
            assert requirement["requirement_version"] == "REQ-V1"
        finally:
            db_session.query(LeadRequirementDetail).filter(
                LeadRequirementDetail.id == requirement_detail.id
            ).delete(synchronize_session=False)
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete()
            db_session.query(Lead).filter(Lead.id == lead.id).delete()
            db_session.query(Customer).filter(Customer.id == customer.id).delete()
            db_session.commit()

    def test_ticket_update_and_complete_accept_json_body(
        self, client: TestClient, db_session: Session, admin_token: str
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

        detail = client.get(
            f"{prefix}/presale/tickets/{ticket_id}",
            headers=headers,
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["deliverables"] == [
            {
                "id": deliverable_payload["id"],
                "ticket_id": ticket_id,
                "deliverable_name": "初版技术方案",
                "deliverable_type": "SOLUTION",
                "file_path": "/files/solution-v1.pdf",
                "file_url": "/files/solution-v1.pdf",
                "status": "DRAFT",
                "created_at": deliverable_payload["created_at"],
                "updated_at": deliverable_payload["updated_at"],
            }
        ]

        completed = client.put(
            f"{prefix}/presale/tickets/{ticket_id}/complete",
            json={"actual_hours": 8, "completion_note": "方案可行，建议进入报价"},
            headers=headers,
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["status"] == "COMPLETED"
        assert completed.json()["actual_hours"] == pytest.approx(8.0)
        assert completed.json()["progress_percent"] == 100
        assert completed.json()["progress_note"] == "方案可行，建议进入报价"

        progress = (
            db_session.query(PresaleTicketProgress)
            .filter(PresaleTicketProgress.ticket_id == ticket_id)
            .order_by(PresaleTicketProgress.id.desc())
            .first()
        )
        assert progress is not None
        assert progress.progress_type == "COMPLETE"
        assert progress.content == "方案可行，建议进入报价"
        assert progress.progress_percent == 100

    def test_ticket_list_filters_by_opportunity_and_ticket_id(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None
        first_project = Project(
            project_code=f"PRJ-PSF-A-{unique}",
            project_name=f"售前过滤项目A-{unique}",
            customer_name="客户A",
            project_type="FCT",
            status="ST01",
            stage="S1",
            health="H1",
            created_by=admin_user.id,
        )
        second_project = Project(
            project_code=f"PRJ-PSF-B-{unique}",
            project_name=f"售前过滤项目B-{unique}",
            customer_name="客户B",
            project_type="ICT",
            status="ST01",
            stage="S1",
            health="H1",
            created_by=admin_user.id,
        )
        db_session.add_all([first_project, second_project])
        db_session.flush()

        first = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": f"销售侧售前支持-{unique}",
                "ticket_type": "TECHNICAL_SUPPORT",
                "urgency": "NORMAL",
                "customer_name": "客户A",
                "opportunity_id": 9001,
                "project_id": first_project.id,
            },
            headers=headers,
        )
        assert first.status_code == 201, first.text
        first_id = first.json()["id"]

        second = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": f"其它商机售前支持-{unique}",
                "ticket_type": "TECHNICAL_SUPPORT",
                "urgency": "NORMAL",
                "customer_name": "客户B",
                "opportunity_id": 9002,
                "project_id": second_project.id,
            },
            headers=headers,
        )
        assert second.status_code == 201, second.text
        second_id = second.json()["id"]

        try:
            by_opportunity = client.get(
                f"{prefix}/presale/tickets",
                params={"opportunity_id": 9001},
                headers=headers,
            )
            assert by_opportunity.status_code == 200, by_opportunity.text
            opportunity_items = by_opportunity.json()["items"]
            assert [item["id"] for item in opportunity_items] == [first_id]
            assert opportunity_items[0]["opportunity_id"] == 9001

            by_ticket = client.get(
                f"{prefix}/presale/tickets",
                params={"opportunity_id": 9002, "ticket_id": second_id},
                headers=headers,
            )
            assert by_ticket.status_code == 200, by_ticket.text
            ticket_items = by_ticket.json()["items"]
            assert [item["id"] for item in ticket_items] == [second_id]
            assert ticket_items[0]["opportunity_id"] == 9002

            by_project = client.get(
                f"{prefix}/presale/tickets",
                params={"project_id": first_project.id},
                headers=headers,
            )
            assert by_project.status_code == 200, by_project.text
            project_items = by_project.json()["items"]
            assert [item["id"] for item in project_items] == [first_id]
            assert project_items[0]["project_id"] == first_project.id
        finally:
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id.in_([first_id, second_id])
            ).delete(synchronize_session=False)
            db_session.query(Project).filter(
                Project.id.in_([first_project.id, second_project.id])
            ).delete(synchronize_session=False)
            db_session.commit()

    def test_ticket_list_filters_by_lead_id_for_early_presales_support(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()
        first_lead_id = 91001
        second_lead_id = 91002

        first = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": f"线索阶段售前支持-{unique}",
                "ticket_type": "TECHNICAL_SUPPORT",
                "urgency": "NORMAL",
                "customer_name": "线索客户A",
                "lead_id": first_lead_id,
            },
            headers=headers,
        )
        assert first.status_code == 201, first.text
        first_id = first.json()["id"]
        assert first.json()["lead_id"] == first_lead_id

        second = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": f"其它线索售前支持-{unique}",
                "ticket_type": "TECHNICAL_SUPPORT",
                "urgency": "NORMAL",
                "customer_name": "线索客户B",
                "lead_id": second_lead_id,
            },
            headers=headers,
        )
        assert second.status_code == 201, second.text
        second_id = second.json()["id"]

        try:
            by_lead = client.get(
                f"{prefix}/presale/tickets",
                params={"lead_id": first_lead_id},
                headers=headers,
            )
            assert by_lead.status_code == 200, by_lead.text
            lead_items = by_lead.json()["items"]
            assert [item["id"] for item in lead_items] == [first_id]
            assert lead_items[0]["lead_id"] == first_lead_id
        finally:
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id.in_([first_id, second_id])
            ).delete(synchronize_session=False)
            db_session.commit()

    def test_ticket_list_enriches_sales_opportunity_context_for_presales_tasks(
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
            customer_name=f"售前任务客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPPST{unique[:6]}",
            customer=customer,
            opp_name=f"售前任务商机-{unique}",
            stage="QUALIFICATION",
            probability=65,
            est_amount=Decimal("860000"),
            expected_close_date=date.today(),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add_all([customer, opportunity])
        db_session.flush()

        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-PST-{unique}",
            title=f"售前支持申请-{unique}",
            ticket_type="TECHNICAL_SUPPORT",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            opportunity_id=opportunity.id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PENDING",
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/tickets",
                params={"opportunity_id": opportunity.id, "ticket_id": ticket.id},
                headers=headers,
            )
            assert response.status_code == 200, response.text
            items = response.json()["items"]
            assert len(items) == 1

            item = items[0]
            assert item["id"] == ticket.id
            assert item["opportunity_id"] == opportunity.id
            assert item["opportunity_code"] == opportunity.opp_code
            assert item["opportunity_name"] == opportunity.opp_name
            assert item["estimated_amount"] == pytest.approx(860000.0)
        finally:
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket.id
            ).delete(synchronize_session=False)
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete()
            db_session.query(Customer).filter(Customer.id == customer.id).delete()
            db_session.commit()

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
            est_amount=Decimal("350000"),
            expected_close_date=date.today(),
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
        completed_payload = completed.json()
        assert completed_payload["status"] == "COMPLETED"
        assert completed_payload["assessment_status"] == AssessmentStatusEnum.COMPLETED.value
        assert completed_payload["current_assessment_id"] is not None

        refreshed = client.get(
            f"{prefix}/sales/opportunities/{opportunity.id}",
            headers=headers,
        )
        assert refreshed.status_code == 200, refreshed.text
        assert refreshed.json()["assessment_status"] == AssessmentStatusEnum.COMPLETED.value
        assert refreshed.json()["assessment_id"] is not None

        db_session.expire_all()
        refreshed_opportunity = db_session.get(Opportunity, opportunity.id)
        assert refreshed_opportunity.assessment_id is not None

        assessment = db_session.get(TechnicalAssessment, refreshed_opportunity.assessment_id)
        assert assessment is not None
        assert assessment.source_type == "OPPORTUNITY"
        assert assessment.source_id == opportunity.id
        assert assessment.status == AssessmentStatusEnum.COMPLETED.value
        assert assessment.decision == "推荐立项"
        assert assessment.presale_ticket_id == ticket_id

        refreshed_ticket = db_session.get(PresaleSupportTicket, ticket_id)
        assert refreshed_ticket.assessment_status == AssessmentStatusEnum.COMPLETED.value
        assert refreshed_ticket.current_assessment_id == assessment.id

        context = client.get(
            f"{prefix}/presale/workbench/context",
            params={
                "source_type": "opportunity",
                "source_id": opportunity.id,
                "presale_ticket_id": ticket_id,
            },
            headers=headers,
        )
        assert context.status_code == 200, context.text
        context_data = context.json()["data"]
        assert context_data["assessment"]["current"]["id"] == assessment.id
        assert context_data["funnel"]["gateStatus"]["is_valid"] is True
        assert "技术评估通过" in context_data["funnel"]["gateStatus"]["checked_items"]

    def test_completing_lead_ticket_updates_sales_assessment_status(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        lead = Lead(
            lead_code=f"LD-PS-{unique}",
            customer_name=f"线索售前闭环客户-{unique}",
            source="展会",
            industry="电子制造",
            owner_id=admin_user.id,
            assessment_status=AssessmentStatusEnum.PENDING.value,
        )
        db_session.add(lead)
        db_session.commit()

        created = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": "线索可行性评估支持",
                "ticket_type": "FEASIBILITY_ASSESSMENT",
                "urgency": "NORMAL",
                "description": "完成后应反写线索技术评估状态",
                "customer_name": lead.customer_name,
                "lead_id": lead.id,
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        ticket_id = created.json()["id"]

        completed = client.put(
            f"{prefix}/presale/tickets/{ticket_id}/complete",
            json={"actual_hours": 4, "completion_note": "线索方案可行，建议继续跟进"},
            headers=headers,
        )
        assert completed.status_code == 200, completed.text
        completed_payload = completed.json()
        assert completed_payload["status"] == "COMPLETED"
        assert completed_payload["assessment_status"] == AssessmentStatusEnum.COMPLETED.value
        assert completed_payload["current_assessment_id"] is not None

        db_session.expire_all()
        refreshed_lead = db_session.get(Lead, lead.id)
        assert refreshed_lead.assessment_status == AssessmentStatusEnum.COMPLETED.value
        assert refreshed_lead.assessment_id is not None

        assessment = db_session.get(TechnicalAssessment, refreshed_lead.assessment_id)
        assert assessment is not None
        assert assessment.source_type == "LEAD"
        assert assessment.source_id == lead.id
        assert assessment.status == AssessmentStatusEnum.COMPLETED.value
        assert assessment.decision == "推荐立项"
        assert assessment.presale_ticket_id == ticket_id

        refreshed_ticket = db_session.get(PresaleSupportTicket, ticket_id)
        assert refreshed_ticket.assessment_status == AssessmentStatusEnum.COMPLETED.value
        assert refreshed_ticket.current_assessment_id == assessment.id

    def test_ticket_board_keeps_processing_and_review_tickets_visible(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        processing_ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-BRD-P-{unique}",
            title=f"看板处理中工单-{unique}",
            ticket_type="TECHNICAL_EXCHANGE",
            urgency="NORMAL",
            customer_name="看板测试客户",
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PROCESSING",
            created_by=admin_user.id,
        )
        review_ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-BRD-R-{unique}",
            title=f"看板评审工单-{unique}",
            ticket_type="SOLUTION_REVIEW",
            urgency="HIGH",
            customer_name="看板测试客户",
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="REVIEW",
            created_by=admin_user.id,
        )
        db_session.add_all([processing_ticket, review_ticket])
        db_session.commit()

        try:
            response = client.get(f"{prefix}/presale/tickets/board", headers=headers)
            assert response.status_code == 200, response.text
            payload = response.json()

            assert any(
                item["ticket_no"] == processing_ticket.ticket_no
                for item in payload["in_progress"]
            )
            assert any(
                item["ticket_no"] == review_ticket.ticket_no
                for item in payload["reviewing"]
            )
        finally:
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.ticket_no.in_(
                    [processing_ticket.ticket_no, review_ticket.ticket_no]
                )
            ).delete(synchronize_session=False)
            db_session.commit()

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

    def test_template_list_normalizes_legacy_null_active_flag(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        template = PresaleSolutionTemplate(
            template_no=f"TMP-NULL-{unique}",
            name=f"历史空启用标记模板-{unique}",
            industry="新能源",
            test_type="EOL",
            description="兼容历史 is_active 为空的数据",
            is_active=True,
            created_by=admin_user.id,
        )
        db_session.add(template)
        db_session.commit()

        db_session.execute(
            text("UPDATE presale_solution_template SET is_active = NULL WHERE id = :id"),
            {"id": template.id},
        )
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/templates",
                params={"keyword": unique},
                headers=headers,
            )
            assert response.status_code == 200, response.text

            payload = response.json()
            item = next(
                item for item in payload["items"] if item["template_no"] == template.template_no
            )
            assert item["is_active"] is True
        finally:
            db_session.query(PresaleSolutionTemplate).filter(
                PresaleSolutionTemplate.template_no == template.template_no
            ).delete(synchronize_session=False)
            db_session.commit()

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
            json={
                "template_id": template_id,
                "lead_id": 2026,
                "opportunity_id": 2,
                "ticket_id": 501,
                "project_id": 42,
                "parameters": {"test_station_count": 4},
            },
            headers=headers,
        )
        assert estimated.status_code == 200, estimated.text
        estimate_payload = estimated.json()
        assert estimate_payload["total_cost"] == pytest.approx(82000.0)
        assert estimate_payload["lead_id"] == 2026
        assert estimate_payload["opportunity_id"] == 2
        assert estimate_payload["ticket_id"] == 501
        assert estimate_payload["project_id"] == 42

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

    def test_solution_list_filters_by_lead_id_through_support_ticket(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        lead_id = 92001
        other_lead_id = 92002
        target_ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-SOL-LEAD-{unique}",
            title=f"线索方案工单-{unique}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            lead_id=lead_id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            created_by=admin_user.id,
        )
        other_ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-SOL-OTHER-{unique}",
            title=f"其他线索方案工单-{unique}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            lead_id=other_lead_id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            created_by=admin_user.id,
        )
        db_session.add_all([target_ticket, other_ticket])
        db_session.flush()

        target_solution = PresaleSolution(
            solution_no=f"SOL-LEAD-{unique}",
            name=f"目标线索方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=target_ticket.id,
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        other_solution = PresaleSolution(
            solution_no=f"SOL-LEAD-NOISE-{unique}",
            name=f"其他线索方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=other_ticket.id,
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add_all([target_solution, other_solution])
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/proposals/solutions",
                params={"lead_id": lead_id, "keyword": unique},
                headers=headers,
            )
            assert response.status_code == 200, response.text
            items = response.json()["items"]

            assert [item["id"] for item in items] == [target_solution.id]
            assert items[0]["ticket_id"] == target_ticket.id
            assert items[0]["lead_id"] == lead_id
        finally:
            db_session.query(PresaleSolution).filter(
                PresaleSolution.id.in_([target_solution.id, other_solution.id])
            ).delete(synchronize_session=False)
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id.in_([target_ticket.id, other_ticket.id])
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

    def test_solution_created_from_lead_context_is_visible_in_lead_scope(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        lead = Lead(
            lead_code=f"LD-SOL-{unique}",
            customer_name=f"线索方案客户-{unique}",
            source="展会",
            industry="电子制造",
            owner_id=admin_user.id,
        )
        db_session.add(lead)
        db_session.commit()

        created_solution = client.post(
            f"{prefix}/presale/proposals/solutions",
            json={
                "name": f"线索阶段售前方案-{unique}",
                "solution_type": "CUSTOM",
                "lead_id": lead.id,
                "requirement_summary": "从销售线索直接进入售前方案管理生成",
            },
            headers=headers,
        )
        assert created_solution.status_code == 201, created_solution.text
        solution = created_solution.json()
        ticket_id = solution.get("ticket_id")

        try:
            assert solution["lead_id"] == lead.id
            assert ticket_id is not None

            db_session.expire_all()
            ticket = db_session.get(PresaleSupportTicket, ticket_id)
            assert ticket is not None
            assert ticket.lead_id == lead.id
            assert ticket.ticket_type == "SOLUTION_DESIGN"

            by_lead = client.get(
                f"{prefix}/presale/proposals/solutions",
                params={"lead_id": lead.id},
                headers=headers,
            )
            assert by_lead.status_code == 200, by_lead.text
            assert any(item["id"] == solution["id"] for item in by_lead.json()["items"])
        finally:
            db_session.query(PresaleSolution).filter(
                PresaleSolution.id == solution["id"]
            ).delete(synchronize_session=False)
            if ticket_id:
                db_session.query(PresaleSupportTicket).filter(
                    PresaleSupportTicket.id == ticket_id
                ).delete(synchronize_session=False)
            db_session.query(Lead).filter(Lead.id == lead.id).delete()
            db_session.commit()

    def test_solution_created_from_cost_estimation_preserves_context_and_breakdown(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        lead = Lead(
            lead_code=f"LD-COST-{unique}",
            customer_name=f"线索成本客户-{unique}",
            source="展会",
            industry="电子制造",
            owner_id=admin_user.id,
        )
        db_session.add(lead)
        db_session.commit()

        cost_breakdown = {
            "mechanical": 55000,
            "electrical": 32000,
            "software": 18000,
            "standard": 12000,
            "labor": 26000,
            "other": 7000,
            "notes": "直接成本估算生成",
        }

        created_solution = client.post(
            f"{prefix}/presale/proposals/solutions",
            json={
                "name": f"线索直接成本估算-{unique}",
                "solution_type": "CUSTOM",
                "lead_id": lead.id,
                "estimated_cost": 150000,
                "suggested_price": 210000,
                "cost_breakdown": cost_breakdown,
            },
            headers=headers,
        )
        assert created_solution.status_code == 201, created_solution.text
        solution = created_solution.json()
        ticket_id = solution.get("ticket_id")

        try:
            assert solution["lead_id"] == lead.id
            assert solution["ticket_id"] is not None
            assert solution["estimated_cost"] == 150000.0
            assert solution["suggested_price"] == 210000.0
            assert solution["cost_breakdown"] == cost_breakdown

            db_session.expire_all()
            stored = db_session.get(PresaleSolution, solution["id"])
            assert stored is not None
            assert stored.cost_breakdown == cost_breakdown
        finally:
            db_session.query(PresaleSolution).filter(
                PresaleSolution.id == solution["id"]
            ).delete(synchronize_session=False)
            if ticket_id:
                db_session.query(PresaleSupportTicket).filter(
                    PresaleSupportTicket.id == ticket_id
                ).delete(synchronize_session=False)
            db_session.query(Lead).filter(Lead.id == lead.id).delete()
            db_session.commit()

    def test_solution_update_preserves_cost_breakdown(
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
                "name": f"成本明细方案-{unique}",
                "solution_type": "CUSTOM",
                "requirement_summary": "用于验证售前成本明细保存",
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        solution_id = created.json()["id"]

        cost_breakdown = {
            "mechanical": 55000,
            "electrical": 32000,
            "software": 18000,
            "standard": 12000,
            "labor": 26000,
            "other": 7000,
            "notes": "含夹具、PLC、电控和调试人工",
        }

        try:
            updated = client.put(
                f"{prefix}/presale/proposals/solutions/{solution_id}",
                json={
                    "estimated_cost": 150000,
                    "suggested_price": 240000,
                    "cost_breakdown": cost_breakdown,
                },
                headers=headers,
            )
            assert updated.status_code == 200, updated.text
            payload = updated.json()
            assert payload["estimated_cost"] == 150000.0
            assert payload["suggested_price"] == 240000.0
            assert payload["cost_breakdown"] == cost_breakdown

            db_session.expire_all()
            solution = db_session.get(PresaleSolution, solution_id)
            assert solution is not None
            assert solution.cost_breakdown == cost_breakdown
        finally:
            db_session.query(PresaleSolution).filter(PresaleSolution.id == solution_id).delete(
                synchronize_session=False
            )
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

    def test_approved_solution_completes_opportunity_assessment_for_g2_gate(
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
            customer_code=f"CUST-G2-{unique}",
            customer_name=f"G2闭环客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        db_session.add(customer)
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPPG2{unique[:6]}",
            customer_id=customer.id,
            opp_name=f"G2闭环商机-{unique}",
            stage="QUALIFICATION",
            probability=65,
            est_amount=Decimal("280000"),
            expected_close_date=date.today(),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
            assessment_status=AssessmentStatusEnum.PENDING.value,
            requirement_maturity=3,
        )
        db_session.add(opportunity)
        db_session.commit()

        created_ticket = client.post(
            f"{prefix}/presale/tickets",
            json={
                "title": f"G2方案支持工单-{unique}",
                "ticket_type": "SOLUTION",
                "urgency": "NORMAL",
                "customer_id": customer.id,
                "customer_name": customer.customer_name,
                "opportunity_id": opportunity.id,
            },
            headers=headers,
        )
        assert created_ticket.status_code == 201, created_ticket.text
        ticket_id = created_ticket.json()["id"]

        created_solution = client.post(
            f"{prefix}/presale/proposals/solutions",
            json={
                "name": f"G2阶段门方案-{unique}",
                "solution_type": "CUSTOM",
                "ticket_id": ticket_id,
                "requirement_summary": "客户需求已澄清",
                "solution_overview": "技术路线可行",
                "estimated_cost": 180000,
                "suggested_price": 280000,
            },
            headers=headers,
        )
        assert created_solution.status_code == 201, created_solution.text
        solution_id = created_solution.json()["id"]

        try:
            approved = client.put(
                f"{prefix}/presale/proposals/solutions/{solution_id}/review",
                json={"review_status": "APPROVED", "review_comment": "方案评审通过"},
                headers=headers,
            )
            assert approved.status_code == 200, approved.text
            assert approved.json()["status"] == "APPROVED"

            db_session.expire_all()
            refreshed_opportunity = db_session.get(Opportunity, opportunity.id)
            assert refreshed_opportunity.assessment_status == AssessmentStatusEnum.COMPLETED.value
            assert refreshed_opportunity.assessment_id is not None

            assessment = db_session.get(TechnicalAssessment, refreshed_opportunity.assessment_id)
            assert assessment is not None
            assert assessment.source_type == "OPPORTUNITY"
            assert assessment.source_id == opportunity.id
            assert assessment.status == AssessmentStatusEnum.COMPLETED.value
            assert assessment.decision == "推荐立项"
            assert assessment.presale_ticket_id == ticket_id

            refreshed_ticket = db_session.get(PresaleSupportTicket, ticket_id)
            assert refreshed_ticket.status == "COMPLETED"
            assert refreshed_ticket.assessment_status == AssessmentStatusEnum.COMPLETED.value
            assert refreshed_ticket.current_assessment_id == assessment.id

            gate = client.post(
                f"{prefix}/sales/funnel/validate-gate",
                json={"gate_type": "G2", "entity_id": opportunity.id, "save_result": False},
                headers=headers,
            )
            assert gate.status_code == 200, gate.text
            gate_data = gate.json()["data"]
            assert gate_data["is_valid"] is True
            assert "技术评估通过" in gate_data["checked_items"]
        finally:
            db_session.query(PresaleSolution).filter(PresaleSolution.id == solution_id).delete(
                synchronize_session=False
            )
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket_id
            ).delete(synchronize_session=False)
            db_session.query(TechnicalAssessment).filter(
                TechnicalAssessment.source_type == "OPPORTUNITY",
                TechnicalAssessment.source_id == opportunity.id,
            ).delete(synchronize_session=False)
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete()
            db_session.query(Customer).filter(Customer.id == customer.id).delete()
            db_session.commit()

    def test_tender_list_filters_by_sales_support_context(
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
            customer_code=f"CUST-BID-{unique}",
            customer_name=f"投标筛选客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPBID{unique[:6]}",
            customer=customer,
            opp_name=f"投标筛选商机-{unique}",
            stage="QUALIFICATION",
            probability=60,
            est_amount=Decimal("1200000"),
            expected_close_date=date.today(),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add_all([customer, opportunity])
        db_session.flush()

        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-BID-{unique}",
            title=f"投标支持申请-{unique}",
            ticket_type="TECHNICAL_SUPPORT",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            opportunity_id=opportunity.id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PENDING",
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()

        matching_tender = PresaleTenderRecord(
            ticket_id=ticket.id,
            opportunity_id=opportunity.id,
            tender_no=f"BID-MATCH-{unique}",
            tender_name=f"匹配投标-{unique}",
            customer_name=customer.customer_name,
            budget_amount=Decimal("900000"),
            result="PENDING",
        )
        noise_tender = PresaleTenderRecord(
            tender_no=f"BID-NOISE-{unique}",
            tender_name=f"不应出现投标-{unique}",
            customer_name=customer.customer_name,
            budget_amount=Decimal("100000"),
            result="PENDING",
        )
        db_session.add_all([matching_tender, noise_tender])
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/tenders",
                params={"opportunity_id": opportunity.id, "ticket_id": ticket.id},
                headers=headers,
            )
            assert response.status_code == 200, response.text
            items = response.json()["items"]
            assert [item["id"] for item in items] == [matching_tender.id]
            assert items[0]["opportunity_id"] == opportunity.id
            assert items[0]["ticket_id"] == ticket.id
        finally:
            db_session.query(PresaleTenderRecord).filter(
                PresaleTenderRecord.id.in_([matching_tender.id, noise_tender.id])
            ).delete(synchronize_session=False)
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket.id
            ).delete(synchronize_session=False)
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete()
            db_session.query(Customer).filter(Customer.id == customer.id).delete()
            db_session.commit()

    def test_tender_list_filters_by_lead_id_through_support_ticket(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        target_ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-BID-LEAD-{unique}",
            title=f"线索投标支持申请-{unique}",
            ticket_type="TECHNICAL_SUPPORT",
            urgency="NORMAL",
            customer_name=f"线索投标客户-{unique}",
            lead_id=810001,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PENDING",
            created_by=admin_user.id,
        )
        noise_ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-BID-NOISE-{unique}",
            title=f"其他线索投标支持申请-{unique}",
            ticket_type="TECHNICAL_SUPPORT",
            urgency="NORMAL",
            customer_name=f"其他线索投标客户-{unique}",
            lead_id=810002,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PENDING",
            created_by=admin_user.id,
        )
        db_session.add_all([target_ticket, noise_ticket])
        db_session.flush()

        matching_tender = PresaleTenderRecord(
            ticket_id=target_ticket.id,
            tender_no=f"BID-LEAD-MATCH-{unique}",
            tender_name=f"线索匹配投标-{unique}",
            customer_name=target_ticket.customer_name,
            budget_amount=Decimal("900000"),
            result="PENDING",
        )
        noise_tender = PresaleTenderRecord(
            ticket_id=noise_ticket.id,
            tender_no=f"BID-LEAD-NOISE-{unique}",
            tender_name=f"其他线索投标-{unique}",
            customer_name=noise_ticket.customer_name,
            budget_amount=Decimal("100000"),
            result="PENDING",
        )
        db_session.add_all([matching_tender, noise_tender])
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/tenders",
                params={"lead_id": target_ticket.lead_id},
                headers=headers,
            )
            assert response.status_code == 200, response.text
            items = response.json()["items"]
            assert [item["id"] for item in items] == [matching_tender.id]
            assert items[0]["ticket_id"] == target_ticket.id
            assert items[0]["lead_id"] == target_ticket.lead_id
        finally:
            db_session.query(PresaleTenderRecord).filter(
                PresaleTenderRecord.id.in_([matching_tender.id, noise_tender.id])
            ).delete(synchronize_session=False)
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id.in_([target_ticket.id, noise_ticket.id])
            ).delete(synchronize_session=False)
            db_session.commit()

    def test_tender_detail_exposes_lead_id_through_support_ticket(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-BID-DETAIL-{unique}",
            title=f"线索投标详情支持申请-{unique}",
            ticket_type="TECHNICAL_SUPPORT",
            urgency="NORMAL",
            customer_name=f"线索投标详情客户-{unique}",
            lead_id=810003,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="PENDING",
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()

        tender = PresaleTenderRecord(
            ticket_id=ticket.id,
            tender_no=f"BID-DETAIL-{unique}",
            tender_name=f"线索投标详情-{unique}",
            customer_name=ticket.customer_name,
            budget_amount=Decimal("900000"),
            result="PENDING",
        )
        db_session.add(tender)
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/tenders/{tender.id}",
                headers=headers,
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload["ticket_id"] == ticket.id
            assert payload["lead_id"] == ticket.lead_id
        finally:
            db_session.query(PresaleTenderRecord).filter(
                PresaleTenderRecord.id == tender.id
            ).delete(synchronize_session=False)
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket.id
            ).delete(synchronize_session=False)
            db_session.commit()

    def test_tender_create_and_list_preserve_project_context(
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
            project_code=f"PTA{unique[:6]}",
            project_name=f"投标过滤项目A-{unique}",
            customer_name=f"投标过滤客户A-{unique}",
            project_type="FCT",
            status="ST01",
            stage="S1",
            health="H1",
            created_by=admin_user.id,
        )
        project_b = Project(
            project_code=f"PTB{unique[:6]}",
            project_name=f"投标过滤项目B-{unique}",
            customer_name=f"投标过滤客户B-{unique}",
            project_type="ICT",
            status="ST01",
            stage="S1",
            health="H1",
            created_by=admin_user.id,
        )
        db_session.add_all([project_a, project_b])
        db_session.flush()
        project_a_id = project_a.id
        project_b_id = project_b.id

        created = client.post(
            f"{prefix}/presale/tenders",
            json={
                "tender_name": f"项目A投标-{unique}",
                "customer_name": project_a.customer_name,
                "project_id": project_a_id,
                "opportunity_id": 9101,
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        created_payload = created.json()
        assert created_payload["project_id"] == project_a_id

        noise_tender = PresaleTenderRecord(
            tender_no=f"BID-NOISE-PROJ-{unique}",
            tender_name=f"项目B投标-{unique}",
            customer_name=project_b.customer_name,
            project_id=project_b_id,
            opportunity_id=9102,
            budget_amount=Decimal("100000"),
            result="PENDING",
        )
        db_session.add(noise_tender)
        db_session.commit()

        try:
            response = client.get(
                f"{prefix}/presale/tenders",
                params={"project_id": project_a_id},
                headers=headers,
            )
            assert response.status_code == 200, response.text
            items = response.json()["items"]
            assert [item["id"] for item in items] == [created_payload["id"]]
            assert items[0]["project_id"] == project_a_id
            assert items[0]["opportunity_id"] == 9101
        finally:
            db_session.query(PresaleTenderRecord).filter(
                PresaleTenderRecord.id.in_([created_payload["id"], noise_tender.id])
            ).delete(synchronize_session=False)
            db_session.query(Project).filter(
                Project.id.in_([project_a_id, project_b_id])
            ).delete(synchronize_session=False)
            db_session.commit()

    def test_tender_created_from_lead_context_is_visible_in_lead_scope(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        lead = Lead(
            lead_code=f"LD-BID-{unique}",
            customer_name=f"线索投标客户-{unique}",
            source="展会",
            industry="电子制造",
            owner_id=admin_user.id,
        )
        db_session.add(lead)
        db_session.commit()

        created = client.post(
            f"{prefix}/presale/tenders",
            json={
                "tender_name": f"线索阶段投标-{unique}",
                "customer_name": lead.customer_name,
                "lead_id": lead.id,
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        tender = created.json()
        ticket_id = tender.get("ticket_id")

        try:
            assert tender["lead_id"] == lead.id
            assert ticket_id is not None

            db_session.expire_all()
            ticket = db_session.get(PresaleSupportTicket, ticket_id)
            assert ticket is not None
            assert ticket.lead_id == lead.id
            assert ticket.ticket_type == "TENDER_SUPPORT"

            by_lead = client.get(
                f"{prefix}/presale/tenders",
                params={"lead_id": lead.id},
                headers=headers,
            )
            assert by_lead.status_code == 200, by_lead.text
            assert [item["id"] for item in by_lead.json()["items"]] == [tender["id"]]
        finally:
            db_session.query(PresaleTenderRecord).filter(
                PresaleTenderRecord.id == tender["id"]
            ).delete(synchronize_session=False)
            if ticket_id:
                db_session.query(PresaleSupportTicket).filter(
                    PresaleSupportTicket.id == ticket_id
                ).delete(synchronize_session=False)
            db_session.query(Lead).filter(Lead.id == lead.id).delete()
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

    def test_tender_analysis_route_is_not_shadowed_by_tender_detail(
        self, client: TestClient, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX

        response = client.get(f"{prefix}/presale/tenders/analysis", headers=headers)

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["data"]["summary"]["total_tenders"] >= 0

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

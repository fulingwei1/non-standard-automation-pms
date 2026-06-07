# -*- coding: utf-8 -*-
"""
销售合同管理 API 测试

测试合同的创建、查询、更新、审批、归档等功能
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import AssessmentStatusEnum
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Customer, Project
from app.models.sales import (
    Contract,
    ContractDeliverable,
    Lead,
    Opportunity,
    Quote,
    QuoteVersion,
    TechnicalAssessment,
)
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSalesContractsAPI:
    """销售合同管理 API 测试类"""

    def test_list_contracts(self, client: TestClient, admin_token: str):
        """测试获取合同列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/contracts/", headers=headers)

        if response.status_code == 404:
            pytest.skip("Contracts API not implemented")

        assert response.status_code == 200, response.text

    def test_create_contract(self, client: TestClient, admin_token: str):
        """测试创建合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique = uuid4().hex[:6].upper()

        contract_data = {
            "contract_no": f"CTAPI{unique}",
            "customer_id": 1,
            "quote_id": 1,
            "contract_name": "测试设备采购合同",
            "contract_type": "sales",
            "sign_date": datetime.now().strftime("%Y-%m-%d"),
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "total_amount": 500000.0,
            "payment_terms": "分期付款，按进度支付",
            "delivery_terms": "3个月内交付",
            "warranty_period": "12个月",
            "remarks": "重要合同",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/?skip_g3_validation=true",
            headers=headers,
            json=contract_data,
        )

        if response.status_code == 404:
            pytest.skip("Contracts API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_create_contract_accepts_legacy_quote_payload_and_infers_context(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """旧前端合同 payload 也应能从报价反推出商机、客户和报价版本。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-CONTRACT-{unique}",
            customer_name=f"合同兼容客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPCON{unique[:6]}",
            customer=customer,
            opp_name=f"合同兼容商机-{unique}",
            stage="QUOTATION",
            probability=80,
            est_amount=Decimal("500000"),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QCON{unique[:6]}",
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
            total_price=Decimal("500000"),
            cost_total=Decimal("300000"),
            gross_margin=Decimal("40.00"),
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id
        db_session.commit()

        contract_code = f"CTCON{unique[:6]}"
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts?skip_g3_validation=true",
            headers=headers,
            json={
                "contract_no": contract_code,
                "quote_id": quote.id,
                "contract_name": f"合同兼容测试-{unique}",
                "total_amount": 500000,
                "sign_date": "2026-06-08",
                "payment_terms": "30-60-10",
            },
        )

        try:
            assert response.status_code == 201, response.text
            payload = response.json()
            assert payload["contract_code"] == contract_code
            assert payload["opportunity_id"] == opportunity.id
            assert payload["customer_id"] == customer.id
            assert payload["quote_version_id"] == quote_version.id
            assert float(payload["contract_amount"]) == 500000.0
            assert payload["signed_date"] == "2026-06-08"
            assert payload["payment_terms_summary"] == "30-60-10"
        finally:
            db_session.query(Contract).filter(Contract.contract_code == contract_code).delete(
                synchronize_session=False
            )
            quote.current_version_id = None
            db_session.flush()
            db_session.query(QuoteVersion).filter(QuoteVersion.id == quote_version.id).delete(
                synchronize_session=False
            )
            db_session.query(Quote).filter(Quote.id == quote.id).delete(
                synchronize_session=False
            )
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete(
                synchronize_session=False
            )
            db_session.query(Customer).filter(Customer.id == customer.id).delete(
                synchronize_session=False
            )
            db_session.commit()

    def test_sign_contract_auto_creates_project_with_quote_cost_and_opportunity_context(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """合同签署自动建项时，应把报价成本基线和商机上下文带入项目。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-SIGN-{unique}",
            customer_name=f"签约建项客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        lead = Lead(
            lead_code=f"LEADSIGN{unique[:6]}",
            customer_name=customer.customer_name,
            industry="电子制造",
            demand_summary="签约前已冻结FCT/EOL测试线需求",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, lead])
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPPSIGN{unique[:6]}",
            lead_id=lead.id,
            customer=customer,
            opp_name=f"签约建项商机-{unique}",
            project_type="FCT",
            equipment_type="EOL",
            stage="WON",
            probability=95,
            est_amount=Decimal("580000"),
            est_margin=Decimal("37.93"),
            acceptance_basis="按冻结需求和终验清单验收",
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QSIGN{unique[:6]}",
            opportunity=opportunity,
            customer=customer,
            status="APPROVED",
            owner_id=admin_user.id,
        )
        db_session.add_all([opportunity, quote])
        db_session.flush()

        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("580000"),
            cost_total=Decimal("360000"),
            gross_margin=Decimal("37.93"),
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id

        contract = Contract(
            contract_code=f"CTSIGN{unique[:6]}",
            contract_name=f"签约建项合同-{unique}",
            contract_type="sales",
            customer=customer,
            opportunity=opportunity,
            quote_id=quote_version.id,
            total_amount=Decimal("580000"),
            payment_terms="30-60-10",
            status="approved",
            sales_owner_id=admin_user.id,
        )
        db_session.add(contract)
        db_session.commit()

        response = client.post(
            (
                f"{settings.API_V1_PREFIX}/sales/contracts/{contract.id}/sign"
                "?auto_generate_payment_plans=false"
            ),
            headers=headers,
            json={
                "sign_date": "2026-06-08",
                "signed_by": "张总",
                "customer_signed_by": "李经理",
                "auto_create_project": True,
            },
        )

        try:
            assert response.status_code == 200, response.text
            data = response.json()["data"]
            project = db_session.get(Project, data["project_id"])
            assert project is not None
            assert project.contract_id == contract.id
            assert project.customer_id == customer.id
            assert project.lead_id == lead.id
            assert project.opportunity_id == opportunity.id
            assert project.contract_no == contract.contract_code
            assert float(project.contract_amount) == 580000.0
            assert float(project.budget_amount) == 360000.0
            assert project.project_type == "FCT"
            assert project.product_category == "EOL"
            assert project.industry == "电子制造"
        finally:
            db_session.query(Project).filter(Project.contract_id == contract.id).delete(
                synchronize_session=False
            )
            db_session.query(Contract).filter(Contract.id == contract.id).delete(
                synchronize_session=False
            )
            quote.current_version_id = None
            db_session.flush()
            db_session.query(QuoteVersion).filter(QuoteVersion.id == quote_version.id).delete(
                synchronize_session=False
            )
            db_session.query(Quote).filter(Quote.id == quote.id).delete(
                synchronize_session=False
            )
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete(
                synchronize_session=False
            )
            db_session.query(Lead).filter(Lead.id == lead.id).delete(synchronize_session=False)
            db_session.query(Customer).filter(Customer.id == customer.id).delete(
                synchronize_session=False
            )
            db_session.commit()

    def test_sign_contract_auto_links_presale_context_to_created_project(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """合同签署自动建项后，售前工单和方案应正式绑定到项目。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-SIGN-PRE-{unique}",
            customer_name=f"签约售前回填客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        lead = Lead(
            lead_code=f"LEADPRE{unique[:6]}",
            customer_name=customer.customer_name,
            industry="电子制造",
            demand_summary="售前技术方案已完成，签约后应交给项目继续执行",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, lead])
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPPPRE{unique[:6]}",
            lead_id=lead.id,
            customer=customer,
            opp_name=f"签约售前回填商机-{unique}",
            project_type="FCT",
            equipment_type="EOL",
            stage="WON",
            probability=95,
            est_amount=Decimal("680000"),
            est_margin=Decimal("35.29"),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QPRE{unique[:6]}",
            opportunity=opportunity,
            customer=customer,
            status="APPROVED",
            owner_id=admin_user.id,
        )
        db_session.add_all([opportunity, quote])
        db_session.flush()

        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("680000"),
            cost_total=Decimal("440000"),
            gross_margin=Decimal("35.29"),
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id

        ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-PRE-{unique}",
            title=f"签约前售前方案工单-{unique}",
            ticket_type="SOLUTION",
            urgency="NORMAL",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            lead_id=lead.id,
            opportunity_id=opportunity.id,
            project_id=None,
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
        db_session.add(assessment)
        db_session.flush()
        ticket.current_assessment_id = assessment.id
        opportunity.assessment_id = assessment.id

        solution = PresaleSolution(
            solution_no=f"SOL-PRE-{unique}",
            name=f"签约前售前技术方案-{unique}",
            solution_type="CUSTOM",
            industry="电子制造",
            test_type="FCT",
            ticket_id=ticket.id,
            project_id=None,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            requirement_summary="签约前需求已冻结",
            solution_overview="FCT/EOL 测试设备方案",
            estimated_cost=Decimal("430000"),
            suggested_price=Decimal("680000"),
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        contract = Contract(
            contract_code=f"CTPRE{unique[:6]}",
            contract_name=f"签约售前回填合同-{unique}",
            contract_type="sales",
            customer=customer,
            opportunity=opportunity,
            quote_id=quote_version.id,
            total_amount=Decimal("680000"),
            status="approved",
            sales_owner_id=admin_user.id,
        )
        db_session.add_all([solution, contract])
        db_session.commit()

        try:
            response = client.post(
                (
                    f"{prefix}/sales/contracts/{contract.id}/sign"
                    "?auto_generate_payment_plans=false"
                ),
                headers=headers,
                json={
                    "sign_date": "2026-06-08",
                    "signed_by": "张总",
                    "customer_signed_by": "李经理",
                    "auto_create_project": True,
                },
            )
            assert response.status_code == 200, response.text
            data = response.json()["data"]
            project = db_session.get(Project, data["project_id"])
            assert project is not None

            db_session.expire_all()
            refreshed_ticket = db_session.get(PresaleSupportTicket, ticket.id)
            refreshed_solution = db_session.get(PresaleSolution, solution.id)
            assert refreshed_ticket.project_id == project.id
            assert refreshed_solution.project_id == project.id

            tickets_response = client.get(
                f"{prefix}/presale/tickets",
                params={"project_id": project.id},
                headers=headers,
            )
            assert tickets_response.status_code == 200, tickets_response.text
            assert [item["id"] for item in tickets_response.json()["items"]] == [ticket.id]

            solutions_response = client.get(
                f"{prefix}/presale/proposals/solutions",
                params={"project_id": project.id},
                headers=headers,
            )
            assert solutions_response.status_code == 200, solutions_response.text
            assert [item["id"] for item in solutions_response.json()["items"]] == [solution.id]
        finally:
            ticket_to_cleanup = db_session.get(PresaleSupportTicket, ticket.id)
            opportunity_to_cleanup = db_session.get(Opportunity, opportunity.id)
            quote_to_cleanup = db_session.get(Quote, quote.id)
            if ticket_to_cleanup:
                ticket_to_cleanup.current_assessment_id = None
            if opportunity_to_cleanup:
                opportunity_to_cleanup.assessment_id = None
            if quote_to_cleanup:
                quote_to_cleanup.current_version_id = None
            db_session.flush()
            db_session.query(Project).filter(Project.contract_id == contract.id).delete(
                synchronize_session=False
            )
            db_session.query(PresaleSolution).filter(PresaleSolution.id == solution.id).delete(
                synchronize_session=False
            )
            db_session.query(TechnicalAssessment).filter(
                TechnicalAssessment.id == assessment.id
            ).delete(synchronize_session=False)
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id == ticket.id
            ).delete(synchronize_session=False)
            db_session.query(Contract).filter(Contract.id == contract.id).delete(
                synchronize_session=False
            )
            db_session.query(QuoteVersion).filter(QuoteVersion.id == quote_version.id).delete(
                synchronize_session=False
            )
            db_session.query(Quote).filter(Quote.id == quote.id).delete(
                synchronize_session=False
            )
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete(
                synchronize_session=False
            )
            db_session.query(Lead).filter(Lead.id == lead.id).delete(synchronize_session=False)
            db_session.query(Customer).filter(Customer.id == customer.id).delete(
                synchronize_session=False
            )
            db_session.commit()

    def test_contract_project_binds_only_quote_selected_presale_solution(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """同一商机多版方案时，签约建项只能绑定报价实际选用的售前方案。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-QSEL-{unique}",
            customer_name=f"报价方案选择客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        opportunity = Opportunity(
            opp_code=f"OPPQSE{unique[:6]}",
            customer=customer,
            opp_name=f"报价方案选择商机-{unique}",
            project_type="FCT",
            equipment_type="EOL",
            stage="QUOTATION",
            probability=80,
            est_amount=Decimal("680000"),
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add_all([customer, opportunity])
        db_session.flush()

        first_ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-QSEL-A-{unique}",
            title=f"未选用售前方案工单-{unique}",
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
        selected_ticket = PresaleSupportTicket(
            ticket_no=f"TICKET-QSEL-B-{unique}",
            title=f"报价选用售前方案工单-{unique}",
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
        db_session.add_all([first_ticket, selected_ticket])
        db_session.flush()

        unselected_solution = PresaleSolution(
            solution_no=f"SOL-QSEL-A-{unique}",
            name=f"未选用售前方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=first_ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            estimated_cost=Decimal("360000"),
            suggested_price=Decimal("620000"),
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        selected_solution = PresaleSolution(
            solution_no=f"SOL-QSEL-B-{unique}",
            name=f"报价实际选用方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=selected_ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            estimated_cost=Decimal("410000"),
            suggested_price=Decimal("680000"),
            estimated_duration=55,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add_all([unselected_solution, selected_solution])
        db_session.commit()

        quote_response = client.post(
            f"{prefix}/sales/quotes",
            headers=headers,
            json={
                "quote_code": f"QQSEL{unique[:6]}",
                "opportunity_id": opportunity.id,
                "customer_id": customer.id,
                "solution_id": selected_solution.id,
                "valid_until": datetime.now().date().isoformat(),
                "version": {"version_no": "V1", "items": []},
            },
        )
        assert quote_response.status_code == 201, quote_response.text
        quote_payload = quote_response.json()

        contract = Contract(
            contract_code=f"CTQSEL{unique[:6]}",
            contract_name=f"报价方案选择合同-{unique}",
            contract_type="sales",
            customer=customer,
            opportunity=opportunity,
            quote_id=quote_payload["current_version_id"],
            total_amount=Decimal("680000"),
            status="approved",
            sales_owner_id=admin_user.id,
        )
        db_session.add(contract)
        db_session.commit()

        try:
            response = client.post(
                (
                    f"{prefix}/sales/contracts/{contract.id}/sign"
                    "?auto_generate_payment_plans=false"
                ),
                headers=headers,
                json={
                    "sign_date": datetime.now().date().isoformat(),
                    "signed_by": "张总",
                    "customer_signed_by": "李经理",
                    "auto_create_project": True,
                },
            )
            assert response.status_code == 200, response.text
            project_id = response.json()["data"]["project_id"]

            db_session.expire_all()
            refreshed_unselected = db_session.get(PresaleSolution, unselected_solution.id)
            refreshed_selected = db_session.get(PresaleSolution, selected_solution.id)
            refreshed_first_ticket = db_session.get(PresaleSupportTicket, first_ticket.id)
            refreshed_selected_ticket = db_session.get(PresaleSupportTicket, selected_ticket.id)

            assert refreshed_selected.project_id == project_id
            assert refreshed_selected_ticket.project_id == project_id
            assert refreshed_unselected.project_id is None
            assert refreshed_first_ticket.project_id is None

            solutions_response = client.get(
                f"{prefix}/presale/proposals/solutions",
                params={"project_id": project_id},
                headers=headers,
            )
            assert solutions_response.status_code == 200, solutions_response.text
            assert [item["id"] for item in solutions_response.json()["items"]] == [
                selected_solution.id
            ]
        finally:
            quote = db_session.get(Quote, quote_payload["id"])
            if quote:
                quote.current_version_id = None
            db_session.flush()
            db_session.query(Project).filter(Project.contract_id == contract.id).delete(
                synchronize_session=False
            )
            db_session.query(Contract).filter(Contract.id == contract.id).delete(
                synchronize_session=False
            )
            db_session.query(QuoteVersion).filter(
                QuoteVersion.id == quote_payload["current_version_id"]
            ).delete(synchronize_session=False)
            db_session.query(Quote).filter(Quote.id == quote_payload["id"]).delete(
                synchronize_session=False
            )
            db_session.query(PresaleSolution).filter(
                PresaleSolution.id.in_([unselected_solution.id, selected_solution.id])
            ).delete(synchronize_session=False)
            db_session.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.id.in_([first_ticket.id, selected_ticket.id])
            ).delete(synchronize_session=False)
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete(
                synchronize_session=False
            )
            db_session.query(Customer).filter(Customer.id == customer.id).delete(
                synchronize_session=False
            )
            db_session.commit()

    def test_legacy_create_project_endpoint_preserves_sales_presale_context(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        """旧合同转项目入口也不能生成缺销售/售前上下文的项目。"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-LCP-{unique}",
            customer_name=f"旧入口建项客户-{unique}",
            industry="新能源",
            contact_person="王工",
            contact_phone="13800138000",
            created_by=admin_user.id,
        )
        lead = Lead(
            lead_code=f"LEADLCP{unique[:6]}",
            customer_name=customer.customer_name,
            industry="新能源",
            demand_summary="旧合同转项目入口也要保留线索与售前上下文",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, lead])
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPPLCP{unique[:6]}",
            lead_id=lead.id,
            customer=customer,
            opp_name=f"旧入口建项商机-{unique}",
            project_type="ATE",
            equipment_type="PACK_EOL",
            stage="WON",
            probability=95,
            est_amount=Decimal("880000"),
            est_margin=Decimal("40.90"),
            acceptance_basis="按冻结需求和终验清单验收",
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        quote = Quote(
            quote_code=f"QLCP{unique[:6]}",
            opportunity=opportunity,
            customer=customer,
            status="APPROVED",
            owner_id=admin_user.id,
        )
        db_session.add_all([opportunity, quote])
        db_session.flush()

        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("880000"),
            cost_total=Decimal("520000"),
            gross_margin=Decimal("40.90"),
            created_by=admin_user.id,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id

        contract = Contract(
            contract_code=f"CTLCP{unique[:6]}",
            contract_name=f"旧入口建项合同-{unique}",
            contract_type="sales",
            customer=customer,
            opportunity=opportunity,
            quote_id=quote_version.id,
            total_amount=Decimal("880000"),
            contract_subject="交付一套 PACK EOL 测试线，按终验标准验收",
            payment_terms="30-60-10",
            status="SIGNED",
            sales_owner_id=admin_user.id,
        )
        db_session.add(contract)
        db_session.flush()

        deliverable = ContractDeliverable(
            contract_id=contract.id,
            deliverable_name="PACK EOL 测试线",
            deliverable_type="EQUIPMENT",
            required_for_payment=True,
        )
        db_session.add(deliverable)
        db_session.commit()

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/{contract.id}/create-project",
            headers=headers,
        )

        try:
            assert response.status_code == 200, response.text
            data = response.json()
            project = db_session.get(Project, data["project_id"])
            assert project is not None
            assert project.project_code == data["project_code"]
            assert project.contract_id == contract.id
            assert project.customer_id == customer.id
            assert project.lead_id == lead.id
            assert project.opportunity_id == opportunity.id
            assert project.contract_no == contract.contract_code
            assert float(project.contract_amount) == 880000.0
            assert float(project.budget_amount) == 520000.0
            assert project.project_type == "ATE"
            assert project.product_category == "PACK_EOL"
            assert project.industry == "新能源"

            db_session.refresh(contract)
            assert contract.project_id == project.id
        finally:
            db_session.query(Project).filter(Project.contract_id == contract.id).delete(
                synchronize_session=False
            )
            db_session.query(ContractDeliverable).filter(
                ContractDeliverable.contract_id == contract.id
            ).delete(synchronize_session=False)
            db_session.query(Contract).filter(Contract.id == contract.id).delete(
                synchronize_session=False
            )
            quote.current_version_id = None
            db_session.flush()
            db_session.query(QuoteVersion).filter(QuoteVersion.id == quote_version.id).delete(
                synchronize_session=False
            )
            db_session.query(Quote).filter(Quote.id == quote.id).delete(
                synchronize_session=False
            )
            db_session.query(Opportunity).filter(Opportunity.id == opportunity.id).delete(
                synchronize_session=False
            )
            db_session.query(Lead).filter(Lead.id == lead.id).delete(synchronize_session=False)
            db_session.query(Customer).filter(Customer.id == customer.id).delete(
                synchronize_session=False
            )
            db_session.commit()

    def test_get_contract_detail(self, client: TestClient, admin_token: str):
        """测试获取合同详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/contracts/1", headers=headers)

        if response.status_code in [404, 422]:
            pytest.skip("No contract data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_contract(self, client: TestClient, admin_token: str):
        """测试更新合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {"remarks": "更新后的备注", "warranty_period": "24个月"}

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/contracts/1", headers=headers, json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Contract API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_contract(self, client: TestClient, admin_token: str):
        """测试删除合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(f"{settings.API_V1_PREFIX}/sales/contracts/999", headers=headers)

        if response.status_code == 404:
            pytest.skip("Contract API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_contract_approval_submit(self, client: TestClient, admin_token: str):
        """测试提交合同审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/submit", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_approval_approve(self, client: TestClient, admin_token: str):
        """测试审批通过合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        approval_data = {"action": "approve", "comments": "审批通过"}

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/approve",
            headers=headers,
            json=approval_data,
        )

        if response.status_code == 404:
            pytest.skip("Contract approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_signing(self, client: TestClient, admin_token: str):
        """测试合同签署"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        signing_data = {
            "sign_date": datetime.now().strftime("%Y-%m-%d"),
            "signed_by": "张总",
            "customer_signed_by": "李经理",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/sign", headers=headers, json=signing_data
        )

        if response.status_code == 404:
            pytest.skip("Contract signing API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_archive(self, client: TestClient, admin_token: str):
        """测试合同归档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contracts/1/archive", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract archive API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_contracts_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/?status=signed", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_contracts_by_customer(self, client: TestClient, admin_token: str):
        """测试按客户过滤合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/?customer_id=1", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract filter API not implemented")

        assert response.status_code == 200, response.text

    def test_expiring_contracts(self, client: TestClient, admin_token: str):
        """测试即将到期的合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/expiring?days=30", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Expiring contracts API not implemented")

        assert response.status_code == 200, response.text

    def test_contract_statistics(self, client: TestClient, admin_token: str):
        """测试合同统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contracts/statistics", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Contract statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_contract_export(self, client: TestClient, admin_token: str):
        """测试导出合同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(f"{settings.API_V1_PREFIX}/sales/contracts/1/export", headers=headers)

        if response.status_code == 404:
            pytest.skip("Contract export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_contract_unauthorized(self, client: TestClient):
        """测试未授权访问合同"""
        response = client.get(f"{settings.API_V1_PREFIX}/sales/contracts/")

        assert response.status_code in [401, 403], response.text

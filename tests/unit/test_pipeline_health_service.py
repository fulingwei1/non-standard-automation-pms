# -*- coding: utf-8 -*-
"""
全链条健康度计算服务测试
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.sales import Contract, Invoice, Lead, Opportunity, Quote
from app.services.pipeline_health_service import PipelineHealthService


@pytest.fixture
def pipeline_health_service(db_session: Session):
    return PipelineHealthService(db_session)


@pytest.fixture
def test_sales_user(db_session: Session):
    from tests.conftest import _get_or_create_user

    user = _get_or_create_user(
        db_session,
        username="pipeline_test_user",
        password="test123",
        real_name="管道测试用户",
        department="销售部",
        employee_role="SALES",
    )

    db_session.flush()
    return user


class TestPipelineHealthService:
    def test_init(self, db_session: Session):
        service = PipelineHealthService(db_session)
        assert service.db is db_session
        assert hasattr(service, "HEALTH_THRESHOLDS")

    def test_calculate_lead_health_h1(self, pipeline_health_service, test_sales_user):
        lead = Lead(
            owner_id=test_sales_user.id,
            lead_name="测试线索",
            status="NEW",
            created_at=datetime.now() - timedelta(days=3),
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_lead_health(lead.id)
        assert health == "H1"
        assert "最近跟进" in details or "健康" in details

    def test_calculate_lead_health_h2(self, pipeline_health_service, test_sales_user):
        lead = Lead(
            owner_id=test_sales_user.id,
            lead_name="测试线索2",
            status="NEW",
            created_at=datetime.now() - timedelta(days=10),
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_lead_health(lead.id)
        assert health in ["H1", "H2"]

    def test_calculate_lead_health_h3(self, pipeline_health_service, test_sales_user):
        lead = Lead(
            owner_id=test_sales_user.id,
            lead_name="测试线索3",
            status="NEW",
            created_at=datetime.now() - timedelta(days=35),
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_lead_health(lead.id)
        assert health == "H3"

    def test_calculate_lead_health_converted(
        self, pipeline_health_service, test_sales_user
    ):
        lead = Lead(
            owner_id=test_sales_user.id,
            lead_name="已转换线索",
            status="CONVERTED",
            created_at=datetime.now() - timedelta(days=5),
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_lead_health(lead.id)
        assert health in ["H1", "H4"]

    def test_calculate_opportunity_health_h1(
        self, pipeline_health_service, test_sales_user
    ):
        opp = Opportunity(
            owner_id=test_sales_user.id,
            opportunity_name="测试商机",
            status="NEGOTIATING",
            created_at=datetime.now() - timedelta(days=7),
            updated_at=datetime.now() - timedelta(days=5),
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_opportunity_health(opp.id)
        assert health == "H1"

    def test_calculate_opportunity_health_h2(
        self, pipeline_health_service, test_sales_user
    ):
        opp = Opportunity(
            owner_id=test_sales_user.id,
            opportunity_name="测试商机2",
            status="NEGOTIATING",
            created_at=datetime.now() - timedelta(days=20),
            updated_at=datetime.now() - timedelta(days=18),
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_opportunity_health(opp.id)
        assert health in ["H1", "H2"]

    def test_calculate_opportunity_health_h3(
        self, pipeline_health_service, test_sales_user
    ):
        opp = Opportunity(
            owner_id=test_sales_user.id,
            opportunity_name="测试商机3",
            status="NEGOTIATING",
            created_at=datetime.now() - timedelta(days=70),
            updated_at=datetime.now() - timedelta(days=68),
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_opportunity_health(opp.id)
        assert health == "H3"

    def test_calculate_opportunity_health_won(
        self, pipeline_health_service, test_sales_user
    ):
        opp = Opportunity(
            owner_id=test_sales_user.id,
            opportunity_name="已赢商机",
            status="WON",
            created_at=datetime.now() - timedelta(days=10),
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_opportunity_health(opp.id)
        assert health in ["H1", "H4"]

    def test_calculate_quote_health_h1(self, pipeline_health_service, test_sales_user):
        quote = Quote(
            owner_id=test_sales_user.id,
            quote_code="Q001",
            quote_name="测试报价",
            status="PENDING",
            created_at=datetime.now() - timedelta(days=10),
        )
        pipeline_health_service.db.add(quote)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_quote_health(quote.id)
        assert health in ["H1", "H2"]

    def test_calculate_quote_health_h3(self, pipeline_health_service, test_sales_user):
        quote = Quote(
            owner_id=test_sales_user.id,
            quote_code="Q002",
            quote_name="测试报价2",
            status="PENDING",
            created_at=datetime.now() - timedelta(days=100),
        )
        pipeline_health_service.db.add(quote)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_quote_health(quote.id)
        assert health == "H3"

    def test_calculate_quote_health_approved(
        self, pipeline_health_service, test_sales_user
    ):
        quote = Quote(
            owner_id=test_sales_user.id,
            quote_code="Q003",
            quote_name="已审批报价",
            status="APPROVED",
            created_at=datetime.now() - timedelta(days=5),
        )
        pipeline_health_service.db.add(quote)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_quote_health(quote.id)
        assert health in ["H1", "H4"]

    def test_calculate_contract_health_normal(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        contract = Contract(
            owner_id=test_sales_user.id,
            customer_id=test_customer.id,
            contract_no="C001",
            contract_name="测试合同",
            contract_amount=Decimal("1000000"),
            status="ACTIVE",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        pipeline_health_service.db.add(contract)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_contract_health(contract.id)
        assert health == "H1"

    def test_calculate_contract_health_delayed(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        contract = Contract(
            owner_id=test_sales_user.id,
            customer_id=test_customer.id,
            contract_no="C002",
            contract_name="延期合同",
            contract_amount=Decimal("1000000"),
            status="DELAYED",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=30),
        )
        pipeline_health_service.db.add(contract)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_contract_health(contract.id)
        assert health in ["H2", "H3"]

    def test_calculate_payment_health_on_time(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        contract = Contract(
            owner_id=test_sales_user.id,
            customer_id=test_customer.id,
            contract_no="C003",
            contract_amount=Decimal("1000000"),
            status="ACTIVE",
        )
        pipeline_health_service.db.add(contract)
        pipeline_health_service.db.commit()

        invoice = Invoice(
            contract_id=contract.id,
            invoice_no="INV001",
            invoice_amount=Decimal("100000"),
            payment_status="PAID",
            due_date=date.today() - timedelta(days=10),
            paid_date=date.today() - timedelta(days=5),
        )
        pipeline_health_service.db.add(invoice)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_payment_health(invoice.id)
        assert health == "H1"

    def test_calculate_payment_health_overdue(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        contract = Contract(
            owner_id=test_sales_user.id,
            customer_id=test_customer.id,
            contract_no="C004",
            contract_amount=Decimal("1000000"),
            status="ACTIVE",
        )
        pipeline_health_service.db.add(contract)
        pipeline_health_service.db.commit()

        invoice = Invoice(
            contract_id=contract.id,
            invoice_no="INV002",
            invoice_amount=Decimal("100000"),
            payment_status="UNPAID",
            due_date=date.today() - timedelta(days=15),
        )
        pipeline_health_service.db.add(invoice)
        pipeline_health_service.db.commit()

        health, details = pipeline_health_service.calculate_payment_health(invoice.id)
        assert health in ["H2", "H3"]

    def test_calculate_overall_pipeline_health(
        self, pipeline_health_service, test_sales_user
    ):
        result = pipeline_health_service.calculate_overall_pipeline_health(
            user_id=test_sales_user.id
        )

        assert isinstance(result, dict)
        assert "LEAD" in result
        assert "OPPORTUNITY" in result
        assert "QUOTE" in result
        assert "CONTRACT" in result
        assert "PAYMENT" in result

        assert all("health" in v for v in result.values())
        assert all("count" in v for v in result.values())

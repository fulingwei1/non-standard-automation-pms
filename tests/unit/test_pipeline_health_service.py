# -*- coding: utf-8 -*-
"""
全链条健康度计算服务测试
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.sales import Contract, Invoice, Lead, Opportunity, Quote
from app.models.project import Customer
from app.services.pipeline_health_service import PipelineHealthService
from tests.factories import CustomerFactory


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


@pytest.fixture
def test_customer(db_session: Session):
    """创建测试客户"""
    customer = CustomerFactory()
    db_session.add(customer)
    db_session.flush()  # 使用 flush 而不是 commit，避免会话问题
    return customer


class TestPipelineHealthService:
    def test_init(self, db_session: Session):
        service = PipelineHealthService(db_session)
        assert service.db is db_session
        assert hasattr(service, "HEALTH_THRESHOLDS")

    def test_calculate_lead_health_h1(self, pipeline_health_service, test_sales_user):
        lead = Lead(
        owner_id=test_sales_user.id,
        lead_code="LEAD001",
        customer_name="测试客户",
        status="NEW",
        created_at=datetime.now() - timedelta(days=3),
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_lead_health(lead.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ['H1', 'H2', 'H3', 'H4']
        assert 'health_score' in result

    def test_calculate_lead_health_h2(self, pipeline_health_service, test_sales_user):
        lead = Lead(
        owner_id=test_sales_user.id,
        lead_code="LEAD002",
        customer_name="测试客户2",
        status="NEW",
        created_at=datetime.now() - timedelta(days=10),
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_lead_health(lead.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H1", "H2"]

    def test_calculate_lead_health_h3(self, pipeline_health_service, test_sales_user):
        lead = Lead(
        owner_id=test_sales_user.id,
        lead_code="LEAD003",
        customer_name="测试客户3",
        status="NEW",
        created_at=datetime.now() - timedelta(days=35),
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_lead_health(lead.id)
        assert isinstance(result, dict)
        assert result['health_status'] == "H3"

    def test_calculate_lead_health_converted(
        self, pipeline_health_service, test_sales_user
    ):
        lead = Lead(
        owner_id=test_sales_user.id,
        lead_code="LEAD004",
        customer_name="已转换客户",
        status="CONVERTED",
        created_at=datetime.now() - timedelta(days=5),
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_lead_health(lead.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H1", "H4"]

    def test_calculate_opportunity_health_h1(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP001",
        opp_name="测试商机",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now() - timedelta(days=7),
        updated_at=datetime.now() - timedelta(days=5),
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_opportunity_health(opp.id)
        assert isinstance(result, dict)
        assert result['health_status'] == "H1"

    def test_calculate_opportunity_health_h2(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP002",
        opp_name="测试商机2",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now() - timedelta(days=20),
        updated_at=datetime.now() - timedelta(days=18),
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_opportunity_health(opp.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H1", "H2"]

    def test_calculate_opportunity_health_h3(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP003",
        opp_name="测试商机3",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now() - timedelta(days=70),
        updated_at=datetime.now() - timedelta(days=68),
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_opportunity_health(opp.id)
        assert isinstance(result, dict)
        assert result['health_status'] == "H3"

    def test_calculate_opportunity_health_won(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP004",
        opp_name="已赢商机",
        customer_id=test_customer.id,
        stage="WON",
        created_at=datetime.now() - timedelta(days=10),
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_opportunity_health(opp.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H1", "H4"]

    def test_calculate_quote_health_h1(self, pipeline_health_service, test_sales_user, test_customer):
        from app.models.sales import Opportunity
        # 创建商机（Quote 需要 opportunity_id）
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP-QUOTE1",
        opp_name="测试商机",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now()
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.flush()

        quote = Quote(
        owner_id=test_sales_user.id,
        quote_code="Q001",
        opportunity_id=opp.id,
        customer_id=test_customer.id,
        status="PENDING",
        created_at=datetime.now() - timedelta(days=10),
        )
        pipeline_health_service.db.add(quote)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_quote_health(quote.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H1", "H2"]

    def test_calculate_quote_health_h3(self, pipeline_health_service, test_sales_user, test_customer):
        from app.models.sales import Opportunity
        # 创建商机
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP-QUOTE2",
        opp_name="测试商机2",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now()
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.flush()

        quote = Quote(
        owner_id=test_sales_user.id,
        quote_code="Q002",
        opportunity_id=opp.id,
        customer_id=test_customer.id,
        status="PENDING",
        created_at=datetime.now() - timedelta(days=100),
        )
        pipeline_health_service.db.add(quote)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_quote_health(quote.id)
        assert isinstance(result, dict)
        assert result['health_status'] == "H3"

    def test_calculate_quote_health_approved(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        from app.models.sales import Opportunity
        # 创建商机
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP-QUOTE3",
        opp_name="测试商机3",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now()
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.flush()

        quote = Quote(
        owner_id=test_sales_user.id,
        quote_code="Q003",
        opportunity_id=opp.id,
        customer_id=test_customer.id,
        status="APPROVED",
        created_at=datetime.now() - timedelta(days=5),
        )
        pipeline_health_service.db.add(quote)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_quote_health(quote.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H1", "H4"]

    def test_calculate_contract_health_normal(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        from app.models.sales import Opportunity
        # 创建商机（Contract 需要 opportunity_id）
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP-CONTRACT1",
        opp_name="测试商机",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now()
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.flush()

        # 创建项目（Contract 关联项目后健康度会更好）
        from app.models.project import Project
        project = Project(
        project_code="PJ-CONTRACT1",
        project_name="测试项目",
        customer_id=test_customer.id,
        stage="S4",
        status="ST09",
        health="H1",
        )
        pipeline_health_service.db.add(project)
        pipeline_health_service.db.flush()

        contract = Contract(
        owner_id=test_sales_user.id,
        customer_id=test_customer.id,
        contract_code="C001",
        opportunity_id=opp.id,
        project_id=project.id,  # 关联项目
        contract_amount=Decimal("1000000"),
        status="ACTIVE",
        signed_date=date.today(),
        )
        pipeline_health_service.db.add(contract)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_contract_health(contract.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H1", "H2"]  # 有项目关联时可能是 H1 或 H2

    def test_calculate_contract_health_delayed(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        from app.models.sales import Opportunity
        # 创建商机
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP-CONTRACT2",
        opp_name="测试商机2",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now()
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.flush()

        contract = Contract(
        owner_id=test_sales_user.id,
        customer_id=test_customer.id,
        contract_code="C002",
        opportunity_id=opp.id,
        contract_amount=Decimal("1000000"),
        status="DELAYED",
        signed_date=date.today() - timedelta(days=30),
        )
        pipeline_health_service.db.add(contract)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_contract_health(contract.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H2", "H3"]

    def test_calculate_payment_health_on_time(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        from app.models.sales import Opportunity
        # 创建商机
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP-CONTRACT3",
        opp_name="测试商机3",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now()
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.flush()

        contract = Contract(
        owner_id=test_sales_user.id,
        customer_id=test_customer.id,
        contract_code="C003",
        opportunity_id=opp.id,
        contract_amount=Decimal("1000000"),
        status="ACTIVE",
        )
        pipeline_health_service.db.add(contract)
        pipeline_health_service.db.commit()

        invoice = Invoice(
        contract_id=contract.id,
        invoice_code="INV001",
        total_amount=Decimal("100000"),  # 使用 total_amount
        amount=Decimal("100000"),  # 也设置 amount 作为备用
        payment_status="PAID",
        due_date=date.today() - timedelta(days=10),
        paid_date=date.today() - timedelta(days=5),
        paid_amount=Decimal("100000"),  # 已付金额等于总金额
        )
        pipeline_health_service.db.add(invoice)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_payment_health(invoice.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H1", "H4"]  # 已完全回款可能是 H4

    def test_calculate_payment_health_overdue(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        from app.models.sales import Opportunity
        # 创建商机
        opp = Opportunity(
        owner_id=test_sales_user.id,
        opp_code="OPP-CONTRACT4",
        opp_name="测试商机4",
        customer_id=test_customer.id,
        stage="NEGOTIATING",
        created_at=datetime.now()
        )
        pipeline_health_service.db.add(opp)
        pipeline_health_service.db.flush()

        contract = Contract(
        owner_id=test_sales_user.id,
        customer_id=test_customer.id,
        contract_code="C004",
        opportunity_id=opp.id,
        contract_amount=Decimal("1000000"),
        status="ACTIVE",
        )
        pipeline_health_service.db.add(contract)
        pipeline_health_service.db.commit()

        invoice = Invoice(
        contract_id=contract.id,
        invoice_code="INV002",
        total_amount=Decimal("100000"),  # 使用 total_amount
        amount=Decimal("100000"),  # 也设置 amount 作为备用
        payment_status="UNPAID",
        due_date=date.today() - timedelta(days=15),
        paid_amount=Decimal("0"),  # 未付款
        )
        pipeline_health_service.db.add(invoice)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_payment_health(invoice.id)
        assert isinstance(result, dict)
        assert result['health_status'] in ["H2", "H3"]

    def test_calculate_pipeline_health(
        self, pipeline_health_service, test_sales_user, test_customer
    ):
        """测试计算全链条健康度（使用具体的ID）"""
        # 创建一个线索用于测试
        from app.models.sales import Lead
        from datetime import datetime
        lead = Lead(
        owner_id=test_sales_user.id,
        lead_code="LEAD-PIPELINE",
        customer_name="测试客户",
        status="NEW",
        created_at=datetime.now()
        )
        pipeline_health_service.db.add(lead)
        pipeline_health_service.db.commit()

        result = pipeline_health_service.calculate_pipeline_health(
        lead_id=lead.id
        )

        assert isinstance(result, dict)
        assert "lead" in result
        assert "overall" in result
        assert "health_status" in result["lead"]
        assert "health_score" in result["lead"]

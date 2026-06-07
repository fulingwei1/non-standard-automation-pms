"""
场景4：报价 → 合同签订 → 项目启动流程

测试从销售报价到项目启动的业务流程
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.project import Customer, Project
from app.models.sales.contracts import Contract, ContractAmendment
from app.models.sales.leads import Opportunity
from app.models.sales.quotes import Quote, QuoteVersion
from app.services.status_transition_service import StatusTransitionService


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:6].upper()}"


class TestQuoteToContractFlow:
    """报价到合同流程测试"""

    @pytest.fixture
    def flow_customer(self, db_session: Session):
        customer = Customer(
            customer_code=_code("CUST-FLOW"),
            customer_name="流程测试客户",
            contact_person="赵经理",
            contact_phone="13600136000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        return customer

    def _create_opportunity(
        self,
        db_session: Session,
        customer: Customer,
        *,
        amount: Decimal,
        suffix: str = "FLOW",
    ) -> Opportunity:
        opportunity = Opportunity(
            opp_code=_code(f"OPP{suffix}"),
            customer_id=customer.id,
            opp_name=f"{customer.customer_name}-{suffix}商机",
            project_type="AUTO_LINE",
            equipment_type="ICT",
            stage="PROPOSAL",
            probability=70,
            est_amount=amount,
            expected_close_date=date.today() + timedelta(days=30),
        )
        db_session.add(opportunity)
        db_session.flush()
        return opportunity

    def _create_quote(
        self,
        db_session: Session,
        customer: Customer,
        *,
        amount: Decimal,
        status: str = "DRAFT",
        suffix: str = "FLOW",
    ) -> tuple[Quote, QuoteVersion]:
        opportunity = self._create_opportunity(
            db_session, customer, amount=amount, suffix=suffix
        )
        quote = Quote(
            quote_code=_code(f"QT{suffix}"),
            opportunity_id=opportunity.id,
            customer_id=customer.id,
            valid_until=date.today() + timedelta(days=30),
            status=status,
        )
        db_session.add(quote)
        db_session.flush()

        version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=amount,
            cost_total=amount * Decimal("0.62"),
            gross_margin=Decimal("38.00"),
        )
        db_session.add(version)
        db_session.flush()
        quote.current_version_id = version.id
        db_session.commit()
        db_session.refresh(quote)
        db_session.refresh(version)
        return quote, version

    def _create_contract(
        self,
        db_session: Session,
        customer: Customer,
        *,
        amount: Decimal,
        quote_version: QuoteVersion | None = None,
        opportunity_id: int | None = None,
        status: str = "DRAFT",
        suffix: str = "FLOW",
    ) -> Contract:
        contract = Contract(
            contract_code=_code(f"CT{suffix}"),
            contract_name=f"{customer.customer_name}-{suffix}合同",
            contract_type="sales",
            customer_id=customer.id,
            opportunity_id=opportunity_id,
            quote_id=quote_version.id if quote_version else None,
            total_amount=amount,
            signing_date=date.today() if status == "SIGNED" else None,
            effective_date=date.today() if status == "SIGNED" else None,
            expiry_date=date.today() + timedelta(days=365),
            status=status,
            payment_terms="30-30-30-10",
            delivery_terms="客户现场安装",
        )
        db_session.add(contract)
        db_session.commit()
        db_session.refresh(contract)
        return contract

    def test_01_create_sales_quote(self, db_session: Session, flow_customer: Customer):
        """测试1：创建销售报价"""
        quote, version = self._create_quote(
            db_session,
            flow_customer,
            amount=Decimal("800000.00"),
            status="DRAFT",
            suffix="FLOW1",
        )

        assert quote.id is not None
        assert quote.status == "DRAFT"
        assert quote.current_version_id == version.id
        assert version.total_price == Decimal("800000.00")

    def test_02_customer_accepts_quote(self, db_session: Session, flow_customer: Customer):
        """测试2：客户接受报价"""
        quote, _ = self._create_quote(
            db_session,
            flow_customer,
            amount=Decimal("750000.00"),
            status="APPROVED",
            suffix="FLOW2",
        )

        quote.status = "ACCEPTED"
        db_session.commit()

        assert quote.status == "ACCEPTED"

    def test_03_create_contract_from_quote(self, db_session: Session, flow_customer: Customer):
        """测试3：从报价创建合同"""
        quote, version = self._create_quote(
            db_session,
            flow_customer,
            amount=Decimal("900000.00"),
            status="ACCEPTED",
            suffix="FLOW3",
        )

        contract = self._create_contract(
            db_session,
            flow_customer,
            amount=version.total_price,
            quote_version=version,
            opportunity_id=quote.opportunity_id,
            suffix="FLOW3",
        )

        assert contract.quote_id == version.id
        assert contract.opportunity_id == quote.opportunity_id
        assert contract.total_amount == version.total_price

    def test_04_negotiate_contract_terms(self, db_session: Session, flow_customer: Customer):
        """测试4：合同条款协商"""
        contract = self._create_contract(
            db_session,
            flow_customer,
            amount=Decimal("850000.00"),
            suffix="FLOW4",
        )

        contract.payment_terms = "预付20%，发货前40%，验收后40%"
        contract.delivery_terms = "合同签订后90天客户现场安装"
        db_session.commit()

        assert "20%" in contract.payment_terms
        assert "90天" in contract.delivery_terms

    def test_05_sign_contract(self, db_session: Session, flow_customer: Customer):
        """测试5：签署合同"""
        contract = self._create_contract(
            db_session,
            flow_customer,
            amount=Decimal("920000.00"),
            suffix="FLOW5",
        )

        contract.status = "SIGNED"
        contract.signing_date = date.today()
        db_session.commit()

        assert contract.status == "SIGNED"
        assert contract.signing_date is not None

    def test_06_create_project_from_contract(self, db_session: Session, flow_customer: Customer):
        """测试6：从合同创建项目"""
        quote, version = self._create_quote(
            db_session,
            flow_customer,
            amount=Decimal("1000000.00"),
            status="ACCEPTED",
            suffix="FLOW6",
        )
        contract = self._create_contract(
            db_session,
            flow_customer,
            amount=version.total_price,
            quote_version=version,
            opportunity_id=quote.opportunity_id,
            status="SIGNED",
            suffix="FLOW6",
        )

        project = StatusTransitionService(db_session).handle_contract_signed(
            contract.id, auto_create_project=True
        )
        db_session.refresh(contract)

        assert project is not None
        assert project.contract_id == contract.id
        assert project.contract_amount == contract.total_amount
        assert contract.project_id == project.id

    def test_07_kickoff_project(self, db_session: Session, flow_customer: Customer):
        """测试7：项目启动"""
        project = Project(
            project_code=_code("PJ-FLOW7"),
            project_name="测试项目",
            customer_id=flow_customer.id,
            customer_name=flow_customer.customer_name,
            stage="S1",
            status="ST01",
        )
        db_session.add(project)
        db_session.commit()

        project.status = "ST02"
        project.actual_start_date = date.today()
        db_session.commit()

        assert project.status == "ST02"

    def test_08_handle_contract_amendment(self, db_session: Session, flow_customer: Customer):
        """测试8：处理合同变更"""
        contract = self._create_contract(
            db_session,
            flow_customer,
            amount=Decimal("700000.00"),
            status="SIGNED",
            suffix="AMEND",
        )

        amendment = ContractAmendment(
            contract_id=contract.id,
            amendment_no=_code("AMD-FLOW"),
            amendment_type="AMOUNT",
            title="客户增加功能需求",
            description="新增扫码追溯和MES对接范围",
            reason="客户现场工艺调整",
            old_value="700000.00",
            new_value="850000.00",
            amount_change=Decimal("150000.00"),
            requestor_id=1,
            request_date=date.today(),
            status="PENDING",
        )
        db_session.add(amendment)
        db_session.commit()

        assert amendment.contract_id == contract.id
        assert amendment.amount_change == Decimal("150000.00")

    def test_09_track_quote_to_contract_conversion_rate(
        self, db_session: Session, flow_customer: Customer
    ):
        """测试9：跟踪报价转合同转化率"""
        quotes: list[tuple[Quote, QuoteVersion]] = []
        for i in range(5):
            quotes.append(
                self._create_quote(
                    db_session,
                    flow_customer,
                    amount=Decimal("500000.00") + Decimal(i * 100000),
                    status="APPROVED",
                    suffix=f"CONV{i}",
                )
            )

        for i, (quote, version) in enumerate(quotes[:3]):
            quote.status = "CONVERTED"
            contract = self._create_contract(
                db_session,
                flow_customer,
                amount=version.total_price,
                quote_version=version,
                opportunity_id=quote.opportunity_id,
                status="SIGNED",
                suffix=f"CONV{i}",
            )
            db_session.add(contract)
        db_session.commit()

        converted_count = sum(1 for quote, _ in quotes if quote.status == "CONVERTED")
        conversion_rate = (converted_count / len(quotes)) * 100

        assert conversion_rate == 60.0

    def test_10_complete_sales_to_project_flow(
        self, db_session: Session, flow_customer: Customer
    ):
        """测试10：完整销售到项目流程"""
        quote, version = self._create_quote(
            db_session,
            flow_customer,
            amount=Decimal("1200000.00"),
            status="DRAFT",
            suffix="COMP",
        )

        quote.status = "APPROVED"
        db_session.commit()
        quote.status = "ACCEPTED"
        db_session.commit()

        contract = self._create_contract(
            db_session,
            flow_customer,
            amount=version.total_price,
            quote_version=version,
            opportunity_id=quote.opportunity_id,
            status="DRAFT",
            suffix="COMP",
        )
        contract.status = "SIGNED"
        contract.signing_date = date.today()
        db_session.commit()

        project = StatusTransitionService(db_session).handle_contract_signed(
            contract.id, auto_create_project=True
        )
        project.status = "ST02"
        project.stage = "S2"
        project.actual_start_date = date.today()
        db_session.commit()

        assert quote.status == "ACCEPTED"
        assert contract.status == "SIGNED"
        assert project.status == "ST02"
        assert project.contract_id == contract.id

"""
场景4：报价 → 合同签订 → 项目启动流程

测试从销售报价到项目启动的业务流程
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.sales.quotes import Quote
from app.models.sales.contracts import Contract
from app.models.project import Project, Customer


class TestQuoteToContractFlow:
    """报价到合同流程测试"""

    @pytest.fixture
    def flow_customer(self, db_session: Session):
        customer = Customer(
            customer_code="CUST-FLOW-001",
            customer_name="流程测试客户",
            contact_person="赵经理",
            contact_phone="13600136000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        return customer

    def test_01_create_sales_quote(self, db_session: Session, flow_customer: Customer):
        """测试1：创建销售报价"""
        quote = Quote(
            quote_code="QT-FLOW-001",
            customer_id=flow_customer.id,
            valid_until=date.today() + timedelta(days=30),
            total_price=Decimal("800000.00"),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(quote)
        db_session.commit()

        assert quote.id is not None
        assert quote.status == "DRAFT"

    def test_02_customer_accepts_quote(self, db_session: Session, flow_customer: Customer):
        """测试2：客户接受报价"""
        quote = Quote(
            quote_code="QT-FLOW-002",
            customer_id=flow_customer.id,
            valid_until=date.today(),
            total_price=Decimal("750000.00"),
            status="APPROVED",
            created_by=1,
        )
        db_session.add(quote)
        db_session.commit()

        quote.status = "ACCEPTED"
        quote.accepted_date = date.today()
        db_session.commit()

        assert quote.status == "ACCEPTED"

    def test_03_create_contract_from_quote(self, db_session: Session, flow_customer: Customer):
        """测试3：从报价创建合同"""
        quote = Quote(
            quote_code="QT-FLOW-003",
            customer_id=flow_customer.id,
            valid_until=date.today(),
            total_price=Decimal("900000.00"),
            status="ACCEPTED",
            created_by=1,
        )
        db_session.add(quote)
        db_session.commit()

        contract = Contract(
            contract_code="CT-FLOW-001",
            customer_id=flow_customer.id,
            quote_id=quote.id,
            contract_date=date.today(),
            total_amount=Decimal("900000.00"),
            status="DRAFT",
            payment_terms="30-30-40",
            delivery_terms="客户现场安装",
            warranty_period=12,
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        assert contract.quote_id == quote.id
        assert contract.total_amount == quote.total_amount

    def test_04_negotiate_contract_terms(self, db_session: Session, flow_customer: Customer):
        """测试4：合同条款协商"""
        contract = Contract(
            contract_code="CT-FLOW-002",
            customer_id=flow_customer.id,
            total_amount=Decimal("850000.00"),
            status="DRAFT",
            payment_terms="预付30%",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 修改条款
        contract.payment_terms = "预付20%，发货前40%，验收后40%"
        contract.delivery_date = date.today() + timedelta(days=90)
        db_session.commit()

        assert "20%" in contract.payment_terms

    def test_05_sign_contract(self, db_session: Session, flow_customer: Customer):
        """测试5：签署合同"""
        contract = Contract(
            contract_code="CT-FLOW-003",
            customer_id=flow_customer.id,
            total_amount=Decimal("920000.00"),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        contract.status = "SIGNED"
        contract.signed_date = date.today()
        contract.signed_by = "赵经理"
        db_session.commit()

        assert contract.status == "SIGNED"
        assert contract.signed_date is not None

    def test_06_create_project_from_contract(self, db_session: Session, flow_customer: Customer):
        """测试6：从合同创建项目"""
        contract = Contract(
            contract_code="CT-FLOW-004",
            customer_id=flow_customer.id,
            total_amount=Decimal("1000000.00"),
            status="SIGNED",
            signed_date=date.today(),
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        project = Project(
            project_code="PJ-FLOW-001",
            project_name="自动化产线项目",
            customer_id=flow_customer.id,
            customer_name=flow_customer.customer_name,
            contract_id=contract.id,
            contract_code=contract.contract_code,
            contract_amount=contract.total_amount,
            stage="S1",
            status="ST01",
            plan_start_date=date.today() + timedelta(days=7),
            plan_end_date=date.today() + timedelta(days=180),
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        contract.project_id = project.id
        db_session.commit()

        assert project.contract_id == contract.id
        assert contract.project_id == project.id

    def test_07_kickoff_project(self, db_session: Session, flow_customer: Customer):
        """测试7：项目启动"""
        contract = Contract(
            contract_code="CT-FLOW-005",
            customer_id=flow_customer.id,
            total_amount=Decimal("880000.00"),
            status="SIGNED",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        project = Project(
            project_code="PJ-FLOW-002",
            project_name="测试项目",
            customer_id=flow_customer.id,
            customer_name=flow_customer.customer_name,
            contract_id=contract.id,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 启动项目
        project.status = "ST02"
        project.actual_start_date = date.today()
        db_session.commit()

        assert project.status == "ST02"

    def test_08_handle_contract_amendment(self, db_session: Session, flow_customer: Customer):
        """测试8：处理合同变更"""
        contract = Contract(
            contract_code="CT-AMEND-001",
            customer_id=flow_customer.id,
            total_amount=Decimal("700000.00"),
            status="SIGNED",
            version=1,
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 创建变更合同
        amendment = Contract(
            contract_code="CT-AMEND-001",
            customer_id=flow_customer.id,
            total_amount=Decimal("850000.00"),
            status="DRAFT",
            version=2,
            parent_id=contract.id,
            amendment_reason="客户增加功能需求",
            created_by=1,
        )
        db_session.add(amendment)
        db_session.commit()

        assert amendment.version == 2
        assert amendment.parent_id == contract.id

    def test_09_track_quote_to_contract_conversion_rate(self, db_session: Session, flow_customer: Customer):
        """测试9：跟踪报价转合同转化率"""
        # 创建5个报价
        quotes = []
        for i in range(5):
            quote = Quote(
                quote_code=f"QT-CONV-{i+1:03d}",
                customer_id=flow_customer.id,
                valid_until=date.today(),
                total_price=Decimal("500000.00") + Decimal(i * 100000),
                status="APPROVED",
                created_by=1,
            )
            db_session.add(quote)
            quotes.append(quote)
        db_session.commit()

        # 3个转化为合同
        for i in range(3):
            quotes[i].status = "CONVERTED"
            contract = Contract(
                contract_code=f"CT-CONV-{i+1:03d}",
                customer_id=flow_customer.id,
                quote_id=quotes[i].id,
                total_amount=quotes[i].total_amount,
                status="SIGNED",
                created_by=1,
            )
            db_session.add(contract)
        db_session.commit()

        # 计算转化率
        converted_count = sum(1 for q in quotes if q.status == "CONVERTED")
        conversion_rate = (converted_count / len(quotes)) * 100

        assert conversion_rate == 60.0  # 60%转化率

    def test_10_complete_sales_to_project_flow(self, db_session: Session, flow_customer: Customer):
        """测试10：完整销售到项目流程"""
        # 步骤1：创建报价
        quote = Quote(
            quote_code="QT-COMPLETE-001",
            customer_id=flow_customer.id,
            valid_until=date.today(),
            total_price=Decimal("1200000.00"),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(quote)
        db_session.commit()

        # 步骤2：报价审批通过
        quote.status = "APPROVED"
        db_session.commit()

        # 步骤3：客户接受
        quote.status = "ACCEPTED"
        db_session.commit()

        # 步骤4：创建合同
        contract = Contract(
            contract_code="CT-COMPLETE-001",
            customer_id=flow_customer.id,
            quote_id=quote.id,
            total_amount=quote.total_amount,
            status="DRAFT",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 步骤5：签署合同
        contract.status = "SIGNED"
        contract.signed_date = date.today()
        db_session.commit()

        # 步骤6：创建项目
        project = Project(
            project_code="PJ-COMPLETE-001",
            project_name="完整流程项目",
            customer_id=flow_customer.id,
            customer_name=flow_customer.customer_name,
            contract_id=contract.id,
            contract_amount=contract.total_amount,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 步骤7：项目启动
        project.status = "ST02"
        project.stage = "S2"
        project.actual_start_date = date.today()
        db_session.commit()

        # 验证完整流程
        assert quote.status == "ACCEPTED"
        assert contract.status == "SIGNED"
        assert project.status == "ST02"
        assert project.contract_id == contract.id

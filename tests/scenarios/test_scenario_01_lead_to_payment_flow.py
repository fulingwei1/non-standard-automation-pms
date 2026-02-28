"""
场景1：销售线索 → 商机 → 报价 → 合同 → 回款 完整流程

测试完整的销售业务闭环，验证各阶段状态流转和数据传递
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.sales.leads import Lead
from app.models.sales.quotes import Quote
from app.models.sales.contracts import Contract
from app.models.sales.invoices import Invoice
from app.models.project import Customer


class TestLeadToPaymentFlow:
    """销售完整流程测试"""

    @pytest.fixture
    def sales_customer(self, db_session: Session):
        """创建测试客户"""
        customer = Customer(
            customer_code="CUST-SALES-001",
            customer_name="测试销售客户",
            contact_person="张经理",
            contact_phone="13800138000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        return customer

    def test_01_create_lead_from_inquiry(self, db_session: Session, admin_token: str):
        """测试1：从客户咨询创建销售线索"""
        lead = Lead(
            lead_code="LEAD-2026-001",
            customer_name="测试销售客户",
            contact_person="张经理",
            contact_phone="13800138000",
            source="WEB",
            status="NEW",
            product_interest="自动化生产线",
            estimated_amount=Decimal("500000.00"),
            probability=30,
            created_by=1,
        )
        db_session.add(lead)
        db_session.commit()
        
        assert lead.id is not None
        assert lead.status == "NEW"
        assert lead.probability == 30

    def test_02_qualify_lead_and_convert_to_opportunity(self, db_session: Session):
        """测试2：线索资格审查并转化为商机"""
        # 创建线索
        lead = Lead(
            lead_code="LEAD-2026-002",
            customer_name="测试销售客户",
            source="REFERRAL",
            status="QUALIFYING",
            probability=50,
            created_by=1,
        )
        db_session.add(lead)
        db_session.commit()

        # 资格审查通过
        lead.status = "QUALIFIED"
        lead.probability = 60
        lead.qualified_date = date.today()
        db_session.commit()

        assert lead.status == "QUALIFIED"
        assert lead.qualified_date is not None

    def test_03_create_quote_from_opportunity(self, db_session: Session, sales_customer: Customer):
        """测试3：从商机创建报价单"""
        quote = Quote(
            quote_code="QT-2026-001",
            customer_id=sales_customer.id,
            valid_until=date.today() + timedelta(days=30),
            total_price=Decimal("520000.00"),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(quote)
        db_session.commit()

        assert quote.id is not None
        assert quote.status == "DRAFT"
        assert quote.total_amount == Decimal("520000.00")

    def test_04_submit_and_approve_quote(self, db_session: Session, sales_customer: Customer):
        """测试4：提交报价并审批"""
        quote = Quote(
            quote_code="QT-2026-002",
            customer_id=sales_customer.id,
            valid_until=date.today(),
            total_price=Decimal("480000.00"),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(quote)
        db_session.commit()

        # 提交审批
        quote.status = "PENDING_APPROVAL"
        db_session.commit()

        # 审批通过
        quote.status = "APPROVED"
        quote.approved_by = 1
        quote.approved_at = datetime.now()
        db_session.commit()

        assert quote.status == "APPROVED"
        assert quote.approved_by is not None

    def test_05_convert_quote_to_contract(self, db_session: Session, sales_customer: Customer):
        """测试5：报价转合同"""
        # 先创建已批准的报价
        quote = Quote(
            quote_code="QT-2026-003",
            customer_id=sales_customer.id,
            valid_until=date.today(),
            total_price=Decimal("500000.00"),
            status="APPROVED",
            created_by=1,
        )
        db_session.add(quote)
        db_session.commit()

        # 创建合同
        contract = Contract(
            contract_code="CT-2026-001",
            customer_id=sales_customer.id,
            quote_id=quote.id,
            contract_date=date.today(),
            total_amount=Decimal("500000.00"),
            status="DRAFT",
            payment_terms="预付30%，发货前30%，验收后40%",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 报价状态更新为已转合同
        quote.status = "CONVERTED"
        db_session.commit()

        assert contract.id is not None
        assert contract.quote_id == quote.id
        assert quote.status == "CONVERTED"

    def test_06_sign_contract(self, db_session: Session, sales_customer: Customer):
        """测试6：合同签署"""
        contract = Contract(
            contract_code="CT-2026-002",
            customer_id=sales_customer.id,
            contract_date=date.today(),
            total_amount=Decimal("450000.00"),
            status="DRAFT",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 签署合同
        contract.status = "SIGNED"
        contract.signed_date = date.today()
        contract.signed_by = "张经理"
        db_session.commit()

        assert contract.status == "SIGNED"
        assert contract.signed_date is not None

    def test_07_create_invoice_from_contract(self, db_session: Session, sales_customer: Customer):
        """测试7：从合同创建发票"""
        # 创建已签署的合同
        contract = Contract(
            contract_code="CT-2026-003",
            customer_id=sales_customer.id,
            total_amount=Decimal("600000.00"),
            status="SIGNED",
            signed_date=date.today(),
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 创建发票（预付款30%）
        invoice = Invoice(
            invoice_code="INV-2026-001",
            contract_id=contract.id,
            customer_id=sales_customer.id,
            invoice_date=date.today(),
            invoice_type="ADVANCE",
            amount=Decimal("180000.00"),  # 30%预付
            tax_rate=Decimal("0.13"),
            tax_amount=Decimal("23400.00"),
            total_amount=Decimal("203400.00"),
            status="ISSUED",
            created_by=1,
        )
        db_session.add(invoice)
        db_session.commit()

        assert invoice.id is not None
        assert invoice.invoice_type == "ADVANCE"
        assert invoice.amount == Decimal("180000.00")

    def test_08_record_payment_receipt(self, db_session: Session, sales_customer: Customer):
        """测试8：登记回款"""
        # 创建发票
        invoice = Invoice(
            invoice_code="INV-2026-002",
            customer_id=sales_customer.id,
            invoice_date=date.today(),
            invoice_type="ADVANCE",
            total_amount=Decimal("203400.00"),
            status="ISSUED",
            created_by=1,
        )
        db_session.add(invoice)
        db_session.commit()

        # 登记回款
        invoice.paid_amount = Decimal("203400.00")
        invoice.paid_date = date.today()
        invoice.status = "PAID"
        db_session.commit()

        assert invoice.status == "PAID"
        assert invoice.paid_amount == invoice.total_amount

    def test_09_complete_payment_flow(self, db_session: Session, sales_customer: Customer):
        """测试9：完整回款流程（预付+发货款+尾款）"""
        # 创建合同
        contract = Contract(
            contract_code="CT-2026-FULL",
            customer_id=sales_customer.id,
            total_amount=Decimal("1000000.00"),
            status="SIGNED",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 预付款30%
        inv1 = Invoice(
            invoice_code="INV-FULL-01",
            contract_id=contract.id,
            customer_id=sales_customer.id,
            invoice_type="ADVANCE",
            amount=Decimal("300000.00"),
            total_amount=Decimal("339000.00"),
            status="PAID",
            paid_amount=Decimal("339000.00"),
            created_by=1,
        )
        db_session.add(inv1)

        # 发货款30%
        inv2 = Invoice(
            invoice_code="INV-FULL-02",
            contract_id=contract.id,
            customer_id=sales_customer.id,
            invoice_type="DELIVERY",
            amount=Decimal("300000.00"),
            total_amount=Decimal("339000.00"),
            status="PAID",
            paid_amount=Decimal("339000.00"),
            created_by=1,
        )
        db_session.add(inv2)

        # 验收款40%
        inv3 = Invoice(
            invoice_code="INV-FULL-03",
            contract_id=contract.id,
            customer_id=sales_customer.id,
            invoice_type="ACCEPTANCE",
            amount=Decimal("400000.00"),
            total_amount=Decimal("452000.00"),
            status="PAID",
            paid_amount=Decimal("452000.00"),
            created_by=1,
        )
        db_session.add(inv3)
        db_session.commit()

        # 验证总回款
        total_paid = inv1.paid_amount + inv2.paid_amount + inv3.paid_amount
        expected_total = Decimal("1000000.00") * Decimal("1.13")
        assert total_paid == expected_total

    def test_10_verify_sales_funnel_conversion_rate(self, db_session: Session, sales_customer: Customer):
        """测试10：验证销售漏斗转化率"""
        # 创建5个线索
        leads = []
        for i in range(5):
            lead = Lead(
                lead_code=f"LEAD-FUNNEL-{i+1}",
                customer_name="测试客户",
                status="NEW",
                probability=20 + i * 10,
                created_by=1,
            )
            db_session.add(lead)
            leads.append(lead)
        
        db_session.commit()

        # 2个转化为商机（40%转化率）
        leads[0].status = "QUALIFIED"
        leads[1].status = "QUALIFIED"

        # 1个转化为报价（20%转化率）
        quote = Quote(
            quote_code="QT-FUNNEL-01",
            customer_id=sales_customer.id,
            valid_until=date.today(),
            total_price=Decimal("300000.00"),
            status="APPROVED",
            created_by=1,
        )
        db_session.add(quote)

        # 1个转化为合同（20%转化率）
        contract = Contract(
            contract_code="CT-FUNNEL-01",
            customer_id=sales_customer.id,
            quote_id=quote.id,
            total_amount=Decimal("300000.00"),
            status="SIGNED",
            created_by=1,
        )
        db_session.add(contract)
        db_session.commit()

        # 验证转化率
        qualified_count = sum(1 for l in leads if l.status == "QUALIFIED")
        assert qualified_count == 2  # 40% conversion rate
        assert quote.status == "APPROVED"
        assert contract.status == "SIGNED"

    def test_11_handle_quote_rejection_and_revision(self, db_session: Session, sales_customer: Customer):
        """测试11：处理报价被拒和修订"""
        # 创建初始报价
        quote_v1 = Quote(
            quote_code="QT-REV-001",
            customer_id=sales_customer.id,
            valid_until=date.today(),
            total_price=Decimal("550000.00"),
            status="REJECTED",
            version=1,
            created_by=1,
        )
        db_session.add(quote_v1)
        db_session.commit()

        # 创建修订版报价
        quote_v2 = Quote(
            quote_code="QT-REV-001",
            customer_id=sales_customer.id,
            valid_until=date.today(),
            total_price=Decimal("480000.00"),  # 降价
            status="APPROVED",
            version=2,
            parent_id=quote_v1.id,
            created_by=1,
        )
        db_session.add(quote_v2)
        db_session.commit()

        assert quote_v1.status == "REJECTED"
        assert quote_v2.version == 2
        assert quote_v2.total_amount < quote_v1.total_amount

    def test_12_track_sales_cycle_time(self, db_session: Session, sales_customer: Customer):
        """测试12：跟踪销售周期时间"""
        # 记录各阶段时间戳
        lead_created = datetime.now() - timedelta(days=60)
        opportunity_created = datetime.now() - timedelta(days=45)
        quote_created = datetime.now() - timedelta(days=30)
        contract_signed = datetime.now() - timedelta(days=15)
        payment_received = datetime.now()

        # 计算各阶段耗时
        lead_to_opportunity = (opportunity_created - lead_created).days
        opportunity_to_quote = (quote_created - opportunity_created).days
        quote_to_contract = (contract_signed - quote_created).days
        contract_to_payment = (payment_received - contract_signed).days
        total_cycle = (payment_received - lead_created).days

        # 验证周期时间合理性
        assert lead_to_opportunity == 15  # 线索到商机
        assert opportunity_to_quote == 15  # 商机到报价
        assert quote_to_contract == 15  # 报价到合同
        assert contract_to_payment == 15  # 合同到回款
        assert total_cycle == 60  # 总周期

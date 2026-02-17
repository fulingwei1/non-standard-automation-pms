# -*- coding: utf-8 -*-
"""
K2组集成测试 - 销售线索到合同全流程
流程：线索创建 → 线索评估 → 商机创建 → 报价 → 报价审批 → 合同签订
"""

import pytest
from datetime import date, datetime
from decimal import Decimal


# ============================================================
# SQLite 内存数据库 fixture
# ============================================================
@pytest.fixture(scope="module")
def db():
    """为本模块提供独立的 SQLite 内存数据库"""
    import sys
    from unittest.mock import MagicMock
    if "redis" not in sys.modules:
        sys.modules["redis"] = MagicMock()
        sys.modules["redis.exceptions"] = MagicMock()

    import os
    os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
    os.environ.setdefault("REDIS_URL", "")
    os.environ.setdefault("ENABLE_SCHEDULER", "false")

    import app.models  # noqa: F401 - 注册所有 ORM 元数据
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ============================================================
# 基础数据 fixtures
# ============================================================
@pytest.fixture(scope="module")
def sales_user(db):
    """创建销售负责人用户"""
    from app.models.user import User
    from app.models.organization import Employee
    from app.core.security import get_password_hash

    emp = Employee(
        employee_code="EMP-SALES-001",
        name="张销售",
        department="销售部",
        role="SALES",
        phone="13800000001",
    )
    db.add(emp)
    db.flush()

    user = User(
        employee_id=emp.id,
        username="sales_flow_test",
        password_hash=get_password_hash("test123"),
        real_name="张销售",
        department="销售部",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def sales_customer(db):
    """创建测试客户"""
    from app.models.project import Customer

    customer = Customer(
        customer_code="CUST-FLOW-001",
        customer_name="智造科技有限公司",
        contact_person="王总",
        contact_phone="13900000001",
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


# ============================================================
# 测试用例
# ============================================================
class TestSalesFlowIntegration:
    """销售线索到合同闭环集成测试"""

    # ─── 1. 线索创建与初始状态验证 ───────────────────────────
    def test_lead_created_with_new_status(self, db, sales_user):
        """创建线索后，状态应为 NEW"""
        from app.models.sales.leads import Lead

        lead = Lead(
            lead_code="LD-FLOW-001",
            source="REFERRAL",
            customer_name="智造科技有限公司",
            industry="汽车零部件",
            contact_name="王总",
            contact_phone="13900000001",
            demand_summary="需要一条全自动装配线",
            owner_id=sales_user.id,
            status="NEW",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        assert lead.id is not None
        assert lead.status == "NEW"
        assert lead.lead_code == "LD-FLOW-001"
        assert lead.demand_summary == "需要一条全自动装配线"

    # ─── 2. 线索评估 → 状态转为 QUALIFIED ───────────────────
    def test_lead_qualified_creates_opportunity(self, db, sales_user, sales_customer):
        """线索评估通过后，状态变为 QUALIFIED，并创建商机"""
        from app.models.sales.leads import Lead, Opportunity

        # 获取已创建的线索
        lead = db.query(Lead).filter(Lead.lead_code == "LD-FLOW-001").first()
        assert lead is not None

        # 评估通过 → 更新状态
        lead.status = "QUALIFIED"
        lead.priority_score = 75
        db.commit()

        # 创建商机
        opp = Opportunity(
            opp_code="OPP-FLOW-001",
            lead_id=lead.id,
            customer_id=sales_customer.id,
            opp_name="全自动装配线项目",
            project_type="AUTOMATION",
            equipment_type="ASSEMBLY",
            stage="DISCOVERY",
            probability=40,
            est_amount=Decimal("850000.00"),
            expected_close_date=date(2026, 6, 30),
            owner_id=sales_user.id,
        )
        db.add(opp)
        db.commit()
        db.refresh(opp)

        assert lead.status == "QUALIFIED"
        assert opp.id is not None
        assert opp.stage == "DISCOVERY"
        assert opp.lead_id == lead.id

    # ─── 3. 商机推进 → 进入报价阶段 ────────────────────────
    def test_opportunity_stage_advances_to_proposal(self, db, sales_user):
        """商机阶段推进至 PROPOSAL（提案阶段）"""
        from app.models.sales.leads import Opportunity

        opp = db.query(Opportunity).filter(
            Opportunity.opp_code == "OPP-FLOW-001"
        ).first()
        assert opp is not None

        opp.stage = "PROPOSAL"
        opp.probability = 60
        db.commit()
        db.refresh(opp)

        assert opp.stage == "PROPOSAL"
        assert opp.probability == 60

    # ─── 4. 创建报价并添加明细 ──────────────────────────────
    def test_quote_created_with_items(self, db, sales_user, sales_customer):
        """为商机创建报价，并添加报价明细"""
        from app.models.sales.leads import Opportunity
        from app.models.sales.quotes import Quote, QuoteVersion, QuoteItem

        opp = db.query(Opportunity).filter(
            Opportunity.opp_code == "OPP-FLOW-001"
        ).first()

        # 创建报价主表
        quote = Quote(
            quote_code="QT-FLOW-001",
            opportunity_id=opp.id,
            customer_id=sales_customer.id,
            status="DRAFT",
            valid_until=date(2026, 3, 31),
            owner_id=sales_user.id,
        )
        db.add(quote)
        db.flush()

        # 创建报价版本
        version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=Decimal("850000.00"),
            cost_total=Decimal("620000.00"),
            gross_margin=Decimal("27.06"),
            lead_time_days=90,
            created_by=sales_user.id,
        )
        db.add(version)
        db.flush()

        # 设置当前版本
        quote.current_version_id = version.id
        db.flush()

        # 添加报价明细
        items = [
            QuoteItem(
                quote_version_id=version.id,
                item_type="EQUIPMENT",
                item_name="主体装配机",
                qty=Decimal("1"),
                unit_price=Decimal("500000.00"),
                cost=Decimal("380000.00"),
                lead_time_days=60,
                unit="台",
            ),
            QuoteItem(
                quote_version_id=version.id,
                item_type="SERVICE",
                item_name="安装调试服务",
                qty=Decimal("1"),
                unit_price=Decimal("80000.00"),
                cost=Decimal("50000.00"),
                lead_time_days=10,
                unit="项",
            ),
            QuoteItem(
                quote_version_id=version.id,
                item_type="SOFTWARE",
                item_name="MES集成软件",
                qty=Decimal("1"),
                unit_price=Decimal("150000.00"),
                cost=Decimal("110000.00"),
                lead_time_days=30,
                unit="套",
            ),
            QuoteItem(
                quote_version_id=version.id,
                item_type="CONSUMABLE",
                item_name="易耗品备件包",
                qty=Decimal("1"),
                unit_price=Decimal("20000.00"),
                cost=Decimal("15000.00"),
                lead_time_days=7,
                unit="套",
            ),
        ]
        db.add_all(items)
        db.commit()
        db.refresh(quote)

        assert quote.id is not None
        assert quote.status == "DRAFT"
        db_items = db.query(QuoteItem).filter(
            QuoteItem.quote_version_id == version.id
        ).all()
        assert len(db_items) == 4
        total = sum(float(i.unit_price) for i in db_items)
        assert abs(total - 750000.0) < 0.01

    # ─── 5. 报价提交审批 → 状态更新 ────────────────────────
    def test_quote_submitted_for_approval(self, db, sales_user):
        """报价提交审批后，状态变为 PENDING_APPROVAL"""
        from app.models.sales import Quote, QuoteApproval

        quote = db.query(Quote).filter(Quote.quote_code == "QT-FLOW-001").first()
        assert quote is not None

        # 提交审批
        quote.status = "PENDING_APPROVAL"
        db.flush()

        # 创建审批记录
        approval = QuoteApproval(
            quote_id=quote.id,
            approval_level=1,
            approval_role="SALES_MANAGER",
            approver_id=sales_user.id,
            approver_name=sales_user.real_name,
            status="PENDING",
        )
        db.add(approval)
        db.commit()
        db.refresh(quote)

        assert quote.status == "PENDING_APPROVAL"
        approvals = db.query(QuoteApproval).filter(
            QuoteApproval.quote_id == quote.id
        ).all()
        assert len(approvals) == 1
        assert approvals[0].status == "PENDING"

    # ─── 6. 报价审批通过 ─────────────────────────────────────
    def test_quote_approval_approved(self, db, sales_user):
        """审批人通过报价，状态变为 APPROVED"""
        from app.models.sales import Quote, QuoteApproval

        quote = db.query(Quote).filter(Quote.quote_code == "QT-FLOW-001").first()
        approval = db.query(QuoteApproval).filter(
            QuoteApproval.quote_id == quote.id
        ).first()

        # 审批通过
        approval.status = "APPROVED"
        approval.approval_result = "APPROVED"
        approval.approval_opinion = "报价合理，毛利率符合要求"
        approval.approved_at = datetime.now()
        quote.status = "APPROVED"
        db.commit()

        db.refresh(quote)
        db.refresh(approval)

        assert quote.status == "APPROVED"
        assert approval.status == "APPROVED"
        assert approval.approval_result == "APPROVED"

    # ─── 7. 从报价创建合同 ──────────────────────────────────
    def test_contract_created_from_quote(self, db, sales_user, sales_customer):
        """报价审批通过后，创建销售合同"""
        from app.models.sales import Quote, QuoteVersion
        from app.models.sales.contracts import Contract

        quote = db.query(Quote).filter(Quote.quote_code == "QT-FLOW-001").first()
        version = db.query(QuoteVersion).filter(
            QuoteVersion.id == quote.current_version_id
        ).first()

        contract = Contract(
            contract_code="CT-FLOW-001",
            contract_name="全自动装配线采购合同",
            contract_type="sales",
            customer_id=sales_customer.id,
            opportunity_id=quote.opportunity_id,
            quote_id=version.id,
            total_amount=Decimal("850000.00"),
            signing_date=date.today(),
            effective_date=date.today(),
            expiry_date=date(2027, 12, 31),
            payment_terms="3-3-3-1分期付款",
            delivery_terms="合同签订后90天交付",
            status="draft",
            sales_owner_id=sales_user.id,
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)

        assert contract.id is not None
        assert contract.contract_code == "CT-FLOW-001"
        assert contract.status == "draft"
        assert float(contract.total_amount) == 850000.00
        assert contract.customer_id == sales_customer.id

    # ─── 8. 合同签署 → 全流程闭环验证 ──────────────────────
    def test_contract_signed_closes_flow(self, db, sales_user, sales_customer):
        """合同签署后全流程闭环：线索→商机→报价→合同均已正确关联"""
        from app.models.sales.leads import Lead, Opportunity
        from app.models.sales.quotes import Quote
        from app.models.sales.contracts import Contract, ContractApproval

        # 合同通过审批并签署
        contract = db.query(Contract).filter(
            Contract.contract_code == "CT-FLOW-001"
        ).first()
        contract.status = "signed"
        db.flush()

        # 创建合同审批记录
        c_approval = ContractApproval(
            contract_id=contract.id,
            approval_level=1,
            approval_role="SALES_MANAGER",
            approver_id=sales_user.id,
            approver_name=sales_user.real_name,
            approval_status="APPROVED",
            approval_opinion="合同条款合理，金额在授权范围内，同意签署",
            approved_at=datetime.now(),
        )
        db.add(c_approval)
        db.commit()

        # ── 全流程闭环校验 ──
        lead = db.query(Lead).filter(Lead.lead_code == "LD-FLOW-001").first()
        opp = db.query(Opportunity).filter(Opportunity.opp_code == "OPP-FLOW-001").first()
        quote = db.query(Quote).filter(Quote.quote_code == "QT-FLOW-001").first()
        contract = db.query(Contract).filter(
            Contract.contract_code == "CT-FLOW-001"
        ).first()

        # 验证链路完整
        assert lead.status == "QUALIFIED"
        assert opp.stage == "PROPOSAL"
        assert opp.lead_id == lead.id
        assert quote.opportunity_id == opp.id
        assert quote.status == "APPROVED"
        assert contract.opportunity_id == opp.id
        assert contract.status == "signed"

        # 验证金额一致性
        assert float(contract.total_amount) == float(opp.est_amount)

        # 验证审批记录
        approvals = db.query(ContractApproval).filter(
            ContractApproval.contract_id == contract.id
        ).all()
        assert len(approvals) == 1
        assert approvals[0].approval_status == "APPROVED"

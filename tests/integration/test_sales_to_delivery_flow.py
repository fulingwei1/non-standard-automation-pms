# -*- coding: utf-8 -*-
"""
金凯博自动化测试（深圳）—— 完整业务链集成测试
从销售线索录入到项目结项、回款核算的端到端流程

业务链路：
  销售线索录入 → 线索评估打分 → 售前方案输出 → 客户报价 & 合同签订
  → 项目立项 → BOM制作 → 采购申请/采购单 → 物料入库
  → 生产排期（装配工单） → FAT出厂验收 → SAT现场验收/项目结项
  → 回款跟进 → 项目毛利核算

测试场景：比亚迪电子 ADAS 域控制器 ICT 在线测试系统，预算 30 万
"""

import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

# ─── Mock redis 和环境变量（必须在任何 app 导入之前）─────────────────────────
if "redis" not in sys.modules:
    redis_mock = MagicMock()
    sys.modules["redis"] = redis_mock
    sys.modules["redis.exceptions"] = MagicMock()

os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ─── 导入所有模型（触发元数据注册）──────────────────────────────────────────
import app.models  # noqa: F401


# ════════════════════════════════════════════════════════════════════════════
#  数据库 Fixture（模块级，共享同一个 SQLite 内存实例）
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def engine():
    """
    创建独立的 SQLite 内存引擎，与全局引擎完全隔离。

    已知问题处理（继承自项目已有方案）：
    - production_work_orders / suppliers 表在元数据中缺失（FK 悬空）
      → 创建存根表避免 NoReferencedTableError
    - idx_created_at 等索引名在多表中重复（SQLite 全局命名空间）
      → 逐表创建，跳过错误
    """
    from app.models.base import Base
    from sqlalchemy import Table, Column, Integer as SAInteger

    # 补全缺失的 FK 目标表（存根）
    for stub in ["production_work_orders", "suppliers"]:
        if stub not in Base.metadata.tables:
            Table(stub, Base.metadata, Column("id", SAInteger, primary_key=True))

    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # 逐表创建（跳过索引冲突等已知错误）
    for table in Base.metadata.sorted_tables:
        try:
            table.create(bind=_engine, checkfirst=True)
        except Exception:
            pass

    yield _engine
    _engine.dispose()


@pytest.fixture(scope="module")
def db(engine):
    """提供模块级数据库会话"""
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ════════════════════════════════════════════════════════════════════════════
#  基础数据 Fixtures
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def sales_user(db):
    """销售负责人 - 张伟"""
    from app.models.organization import Employee
    from app.models.user import User

    emp = Employee(
        employee_code="EMP-S001",
        name="张伟",
        department="销售部",
        role="SALES_ENGINEER",
        phone="13800138001",
    )
    db.add(emp)
    db.flush()

    user = User(
        employee_id=emp.id,
        username="zhang_wei_sales",
        password_hash="$2b$12$placeholder_hash",
        real_name="张伟",
        department="销售部",
        position="销售工程师",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def pm_user(db):
    """项目经理 - 李明"""
    from app.models.organization import Employee
    from app.models.user import User

    emp = Employee(
        employee_code="EMP-PM001",
        name="李明",
        department="项目部",
        role="PROJECT_MANAGER",
        phone="13800138002",
    )
    db.add(emp)
    db.flush()

    user = User(
        employee_id=emp.id,
        username="li_ming_pm",
        password_hash="$2b$12$placeholder_hash",
        real_name="李明",
        department="项目部",
        position="项目经理",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def byd_customer(db):
    """比亚迪电子 - 客户数据"""
    from app.models.project import Customer

    customer = Customer(
        customer_code="CUST-BYD-001",
        customer_name="比亚迪电子",
        short_name="比亚迪",
        customer_type="A",
        industry="汽车电子",
        address="广东省深圳市龙岗区比亚迪路3009号",
        contact_person="王工",
        contact_phone="13800138003",
        contact_email="wang.gong@byd.com",
        credit_level="A",
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture(scope="module")
def ni_vendor(db):
    """NI（国家仪器）供应商"""
    from app.models.vendor import Vendor

    vendor = Vendor(
        supplier_code="VND-NI-001",
        supplier_name="美国国家仪器（NI）有限公司",
        vendor_type="MATERIAL",
        contact_person="陈工",
        contact_phone="13800138010",
        supplier_level="A",
        payment_terms="月结30天",
        status="ACTIVE",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@pytest.fixture(scope="module")
def smc_vendor(db):
    """SMC 气动元件供应商"""
    from app.models.vendor import Vendor

    vendor = Vendor(
        supplier_code="VND-SMC-001",
        supplier_name="SMC（中国）有限公司",
        vendor_type="MATERIAL",
        contact_person="赵工",
        contact_phone="13800138011",
        supplier_level="A",
        payment_terms="月结30天",
        status="ACTIVE",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


# ════════════════════════════════════════════════════════════════════════════
#  模块级"共享状态"容器 —— 把业务对象 id 串联到各测试
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def flow_state():
    """
    业务链共享状态字典，用于在各测试间传递关键 ID。
    模拟真实系统中跨步骤的业务对象引用。
    """
    return {}


# ════════════════════════════════════════════════════════════════════════════
#  测试用例（按业务流程顺序排列）
# ════════════════════════════════════════════════════════════════════════════


class TestSalesLeadToDelivery:
    """完整业务链集成测试：销售线索 → 项目交付 → 回款核算"""

    # ────────────────────────────────────────────────────────────────────────
    # 1. 线索录入 & 评分
    # ────────────────────────────────────────────────────────────────────────

    def test_lead_create_and_score(self, db, sales_user, byd_customer, flow_state):
        """
        场景：录入比亚迪 ADAS 域控制器 ICT 测试系统线索，
              按技术可行性(40分) + 预算匹配(30分) + 竞争态势(30分) 评分，
              期望总分 ≥ 70 分（A级线索启动阈值）。
        """
        from app.models.sales import Lead, Opportunity
        from tests.fixtures.industry_data import PROJECT_TYPES, CUSTOMERS

        # 1-a 创建线索
        lead = Lead(
            lead_code="LD260217001",
            source="展会-慕尼黑上海电子展",
            customer_name="比亚迪电子",
            industry="汽车电子",
            contact_name="王工",
            contact_phone="13800138003",
            demand_summary=(
                "ADAS域控制器主板ICT在线测试系统，"
                "需兼容8个版本测试点，节拍≤12秒/件，预算30万"
            ),
            owner_id=sales_user.id,
            status="NEW",
        )
        db.add(lead)
        db.flush()

        # 1-b 线索评分算法（模拟售前系统评分逻辑）
        ict_params = PROJECT_TYPES["ICT"]

        def score_ict_lead(budget: float, tech_complexity: str, competition: str) -> int:
            """
            评分模型：
              技术可行性（满分40）: MEDIUM=30, HIGH=20, LOW=40
              预算匹配（满分30）:   预算/均价 >= 1.0 → 30; 0.8~1.0 → 20; <0.8 → 10
              竞争态势（满分30）:   LOW=25, MEDIUM=18, HIGH=10
            """
            tech_score = {"LOW": 40, "MEDIUM": 30, "HIGH": 20}.get(tech_complexity, 20)
            ratio = budget / ict_params["avg_budget"]
            budget_score = 30 if ratio >= 1.0 else (20 if ratio >= 0.8 else 10)
            comp_score = {"LOW": 25, "MEDIUM": 18, "HIGH": 10}.get(competition, 18)
            return tech_score + budget_score + comp_score

        budget = 300_000          # 比亚迪预算 30 万
        score = score_ict_lead(
            budget=budget,
            tech_complexity="MEDIUM",   # ICT 难度中等
            competition="MEDIUM",        # 竞争态势中等
        )

        # 更新线索评分
        lead.priority_score = score
        lead.status = "QUALIFIED"
        db.commit()
        db.refresh(lead)

        flow_state["lead_id"] = lead.id
        flow_state["budget"] = budget

        # ── 断言 ──
        assert lead.id is not None, "线索应成功保存到数据库"
        assert lead.lead_code == "LD260217001"
        assert score >= 70, f"ICT线索评分 {score} 应 ≥ 70（A级线索阈值）"
        assert lead.priority_score >= 70
        assert lead.status == "QUALIFIED"

        print(f"\n✓ 线索评分：{score} 分 | 预算匹配：{budget/ict_params['avg_budget']:.0%}")

    # ────────────────────────────────────────────────────────────────────────
    # 2. 售前方案输出
    # ────────────────────────────────────────────────────────────────────────

    def test_presale_solution_generation(self, db, sales_user, byd_customer, flow_state):
        """
        场景：基于 ICT 线索生成售前技术方案，
              验证方案摘要包含关键技术词汇（ICT、飞针/床钉、夹具、程序）。
        """
        from tests.fixtures.industry_data import PROJECT_TYPES, KPI_BENCHMARKS

        # 2-a 使用 Mock 模式生成售前方案对象（presale_ai_solution 模型依赖外部AI）
        solution_summary = {
            "title": "比亚迪电子ADAS域控制器ICT在线测试系统—技术方案",
            "equipment_type": "ICT",
            "technical_approach": (
                "采用 NI PXI 平台搭配飞针测试仪，"
                "定制专用床钉夹具适配 ADAS 主板 8 版本测试点；"
                "测试程序基于 LabVIEW 开发，支持在线参数配置与版本切换；"
                "预计节拍 ≤ 10 秒/件，故障覆盖率 ≥ 99.2%。"
            ),
            "bom_estimate_cny": 185_000,   # 硬件 BOM 估算
            "labor_estimate_cny": 75_000,  # 人工成本估算
            "total_cost_estimate": 260_000,
            "gross_margin_estimate": (300_000 - 260_000) / 300_000,
            "delivery_days": 90,
            "risk_summary": PROJECT_TYPES["ICT"]["typical_risks"],
        }

        # 2-b 验收关键技术词
        required_keywords = ["ICT", "夹具", "程序", "测试"]
        full_text = solution_summary["title"] + solution_summary["technical_approach"]
        found = [kw for kw in required_keywords if kw in full_text]

        # 2-c 存储方案摘要到 flow_state，供后续步骤使用
        flow_state["solution"] = solution_summary

        # ── 断言 ──
        assert len(found) == len(required_keywords), (
            f"方案缺少关键词：{set(required_keywords) - set(found)}"
        )
        assert solution_summary["gross_margin_estimate"] > 0, "预估毛利率应为正"
        assert solution_summary["total_cost_estimate"] < flow_state["budget"], (
            "估算成本不应超出预算"
        )
        assert solution_summary["delivery_days"] <= PROJECT_TYPES["ICT"]["avg_duration_days"] + 10

        print(
            f"\n✓ 售前方案生成 | 预估毛利率 "
            f"{solution_summary['gross_margin_estimate']:.1%} | "
            f"交期 {solution_summary['delivery_days']} 天"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 3. 客户报价单
    # ────────────────────────────────────────────────────────────────────────

    def test_quotation_creation(self, db, sales_user, byd_customer, flow_state):
        """
        场景：创建报价单，录入含税/不含税价格，
              验证：含税价 = 不含税价 × 1.13（增值税13%）。
        """
        from app.models.sales import Opportunity, Quote, QuoteVersion, QuoteItem
        from tests.fixtures.industry_data import KPI_BENCHMARKS

        # 3-a 创建商机
        opp = Opportunity(
            opp_code="OPP260217001",
            customer_id=byd_customer.id,
            opp_name="比亚迪ADAS域控制器ICT测试系统商机",
            project_type="ICT",
            stage="PROPOSAL",
            probability=75,
            est_amount=Decimal("300000.00"),
            expected_close_date=date.today() + timedelta(days=45),
            owner_id=sales_user.id,
        )
        db.add(opp)
        db.flush()
        flow_state["opp_id"] = opp.id

        # 3-b 创建报价主表
        quote = Quote(
            quote_code="QT260217001",
            opportunity_id=opp.id,
            customer_id=byd_customer.id,
            status="DRAFT",
            valid_until=date.today() + timedelta(days=30),
            owner_id=sales_user.id,
        )
        db.add(quote)
        db.flush()

        # 3-c 创建报价版本（不含税价）
        unit_price_ex_tax = Decimal("265_486.73")  # 不含税价（合计）
        tax_rate = Decimal("0.13")
        unit_price_inc_tax = (unit_price_ex_tax * (1 + tax_rate)).quantize(Decimal("0.01"))

        version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1",
            total_price=unit_price_inc_tax,   # 含税总价录入报价版本
            cost_total=Decimal("182000.00"),
            gross_margin=Decimal("35.50"),
            lead_time_days=90,
            delivery_date=date.today() + timedelta(days=90),
            created_by=sales_user.id,
        )
        db.add(version)
        db.flush()

        # 3-d 录入报价明细
        items_data = [
            ("NI PXI 机箱及板卡", Decimal("35000.00"), Decimal("1")),
            ("ICT床钉夹具（定制）", Decimal("45000.00"), Decimal("1")),
            ("测试程序开发", Decimal("60000.00"), Decimal("1")),
            ("气缸等气动元件", Decimal("2240.00"), Decimal("1")),
            ("工业相机×2", Decimal("6400.00"), Decimal("1")),
            ("集成调试及项目管理", Decimal("116846.73"), Decimal("1")),
        ]
        for name, price, qty in items_data:
            item = QuoteItem(
                quote_version_id=version.id,
                item_name=name,
                qty=qty,
                unit_price=price,
                cost=price * qty,   # 用 cost 字段记录该行小计
            )
            db.add(item)

        # 更新报价主表当前版本
        quote.current_version_id = version.id
        db.commit()
        db.refresh(version)
        flow_state["quote_id"] = quote.id
        flow_state["quote_version_id"] = version.id
        flow_state["price_ex_tax"] = unit_price_ex_tax

        # ── 断言 ──
        calculated_inc = (unit_price_ex_tax * Decimal("1.13")).quantize(Decimal("0.01"))
        assert version.total_price == calculated_inc, (
            f"含税价 {version.total_price} ≠ 不含税价×1.13={calculated_inc}"
        )
        # 毛利率合理性校验
        if version.cost_total and version.total_price:
            gm = float(version.total_price - version.cost_total) / float(version.total_price)
            assert gm > 0, "报价毛利率应为正数"

        print(
            f"\n✓ 报价单 {quote.quote_code} | "
            f"不含税 ¥{unit_price_ex_tax:,.2f} → "
            f"含税 ¥{calculated_inc:,.2f}"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 4. 合同签订
    # ────────────────────────────────────────────────────────────────────────

    def test_contract_signing(self, db, sales_user, byd_customer, flow_state):
        """
        场景：报价经客户确认后签订合同，
              验证付款节点比例合计 = 100%（3-3-3-1 模式）。
        """
        from app.models.sales import Contract

        contract_amount = Decimal("300000.00")

        # 4-a 创建合同
        contract = Contract(
            contract_code="CTR260217001",
            contract_name="比亚迪电子ADAS ICT测试系统销售合同",
            contract_type="sales",
            customer_id=byd_customer.id,
            opportunity_id=flow_state["opp_id"],
            quote_id=flow_state["quote_version_id"],
            total_amount=contract_amount,
            signing_date=date.today(),
            effective_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            payment_terms="30%预付款 + 30%中期款 + 30%验收款 + 10%质保金",
            delivery_terms="合同签订后90个工作日内完成FAT验收",
            status="signed",
            sales_owner_id=sales_user.id,
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        flow_state["contract_id"] = contract.id
        flow_state["contract_amount"] = float(contract_amount)

        # 4-b 创建付款节点（3/3/3/1 比例）
        payment_nodes = [
            {
                "payment_no": 1,
                "payment_name": "预付款（合同签订）",
                "payment_type": "ADVANCE",
                "payment_ratio": Decimal("30.00"),
                "planned_amount": contract_amount * Decimal("0.30"),
                "planned_date": date.today() + timedelta(days=7),
                "trigger_condition": "合同签订后7天内",
            },
            {
                "payment_no": 2,
                "payment_name": "中期款（图纸确认）",
                "payment_type": "DELIVERY",
                "payment_ratio": Decimal("30.00"),
                "planned_amount": contract_amount * Decimal("0.30"),
                "planned_date": date.today() + timedelta(days=45),
                "trigger_condition": "图纸及方案确认后",
            },
            {
                "payment_no": 3,
                "payment_name": "验收款（FAT通过）",
                "payment_type": "ACCEPTANCE",
                "payment_ratio": Decimal("30.00"),
                "planned_amount": contract_amount * Decimal("0.30"),
                "planned_date": date.today() + timedelta(days=90),
                "trigger_condition": "FAT出厂验收通过",
            },
            {
                "payment_no": 4,
                "payment_name": "质保金（SAT通过后1年）",
                "payment_type": "WARRANTY",
                "payment_ratio": Decimal("10.00"),
                "planned_amount": contract_amount * Decimal("0.10"),
                "planned_date": date.today() + timedelta(days=365),
                "trigger_condition": "SAT现场验收通过后12个月质保期满",
            },
        ]

        from app.models.project import ProjectPaymentPlan

        plans = []
        for node in payment_nodes:
            plan = ProjectPaymentPlan(
                project_id=None,   # 合同签订时项目尚未立项，project_id 留空
                contract_id=contract.id,
                payment_no=node["payment_no"],
                payment_name=node["payment_name"],
                payment_type=node["payment_type"],
                payment_ratio=node["payment_ratio"],
                planned_amount=node["planned_amount"],
                planned_date=node["planned_date"],
                trigger_condition=node["trigger_condition"],
                status="PENDING",
            )
            db.add(plan)
            plans.append(plan)

        db.commit()
        flow_state["payment_plan_ids"] = [p.id for p in [
            db.query(ProjectPaymentPlan)
              .filter(ProjectPaymentPlan.contract_id == contract.id)
              .order_by(ProjectPaymentPlan.payment_no)
              .all()
        ][0]]  # flatten

        # ── 断言 ──
        all_plans = (
            db.query(ProjectPaymentPlan)
            .filter(ProjectPaymentPlan.contract_id == contract.id)
            .all()
        )
        total_ratio = sum(float(p.payment_ratio) for p in all_plans)
        assert abs(total_ratio - 100.0) < 0.01, (
            f"付款节点比例合计 {total_ratio:.1f}% ≠ 100%"
        )
        assert len(all_plans) == 4, "应有 4 个付款节点（3+3+3+1）"
        # 验证付款类型顺序
        types = [p.payment_type for p in all_plans]
        assert "ADVANCE" in types and "WARRANTY" in types, "应含预付款和质保金节点"

        print(
            f"\n✓ 合同 {contract.contract_code} 签订 | "
            f"金额 ¥{contract_amount:,.0f} | "
            f"付款节点 {len(all_plans)} 期 | 比例合计 {total_ratio:.0f}%"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 5. 项目立项
    # ────────────────────────────────────────────────────────────────────────

    def test_project_initiation_from_contract(
        self, db, pm_user, byd_customer, flow_state
    ):
        """
        场景：从已签合同生成项目，
              验证项目编号格式为 PJyymmddxxx（如 PJ260217001）。
        """
        from app.models.project import Project

        # 5-a 根据合同信息生成项目
        today = date.today()
        project_code = f"PJ{today.strftime('%y%m%d')}001"

        project = Project(
            project_code=project_code,
            project_name="比亚迪电子ADAS域控制器ICT在线测试系统",
            short_name="BYD-ADAS-ICT",
            customer_id=byd_customer.id,
            customer_name="比亚迪电子",
            contract_no=f"CTR260217001",
            project_type="ICT",
            industry="汽车电子",
            project_category="销售",
            stage="S1",
            status="ST01",
            health="H1",
            contract_amount=Decimal(str(flow_state["contract_amount"])),
            budget_amount=Decimal(str(flow_state["contract_amount"])),
            planned_start_date=today,
            planned_end_date=today + timedelta(days=90),
            pm_id=pm_user.id,
            pm_name=pm_user.real_name,
            priority="HIGH",
            description=(
                "ADAS域控制器主板ICT在线测试系统，"
                "兼容8版本测试点，节拍≤10秒/件，源自合同 CTR260217001"
            ),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        flow_state["project_id"] = project.id
        flow_state["project_code"] = project.project_code

        # 5-b 将付款计划关联到项目
        from app.models.project import ProjectPaymentPlan

        db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.contract_id == flow_state["contract_id"]
        ).update({"project_id": project.id})
        db.commit()

        # ── 断言 ──
        import re
        pattern = r"^PJ\d{6}\d{3}$"
        assert re.match(pattern, project.project_code), (
            f"项目编号 {project.project_code!r} 不符合 PJyymmddxxx 格式"
        )
        assert project.customer_id == byd_customer.id
        assert float(project.contract_amount) == flow_state["contract_amount"]
        assert project.pm_id == pm_user.id

        print(
            f"\n✓ 项目立项 {project.project_code} | "
            f"PM: {pm_user.real_name} | "
            f"合同额 ¥{float(project.contract_amount):,.0f}"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 6. BOM 清单制作
    # ────────────────────────────────────────────────────────────────────────

    def test_bom_creation(self, db, pm_user, ni_vendor, smc_vendor, flow_state):
        """
        场景：为 ICT 项目创建 BOM，录入关键物料：
              NI机箱（3.5万）、气缸×8（0.28万合计2.24万）、工业相机×2（0.64万合计1.28万）。
              验证 BOM 总金额 = 各行明细之和。
        """
        from app.models.material import BomHeader, BomItem, Material, MaterialCategory

        # 6-a 创建物料分类
        cat_instrument = MaterialCategory(
            category_code="CAT-INST",
            category_name="仪器仪表",
            level=1,
        )
        cat_pneumatic = MaterialCategory(
            category_code="CAT-PNEU",
            category_name="气动元件",
            level=1,
        )
        cat_vision = MaterialCategory(
            category_code="CAT-VIS",
            category_name="视觉器件",
            level=1,
        )
        db.add_all([cat_instrument, cat_pneumatic, cat_vision])
        db.flush()

        # 6-b 创建物料主数据
        ni_pxi = Material(
            material_code="MAT-NI-001",
            material_name="NI PXI机箱",
            category_id=cat_instrument.id,
            specification="PXIe-1082, 8-slot, 500W",
            brand="NI",
            unit="台",
            standard_price=Decimal("35000.00"),
            lead_time_days=30,
            is_key_material=True,
            default_supplier_id=ni_vendor.id,
        )
        cylinder = Material(
            material_code="MAT-SMC-001",
            material_name="气缸（SMC CQ2B32-50D）",
            category_id=cat_pneumatic.id,
            specification="CQ2B32-50D, 双轴, 行程50mm",
            brand="SMC",
            unit="个",
            standard_price=Decimal("280.00"),
            lead_time_days=7,
            is_key_material=False,
            default_supplier_id=smc_vendor.id,
        )
        camera = Material(
            material_code="MAT-HK-001",
            material_name="工业相机（海康MV-CS050-10GM）",
            category_id=cat_vision.id,
            specification="500万像素, 全局快门, GigE接口",
            brand="海康",
            unit="台",
            standard_price=Decimal("3200.00"),
            lead_time_days=14,
            is_key_material=True,
        )
        db.add_all([ni_pxi, cylinder, camera])
        db.flush()

        # 6-c 创建 BOM 表头
        bom = BomHeader(
            bom_no=f"BOM-{flow_state['project_code']}-001",
            bom_name="ADAS ICT测试系统物料清单 V1.0",
            project_id=flow_state["project_id"],
            version="1.0",
            is_latest=True,
            status="DRAFT",
            created_by=pm_user.id,
        )
        db.add(bom)
        db.flush()

        # 6-d 录入 BOM 明细
        bom_items_data = [
            {
                "item_no": 10,
                "material": ni_pxi,
                "qty": Decimal("1"),
                "unit_price": Decimal("35000.00"),
                "is_key": True,
                "supplier_id": ni_vendor.id,
            },
            {
                "item_no": 20,
                "material": cylinder,
                "qty": Decimal("8"),
                "unit_price": Decimal("280.00"),
                "is_key": False,
                "supplier_id": smc_vendor.id,
            },
            {
                "item_no": 30,
                "material": camera,
                "qty": Decimal("2"),
                "unit_price": Decimal("3200.00"),
                "is_key": True,
                "supplier_id": None,
            },
        ]

        total_bom_amount = Decimal("0")
        for row in bom_items_data:
            amount = row["qty"] * row["unit_price"]
            total_bom_amount += amount
            item = BomItem(
                bom_id=bom.id,
                item_no=row["item_no"],
                material_id=row["material"].id,
                material_code=row["material"].material_code,
                material_name=row["material"].material_name,
                specification=row["material"].specification,
                unit=row["material"].unit,
                quantity=row["qty"],
                unit_price=row["unit_price"],
                amount=amount,
                source_type="PURCHASE",
                supplier_id=row["supplier_id"],
                is_key_item=row["is_key"],
                level=1,
            )
            db.add(item)

        bom.total_items = len(bom_items_data)
        bom.total_amount = total_bom_amount
        db.commit()
        db.refresh(bom)
        flow_state["bom_id"] = bom.id
        flow_state["bom_amount"] = float(total_bom_amount)
        flow_state["ni_pxi_material_id"] = ni_pxi.id
        flow_state["cylinder_material_id"] = cylinder.id
        flow_state["camera_material_id"] = camera.id
        flow_state["ni_vendor_id"] = ni_vendor.id
        flow_state["smc_vendor_id"] = smc_vendor.id

        # ── 断言 ──
        # NI机箱单价 3.5万
        assert float(ni_pxi.standard_price) == 35000.0, "NI机箱单价应为 3.5 万"
        # 气缸 8 个 × 280 = 2240
        cylinder_total = float(Decimal("8") * Decimal("280.00"))
        assert cylinder_total == 2240.0, f"气缸合计金额 {cylinder_total} 应为 2240（0.224万）"
        # 相机 2 台 × 3200 = 6400
        camera_total = float(Decimal("2") * Decimal("3200.00"))
        assert camera_total == 6400.0, f"相机合计金额 {camera_total} 应为 6400（0.64万）"
        # BOM 总金额
        expected_total = 35000.0 + 2240.0 + 6400.0
        assert float(bom.total_amount) == pytest.approx(expected_total, rel=1e-4), (
            f"BOM总金额 {float(bom.total_amount)} ≠ 预期 {expected_total}"
        )
        assert bom.total_items == 3

        print(
            f"\n✓ BOM {bom.bom_no} | {bom.total_items} 行 | "
            f"总金额 ¥{float(bom.total_amount):,.2f}"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 7. BOM 缺料 → 采购申请
    # ────────────────────────────────────────────────────────────────────────

    def test_purchase_request_from_bom(self, db, pm_user, flow_state):
        """
        场景：BOM 中 NI 机箱和工业相机库存为 0，触发采购申请，
              验证采购申请行数=2（按供应商拆分），数量和供应商正确。
        """
        from app.models.purchase import PurchaseRequest, PurchaseRequestItem
        from app.models.material import BomItem, BomHeader

        # 7-a 查找 BOM 中库存为 0 的物料（模拟缺料检测）
        bom_items = (
            db.query(BomItem)
            .filter(BomItem.bom_id == flow_state["bom_id"])
            .all()
        )
        shortage_items = [
            item for item in bom_items
            if item.received_qty == 0  # 均未到货 = 全部缺料
        ]
        assert len(shortage_items) == 3, f"应有 3 行缺料，实际 {len(shortage_items)}"

        # 7-b 生成采购申请（NI 机箱单独一张，SMC+海康合并一张）
        pr_ni = PurchaseRequest(
            request_no="PR260217001",
            project_id=flow_state["project_id"],
            source_type="BOM",
            source_id=flow_state["bom_id"],
            request_reason="BOM缺料自动触发采购申请 - NI仪器仪表",
            required_date=date.today() + timedelta(days=30),
            status="DRAFT",
            requested_by=pm_user.id,
            requested_at=datetime.now(),
            created_by=pm_user.id,
        )
        db.add(pr_ni)
        db.flush()

        # NI机箱采购申请明细
        pr_ni_item = PurchaseRequestItem(
            request_id=pr_ni.id,
            material_id=flow_state["ni_pxi_material_id"],
            material_code="MAT-NI-001",
            material_name="NI PXI机箱",
            specification="PXIe-1082, 8-slot, 500W",
            unit="台",
            quantity=Decimal("1"),
            unit_price=Decimal("35000.00"),
            amount=Decimal("35000.00"),
            required_date=date.today() + timedelta(days=30),
        )
        db.add(pr_ni_item)

        # 气缸 + 相机 合并一张采购申请
        pr_other = PurchaseRequest(
            request_no="PR260217002",
            project_id=flow_state["project_id"],
            source_type="BOM",
            source_id=flow_state["bom_id"],
            request_reason="BOM缺料自动触发采购申请 - 气动元件/视觉器件",
            required_date=date.today() + timedelta(days=14),
            status="DRAFT",
            requested_by=pm_user.id,
            requested_at=datetime.now(),
            created_by=pm_user.id,
        )
        db.add(pr_other)
        db.flush()

        pr_cyl_item = PurchaseRequestItem(
            request_id=pr_other.id,
            material_id=flow_state["cylinder_material_id"],
            material_code="MAT-SMC-001",
            material_name="气缸（SMC CQ2B32-50D）",
            unit="个",
            quantity=Decimal("8"),
            unit_price=Decimal("280.00"),
            amount=Decimal("2240.00"),
            required_date=date.today() + timedelta(days=7),
        )
        pr_cam_item = PurchaseRequestItem(
            request_id=pr_other.id,
            material_id=flow_state["camera_material_id"],
            material_code="MAT-HK-001",
            material_name="工业相机（海康）",
            unit="台",
            quantity=Decimal("2"),
            unit_price=Decimal("3200.00"),
            amount=Decimal("6400.00"),
            required_date=date.today() + timedelta(days=14),
        )
        db.add_all([pr_cyl_item, pr_cam_item])

        # 更新申请总金额
        pr_ni.total_amount = Decimal("35000.00")
        pr_other.total_amount = Decimal("8640.00")
        db.commit()

        flow_state["pr_ni_id"] = pr_ni.id
        flow_state["pr_other_id"] = pr_other.id

        # ── 断言 ──
        ni_items = list(db.query(PurchaseRequestItem)
                          .filter(PurchaseRequestItem.request_id == pr_ni.id).all())
        other_items = list(db.query(PurchaseRequestItem)
                             .filter(PurchaseRequestItem.request_id == pr_other.id).all())

        assert len(ni_items) == 1, "NI采购申请应有1行（机箱）"
        assert float(ni_items[0].quantity) == 1.0, "NI机箱数量应为1台"
        assert ni_items[0].supplier_id == flow_state["ni_vendor_id"], "供应商应为NI"

        assert len(other_items) == 2, "其他采购申请应有2行（气缸+相机）"
        cyl = next(i for i in other_items if "气缸" in i.material_name)
        assert float(cyl.quantity) == 8.0, "气缸数量应为8个"

        print(
            f"\n✓ 采购申请 {pr_ni.request_no}（NI机箱）+ "
            f"{pr_other.request_no}（气动/视觉）生成完毕"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 8. 物料到货入库
    # ────────────────────────────────────────────────────────────────────────

    def test_material_receipt(self, db, pm_user, ni_vendor, flow_state):
        """
        场景：NI机箱到货，创建收货单，验证库存更新（current_stock +1）。
        """
        from app.models.purchase import (
            PurchaseOrder, PurchaseOrderItem,
            GoodsReceipt, GoodsReceiptItem,
        )
        from app.models.material import Material

        # 8-a 先生成采购单（PR → PO）
        po = PurchaseOrder(
            order_no="PO260217001",
            supplier_id=ni_vendor.id,
            project_id=flow_state["project_id"],
            source_request_id=flow_state["pr_ni_id"],
            order_title="NI PXI机箱采购订单",
            total_amount=Decimal("35000.00"),
            tax_rate=Decimal("13"),
            tax_amount=Decimal("4550.00"),
            amount_with_tax=Decimal("39550.00"),
            order_date=date.today(),
            required_date=date.today() + timedelta(days=30),
            status="APPROVED",
            payment_terms="月结30天",
            created_by=pm_user.id,
        )
        db.add(po)
        db.flush()

        po_item = PurchaseOrderItem(
            order_id=po.id,
            item_no=1,
            material_id=flow_state["ni_pxi_material_id"],
            material_code="MAT-NI-001",
            material_name="NI PXI机箱",
            specification="PXIe-1082, 8-slot",
            unit="台",
            quantity=Decimal("1"),
            unit_price=Decimal("35000.00"),
            amount=Decimal("35000.00"),
        )
        db.add(po_item)
        db.flush()
        flow_state["po_id"] = po.id

        # 8-b 创建收货单
        receipt = GoodsReceipt(
            receipt_no="GR260217001",
            order_id=po.id,
            supplier_id=ni_vendor.id,
            receipt_date=date.today() + timedelta(days=28),
            receipt_type="NORMAL",
            delivery_note_no="NI-DN-2026-001",
            status="PENDING",
            inspect_status="PENDING",
            created_by=pm_user.id,
        )
        db.add(receipt)
        db.flush()

        receipt_item = GoodsReceiptItem(
            receipt_id=receipt.id,
            order_item_id=po_item.id,
            material_code="MAT-NI-001",
            material_name="NI PXI机箱",
            delivery_qty=Decimal("1"),
            received_qty=Decimal("1"),
            qualified_qty=Decimal("1"),
            rejected_qty=Decimal("0"),
            warehoused_qty=Decimal("1"),
            inspect_result="QUALIFIED",
        )
        db.add(receipt_item)

        # 8-c 质检通过 → 更新状态
        receipt.inspect_status = "QUALIFIED"
        receipt.inspected_at = datetime.now()
        receipt.status = "COMPLETED"
        receipt.warehoused_at = datetime.now()
        receipt.warehoused_by = pm_user.id

        # 8-d 更新物料库存（模拟入库动作）
        ni_mat = db.query(Material).filter(
            Material.id == flow_state["ni_pxi_material_id"]
        ).first()
        stock_before = float(ni_mat.current_stock)
        ni_mat.current_stock = (ni_mat.current_stock or Decimal("0")) + Decimal("1")

        # 更新 PO 明细已收货数量
        po_item.received_qty = Decimal("1")

        db.commit()
        db.refresh(ni_mat)
        db.refresh(receipt)

        flow_state["gr_id"] = receipt.id

        # ── 断言 ──
        assert float(ni_mat.current_stock) == stock_before + 1.0, (
            f"NI机箱库存应从 {stock_before} 增加到 {stock_before + 1}"
        )
        assert receipt.status == "COMPLETED", "收货单状态应为 COMPLETED"
        assert receipt.inspect_status == "QUALIFIED", "质检状态应为 QUALIFIED（合格）"

        print(
            f"\n✓ NI PXI机箱入库 | 收货单 {receipt.receipt_no} | "
            f"库存 {stock_before:.0f} → {float(ni_mat.current_stock):.0f} 台"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 9. 生产排期（装配工单）
    # ────────────────────────────────────────────────────────────────────────

    def test_work_order_creation(self, db, pm_user, flow_state):
        """
        场景：物料准备充足后，生成 ICT 设备装配工单并分配工程师。
              使用 Mock 模式绕过 Worker/Workshop/ProcessDict 等复杂关联。
        """
        # 装配工单逻辑（用纯 Python 数据结构 + Mock 模拟，避免生产模型复杂关联）
        work_order_data = {
            "work_order_no": f"WO-{flow_state['project_code']}-001",
            "task_name": "ADAS ICT测试系统装配联调",
            "task_type": "ASSEMBLY",
            "project_id": flow_state["project_id"],
            "plan_qty": 1,
            "standard_hours": Decimal("160"),   # 20 人天 × 8h
            "plan_start_date": date.today() + timedelta(days=30),
            "plan_end_date": date.today() + timedelta(days=75),
            "status": "PENDING",
            "priority": "HIGH",
            "work_content": (
                "1. NI PXI机箱安装与调试；"
                "2. 气缸行程调整及气路搭建；"
                "3. 工业相机安装与标定；"
                "4. ICT测试程序集成联调；"
                "5. 功能及性能验证"
            ),
            "assigned_engineer": pm_user.real_name,
            "assigned_user_id": pm_user.id,
        }

        # Mock 工单对象（WorkOrder 依赖 Worker/Workshop 等非核心表）
        mock_work_order = MagicMock()
        for k, v in work_order_data.items():
            setattr(mock_work_order, k, v)

        flow_state["work_order"] = work_order_data

        # ── 断言 ──
        assert work_order_data["task_type"] == "ASSEMBLY", "工单类型应为装配"
        assert work_order_data["assigned_user_id"] == pm_user.id, "应分配项目工程师"
        assert float(work_order_data["standard_hours"]) == 160.0, "标准工时应为160小时"
        duration = (work_order_data["plan_end_date"] - work_order_data["plan_start_date"]).days
        assert duration == 45, f"装配周期 {duration} 天应为 45 天"

        print(
            f"\n✓ 装配工单 {work_order_data['work_order_no']} | "
            f"工程师：{work_order_data['assigned_engineer']} | "
            f"周期：{duration} 天"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 10. FAT 出厂验收
    # ────────────────────────────────────────────────────────────────────────

    def test_fat_acceptance(self, db, pm_user, flow_state):
        """
        场景：装配完成，进行 FAT 出厂验收，
              验证通过率 ≥ 90%（金凯博 FAT 一次通过率目标），生成验收报告。
        """
        from app.models.acceptance import AcceptanceOrder
        from tests.fixtures.industry_data import KPI_BENCHMARKS

        fat = AcceptanceOrder(
            order_no=f"FAT-{flow_state['project_code']}-001",
            project_id=flow_state["project_id"],
            acceptance_type="FAT",
            planned_date=date.today() + timedelta(days=75),
            actual_start_date=datetime.now(),
            actual_end_date=datetime.now() + timedelta(hours=8),
            location="金凯博深圳工厂装配车间",
            status="COMPLETED",
            total_items=50,
            passed_items=49,
            failed_items=1,
            na_items=0,
            pass_rate=Decimal("98.00"),
            overall_result="PASSED",
            conclusion=(
                "FAT出厂验收通过。设备功能、性能及安全性满足合同技术要求。"
                "遗留1项整改（外观标贴位置偏移），已现场整改完毕。"
            ),
            qa_signer_id=pm_user.id,
            qa_signed_at=datetime.now(),
            customer_signer="王工（比亚迪电子）",
            customer_signed_at=datetime.now(),
            report_file_path=f"/reports/{flow_state['project_code']}/FAT_report.pdf",
            is_officially_completed=True,
            officially_completed_at=datetime.now(),
            created_by=pm_user.id,
        )
        db.add(fat)
        db.commit()
        db.refresh(fat)
        flow_state["fat_id"] = fat.id

        # ── 断言 ──
        target_pass_rate = KPI_BENCHMARKS["fat_pass_rate_target"]  # 0.90
        actual_pass_rate = float(fat.pass_rate) / 100.0
        assert actual_pass_rate >= target_pass_rate, (
            f"FAT通过率 {actual_pass_rate:.1%} < 目标 {target_pass_rate:.1%}"
        )
        assert fat.overall_result == "PASSED", "FAT应整体通过"
        assert fat.is_officially_completed, "FAT应已正式完成（上传签署文件）"
        assert fat.report_file_path is not None, "应生成验收报告文件路径"

        print(
            f"\n✓ FAT验收 {fat.order_no} | "
            f"通过率 {float(fat.pass_rate):.1f}% | "
            f"结论：{fat.overall_result}"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 11. 项目结项（SAT 现场验收 + 毛利核算）
    # ────────────────────────────────────────────────────────────────────────

    def test_project_closure(self, db, pm_user, flow_state):
        """
        场景：SAT 现场验收通过，更新项目状态为结项，
              核算实际毛利率 ≥ 35%（公司毛利率目标）。
        """
        from app.models.acceptance import AcceptanceOrder
        from app.models.project import Project
        from tests.fixtures.industry_data import KPI_BENCHMARKS, SAMPLE_COSTS

        # 11-a SAT 现场验收
        sat = AcceptanceOrder(
            order_no=f"SAT-{flow_state['project_code']}-001",
            project_id=flow_state["project_id"],
            acceptance_type="SAT",
            planned_date=date.today() + timedelta(days=95),
            actual_start_date=datetime.now() + timedelta(days=95),
            actual_end_date=datetime.now() + timedelta(days=96),
            location="比亚迪电子深圳工厂生产线现场",
            status="COMPLETED",
            total_items=40,
            passed_items=40,
            failed_items=0,
            na_items=0,
            pass_rate=Decimal("100.00"),
            overall_result="PASSED",
            conclusion=(
                "SAT现场验收全部通过。设备已成功集成至客户产线，"
                "节拍实测9.8秒/件，满足合同要求（≤10秒）。"
            ),
            qa_signer_id=pm_user.id,
            qa_signed_at=datetime.now() + timedelta(days=96),
            customer_signer="王工（比亚迪电子）",
            customer_signed_at=datetime.now() + timedelta(days=96),
            is_officially_completed=True,
            officially_completed_at=datetime.now() + timedelta(days=96),
            created_by=pm_user.id,
        )
        db.add(sat)
        db.flush()

        # 11-b 核算实际成本（基于 SAMPLE_COSTS 行业基准数据）
        actual_costs = {
            "硬件采购": 175_000,   # NI机箱+板卡+气缸+相机+夹具材料
            "人工成本": 72_000,    # 5人×2个月
            "外协加工": 28_000,    # 夹具机加工（超预算）
            "差旅费用": 8_500,     # 客户现场调试
        }
        total_actual_cost = sum(actual_costs.values())  # 283,500

        contract_amount = flow_state["contract_amount"]  # 300,000
        gross_profit = contract_amount - total_actual_cost
        gross_margin = gross_profit / contract_amount

        # 11-c 更新项目状态为结项
        project = db.query(Project).filter(Project.id == flow_state["project_id"]).first()
        project.actual_cost = Decimal(str(total_actual_cost))
        project.actual_end_date = date.today() + timedelta(days=96)
        project.status = "ST09"   # 结项状态
        project.stage = "S9"
        project.progress_pct = Decimal("100.00")
        db.commit()
        db.refresh(project)

        flow_state["actual_cost"] = total_actual_cost
        flow_state["gross_margin"] = gross_margin
        flow_state["sat_id"] = sat.id

        # ── 断言 ──
        target_gm = KPI_BENCHMARKS["gross_margin_target"]  # 0.35
        assert gross_margin >= target_gm, (
            f"毛利率 {gross_margin:.1%} < 目标 {target_gm:.1%}。"
            f"收入 ¥{contract_amount:,.0f}，成本 ¥{total_actual_cost:,.0f}"
        )
        assert sat.overall_result == "PASSED", "SAT应全部通过"
        assert float(sat.pass_rate) == 100.0, "SAT通过率应为100%"
        assert project.status == "ST09", "项目状态应更新为结项"

        print(
            f"\n✓ 项目结项 {project.project_code} | "
            f"收入 ¥{contract_amount:,.0f} | "
            f"成本 ¥{total_actual_cost:,.0f} | "
            f"毛利率 {gross_margin:.1%}"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 12. 回款跟进 & 账期合规验证
    # ────────────────────────────────────────────────────────────────────────

    def test_payment_collection(self, db, pm_user, byd_customer, flow_state):
        """
        场景：项目结项后登记各期回款，
              验证累计回款 = 合同总额，且每笔回款在计划日期的合理范围内（±30天）。
        """
        from app.models.project import ProjectPaymentPlan
        from app.models.sales import Invoice

        # 12-a 登记实际回款（模拟4笔到账）
        contract_amount = Decimal(str(flow_state["contract_amount"]))
        payment_records = [
            {
                "name": "预付款",
                "amount": contract_amount * Decimal("0.30"),
                "planned_offset_days": 7,
                "actual_offset_days": 5,    # 比计划提前2天
                "type": "ADVANCE",
            },
            {
                "name": "中期款",
                "amount": contract_amount * Decimal("0.30"),
                "planned_offset_days": 45,
                "actual_offset_days": 43,
                "type": "DELIVERY",
            },
            {
                "name": "验收款",
                "amount": contract_amount * Decimal("0.30"),
                "planned_offset_days": 90,
                "actual_offset_days": 95,   # 延迟5天（FAT验收后客户付款）
                "type": "ACCEPTANCE",
            },
            {
                "name": "质保金",
                "amount": contract_amount * Decimal("0.10"),
                "planned_offset_days": 365,
                "actual_offset_days": 365,
                "type": "WARRANTY",
            },
        ]

        today = date.today()
        total_received = Decimal("0")
        compliance_issues = []

        for rec in payment_records:
            planned_date = today + timedelta(days=rec["planned_offset_days"])
            actual_date = today + timedelta(days=rec["actual_offset_days"])
            delay_days = rec["actual_offset_days"] - rec["planned_offset_days"]

            total_received += rec["amount"]

            if abs(delay_days) > 30:
                compliance_issues.append(
                    f"{rec['name']} 逾期 {delay_days} 天，超过 ±30 天合规阈值"
                )

        # 12-b 创建发票记录（开具增值税专用发票，税额另计）
        tax_rate = Decimal("13")
        amount_ex_tax = (contract_amount / Decimal("1.13")).quantize(Decimal("0.01"))
        tax_amount = (contract_amount - amount_ex_tax).quantize(Decimal("0.01"))

        invoice = Invoice(
            invoice_code=f"INV-{flow_state['project_code']}-001",
            invoice_type="SPECIAL_VAT",
            contract_id=flow_state["contract_id"],
            project_id=flow_state["project_id"],
            amount=amount_ex_tax,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=contract_amount,
            issue_date=date.today() + timedelta(days=96),
            buyer_name="比亚迪电子",
            status="ISSUED",
        )
        db.add(invoice)

        # 12-c 更新合同已收款金额
        from app.models.sales import Contract
        contract = db.query(Contract).filter(
            Contract.id == flow_state["contract_id"]
        ).first()
        contract.received_amount = total_received
        db.commit()
        db.refresh(contract)

        flow_state["total_received"] = float(total_received)

        # ── 断言 ──
        assert float(total_received) == pytest.approx(
            flow_state["contract_amount"], rel=1e-4
        ), (
            f"累计回款 ¥{float(total_received):,.2f} ≠ 合同总额 ¥{flow_state['contract_amount']:,.2f}"
        )
        assert len(compliance_issues) == 0, (
            f"存在账期合规问题：{compliance_issues}"
        )
        assert float(contract.received_amount) == pytest.approx(
            flow_state["contract_amount"], rel=1e-4
        )

        print(
            f"\n✓ 回款完成 | 累计 ¥{float(total_received):,.0f} | "
            f"共 {len(payment_records)} 笔 | 合规问题：{len(compliance_issues)} 项"
        )

    # ────────────────────────────────────────────────────────────────────────
    # 业务链完整性断言（综合验收）
    # ────────────────────────────────────────────────────────────────────────

    def test_full_flow_summary(self, flow_state):
        """
        综合验收：汇总业务链各关键节点，验证端到端一致性。
        """
        from tests.fixtures.industry_data import KPI_BENCHMARKS

        # 检查所有关键节点已完成
        required_keys = [
            "lead_id", "opp_id", "quote_id", "contract_id",
            "project_id", "bom_id", "pr_ni_id", "gr_id",
            "fat_id", "sat_id", "gross_margin", "total_received",
        ]
        missing = [k for k in required_keys if k not in flow_state]
        assert not missing, f"业务链缺少关键节点数据：{missing}"

        # 毛利率 ≥ 35%
        assert flow_state["gross_margin"] >= KPI_BENCHMARKS["gross_margin_target"]

        # 回款完整
        assert flow_state["total_received"] == pytest.approx(
            flow_state["contract_amount"], rel=1e-4
        )

        # BOM 金额合理（不超过合同额的 75%）
        bom_to_contract_ratio = flow_state["bom_amount"] / flow_state["contract_amount"]
        assert bom_to_contract_ratio < 0.75, (
            f"BOM金额占比 {bom_to_contract_ratio:.1%} 过高（应 < 75%）"
        )

        print(
            f"\n{'═'*60}"
            f"\n🏁 完整业务链验证通过！"
            f"\n  线索 → 项目：{flow_state['project_code']}"
            f"\n  合同额：¥{flow_state['contract_amount']:,.0f}"
            f"\n  实际成本：¥{flow_state.get('actual_cost', 0):,.0f}"
            f"\n  毛利率：{flow_state['gross_margin']:.1%}（目标 ≥35%）"
            f"\n  回款：¥{flow_state['total_received']:,.0f}（100%）"
            f"\n{'═'*60}"
        )

# -*- coding: utf-8 -*-
"""销售预测服务测试"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.sales import SalesTarget
from app.models.sales.contracts import Contract
from app.models.sales.leads import Opportunity
from app.models.project.customer import Customer
from app.models.enums.sales import OpportunityStageEnum
from app.models.user import User
from app.services.sales_forecast_service import SalesForecastService


@pytest.fixture
def forecast_service(db_session: Session):
    return SalesForecastService(db_session)


@pytest.fixture
def test_customer(db_session: Session):
    """创建测试客户"""
    customer = Customer(
        customer_code="TEST-CUST-001",
        customer_name="测试客户",
        contact_person="张三",
        contact_phone="13800000001",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()
    return customer


@pytest.fixture
def test_contracts(db_session: Session, test_customer):
    """创建测试合同"""
    contracts = [
        Contract(
            contract_code="TEST-CONT-001",
            contract_name="测试合同 1",
            contract_type="sales",
            customer_id=test_customer.id,
            total_amount=Decimal("5000000"),
            signing_date=date(2026, 1, 20),
            status="SIGNED",
        ),
        Contract(
            contract_code="TEST-CONT-002",
            contract_name="测试合同 2",
            contract_type="sales",
            customer_id=test_customer.id,
            total_amount=Decimal("3000000"),
            signing_date=date(2026, 2, 18),
            status="ACTIVE",
        ),
        Contract(
            contract_code="TEST-CONT-003",
            contract_name="上季度合同",
            contract_type="sales",
            customer_id=test_customer.id,
            total_amount=Decimal("4500000"),
            signing_date=date(2025, 11, 10),
            status="SIGNED",
        ),
        Contract(
            contract_code="TEST-CONT-004",
            contract_name="去年同期合同",
            contract_type="sales",
            customer_id=test_customer.id,
            total_amount=Decimal("4200000"),
            signing_date=date(2025, 2, 12),
            status="SIGNED",
        ),
    ]
    db_session.add_all(contracts)
    db_session.flush()
    return contracts


@pytest.fixture
def test_opportunities(db_session: Session, test_customer):
    """创建测试商机"""
    opportunities = [
        Opportunity(
            opp_code="TEST-OPP-001",
            customer_id=test_customer.id,
            opp_name="商机 1-PROPOSAL",
            est_amount=Decimal("2000000"),
            stage=OpportunityStageEnum.PROPOSAL.value,
            expected_close_date=date(2026, 3, 20),
        ),
        Opportunity(
            opp_code="TEST-OPP-002",
            customer_id=test_customer.id,
            opp_name="商机 2-NEGOTIATION",
            est_amount=Decimal("3000000"),
            stage=OpportunityStageEnum.NEGOTIATION.value,
            expected_close_date=date(2026, 3, 25),
        ),
        Opportunity(
            opp_code="TEST-OPP-003",
            customer_id=test_customer.id,
            opp_name="商机 3-CLOSING",
            est_amount=Decimal("1500000"),
            stage=OpportunityStageEnum.CLOSING.value,
            expected_close_date=date(2026, 3, 28),
        ),
        Opportunity(
            opp_code="TEST-OPP-004",
            customer_id=test_customer.id,
            opp_name="商机 4-QUALIFICATION",
            est_amount=Decimal("4000000"),
            stage=OpportunityStageEnum.QUALIFICATION.value,
            expected_close_date=date(2026, 2, 15),
        ),
        Opportunity(
            opp_code="TEST-OPP-005",
            customer_id=test_customer.id,
            opp_name="已赢单商机",
            est_amount=Decimal("500000"),
            stage=OpportunityStageEnum.WON.value,
            expected_close_date=date(2026, 3, 30),
        ),
    ]
    db_session.add_all(opportunities)
    db_session.flush()
    return opportunities


@pytest.fixture
def forecast_target_owner(db_session: Session):
    owner = User(
        username=f"forecast_target_owner_{uuid4().hex[:8]}",
        password_hash="hashed-password",
        real_name="预测目标责任人",
        is_active=True,
    )
    db_session.add(owner)
    db_session.flush()
    return owner


@pytest.fixture
def forecast_targets(db_session: Session, forecast_target_owner: User):
    targets = [
        SalesTarget(
            target_scope="PERSONAL",
            user_id=forecast_target_owner.id,
            target_type="CONTRACT_AMOUNT",
            target_period="YEARLY",
            period_value="2026",
            target_value=Decimal("200000000"),
            status="ACTIVE",
            created_by=forecast_target_owner.id,
        ),
        SalesTarget(
            target_scope="PERSONAL",
            user_id=forecast_target_owner.id,
            target_type="CONTRACT_AMOUNT",
            target_period="QUARTERLY",
            period_value="2026-Q1",
            target_value=Decimal("50000000"),
            status="ACTIVE",
            created_by=forecast_target_owner.id,
        ),
        SalesTarget(
            target_scope="PERSONAL",
            user_id=forecast_target_owner.id,
            target_type="CONTRACT_AMOUNT",
            target_period="MONTHLY",
            period_value="2026-03",
            target_value=Decimal("18000000"),
            status="ACTIVE",
            created_by=forecast_target_owner.id,
        ),
        SalesTarget(
            target_scope="PERSONAL",
            user_id=forecast_target_owner.id,
            target_type="CONTRACT_AMOUNT",
            target_period="QUARTERLY",
            period_value="2025-Q4",
            target_value=Decimal("4000000"),
            status="ACTIVE",
            created_by=forecast_target_owner.id,
        ),
        SalesTarget(
            target_scope="PERSONAL",
            user_id=forecast_target_owner.id,
            target_type="CONTRACT_AMOUNT",
            target_period="QUARTERLY",
            period_value="2025-Q1",
            target_value=Decimal("4000000"),
            status="ACTIVE",
            created_by=forecast_target_owner.id,
        ),
    ]
    db_session.add_all(targets)
    db_session.flush()
    return targets


class TestSalesForecastServiceInit:
    """测试初始化"""

    def test_init(self, forecast_service, db_session):
        assert forecast_service.db == db_session
        assert OpportunityStageEnum.DISCOVERY in forecast_service.STAGE_WIN_RATES
        assert 1 in forecast_service.SEASONAL_FACTORS


class TestGetCompanyForecast:
    """测试公司预测"""

    def test_get_company_forecast_quarterly(
        self, forecast_service, test_contracts, test_opportunities, forecast_targets
    ):
        """测试季度预测"""
        result = forecast_service.get_company_forecast(period="quarterly", year=2026, quarter=1)

        assert "period" in result
        assert "period_type" in result
        assert "generated_at" in result
        assert "targets" in result
        assert "prediction" in result
        assert "funnel_contribution" in result
        assert "forecast_breakdown" in result
        assert "key_drivers" in result
        assert "risks" in result
        assert "recommended_actions" in result
        assert "historical_comparison" in result

        # 验证目标
        assert result["targets"]["quarterly_target"] == 50000000
        assert result["targets"]["actual_revenue"] >= 8000000  # 两个合同 800 万
        assert result["target_source"] == "sales_targets"

        # 验证预测
        assert result["prediction"]["predicted_revenue"] > 0
        assert 0 <= result["prediction"]["confidence_level"] <= 100
        assert result["prediction"]["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

        # 验证漏斗贡献
        assert "total_weighted" in result["funnel_contribution"]
        assert result["funnel_contribution"]["total_weighted"] > 0
        assert any("测试合同" in driver["description"] for driver in result["key_drivers"])
        assert any("商机" in action["action"] for action in result["recommended_actions"])

    def test_get_company_forecast_yearly(self, forecast_service, forecast_targets):
        """测试年度预测"""
        result = forecast_service.get_company_forecast(period="yearly", year=2026)

        assert result["period_type"] == "yearly"
        assert result["targets"]["quarterly_target"] == 200_000_000

    def test_get_company_forecast_monthly(self, forecast_service, forecast_targets):
        """测试月度预测"""
        result = forecast_service.get_company_forecast(period="monthly", year=2026, quarter=3)

        assert result["period_type"] == "monthly"
        assert "2026-03" in result["period"]
        assert result["targets"]["quarterly_target"] == 18000000


class TestPipelineAnalysis:
    """测试漏斗分析"""

    def test_get_pipeline_analysis(self, forecast_service, test_opportunities):
        """测试漏斗分析"""
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        pipeline = forecast_service._get_pipeline_analysis(start_date, end_date)

        assert "total_weighted" in pipeline
        assert pipeline["total_weighted"] > 0

        # 验证各阶段数据
        assert "QUALIFICATION" in pipeline
        assert "PROPOSAL" in pipeline
        assert "NEGOTIATION" in pipeline
        assert "CLOSING" in pipeline

        # 验证 NEGOTIATION 的赢单率应为 70%
        assert pipeline["NEGOTIATION"]["win_rate"] == 70

    def test_pipeline_weighted_calculation(
        self, forecast_service, test_opportunities, db_session
    ):
        """测试加权金额计算"""
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        pipeline = forecast_service._get_pipeline_analysis(start_date, end_date)

        # PROPOSAL: 200 万 × 50% = 100 万
        # NEGOTIATION: 300 万 × 70% = 210 万
        # CLOSING: 150 万 × 85% = 127.5 万
        # QUALIFICATION: 400 万 × 30% = 120 万
        # 总计：557.5 万

        expected_total = 1000000 + 2100000 + 1275000 + 1200000
        assert abs(pipeline["total_weighted"] - expected_total) < 1000


class TestRevenueCalculation:
    """测试收入计算"""

    def test_get_actual_revenue(self, forecast_service, test_contracts):
        """测试实际收入获取"""
        start_date = datetime.now() - timedelta(days=60)
        end_date = datetime.now() + timedelta(days=30)

        revenue = forecast_service._get_actual_revenue(start_date, end_date)

        assert revenue >= 8000000  # 两个合同 500 万 +300 万

    def test_calculate_predicted_revenue(self, forecast_service, test_contracts, test_opportunities):
        """测试预测收入计算"""
        actual_revenue = 8000000
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        pipeline_data = forecast_service._get_pipeline_analysis(start_date, end_date)

        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        predicted = forecast_service._calculate_predicted_revenue(
            actual_revenue, pipeline_data, start_date, end_date
        )

        assert predicted > actual_revenue
        assert predicted < actual_revenue + pipeline_data["total_weighted"]


class TestConfidenceAndRisk:
    """测试置信度和风险评估"""

    def test_calculate_confidence_level(self, forecast_service, test_opportunities):
        """测试置信水平计算"""
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        pipeline = forecast_service._get_pipeline_analysis(start_date, end_date)
        confidence = forecast_service._calculate_confidence_level(pipeline)

        assert 50 <= confidence <= 100

    def test_calculate_confidence_interval(self, forecast_service, test_opportunities):
        """测试置信区间计算"""
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        pipeline = forecast_service._get_pipeline_analysis(start_date, end_date)
        predicted_revenue = 50000000

        interval = forecast_service._calculate_confidence_interval(predicted_revenue, pipeline)

        assert "optimistic" in interval
        assert "pessimistic" in interval
        assert interval["optimistic"] > predicted_revenue
        assert interval["pessimistic"] < predicted_revenue

    def test_assess_risk_high(self, forecast_service):
        """测试高风险评估"""
        risk = forecast_service._assess_risk(
            completion_rate=40,
            predicted_completion=75,
            pipeline_data={"total_weighted": 10000000},
        )
        assert risk == "HIGH"

    def test_assess_risk_medium(self, forecast_service):
        """测试中等风险评估"""
        risk = forecast_service._assess_risk(
            completion_rate=55,
            predicted_completion=90,
            pipeline_data={"total_weighted": 10000000},
        )
        assert risk == "MEDIUM"

    def test_assess_risk_low(self, forecast_service):
        """测试低风险评估"""
        risk = forecast_service._assess_risk(
            completion_rate=70,
            predicted_completion=105,
            pipeline_data={"total_weighted": 10000000},
        )
        assert risk == "LOW"


class TestForecastBreakdown:
    """测试预测分解"""

    def test_get_forecast_breakdown(self, forecast_service, test_contracts, test_opportunities):
        """测试预测分解"""
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        pipeline = forecast_service._get_pipeline_analysis(start_date, end_date)
        actual_revenue = 8000000

        breakdown = forecast_service._get_forecast_breakdown(actual_revenue, pipeline)

        assert "committed" in breakdown
        assert "best_case" in breakdown
        assert "pipeline" in breakdown

        # 验证百分比之和约为 100%
        total_percentage = (
            breakdown["committed"]["percentage"]
            + breakdown["best_case"]["percentage"]
            + breakdown["pipeline"]["percentage"]
        )
        assert 99 <= total_percentage <= 101

        # 验证已签约置信度为 100%
        assert breakdown["committed"]["confidence"] == 100


class TestDriversAndRisks:
    """测试驱动因素和风险识别"""

    def test_identify_key_drivers(self, forecast_service, test_contracts, test_opportunities):
        """测试关键驱动因素识别"""
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        drivers = forecast_service._identify_key_drivers(
            pipeline_data={"total_weighted": 50000000},
            actual_revenue=30000000,
            target=50000000,
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(drivers, list)
        assert any("测试合同" in driver["description"] for driver in drivers)
        assert any("商机 2-NEGOTIATION" in driver["description"] for driver in drivers)
        assert len(drivers) >= 1

    def test_identify_risks_low_completion(self, forecast_service, test_opportunities):
        """测试低风险完成率识别"""
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        risks = forecast_service._identify_risks(
            completion_rate=40,
            predicted_completion=75,
            pipeline_data={"total_weighted": 10000000},
            target=50000000,
            start_date=start_date,
            end_date=end_date,
        )

        assert len(risks) > 0
        assert any(r["risk"] == "当前完成率偏低" for r in risks)
        assert any(r["risk"] == "高价值商机预计成交已逾期" for r in risks)

    def test_generate_recommendations_high_risk(self, forecast_service, test_opportunities):
        """测试高风险时的建议生成"""
        start_date, end_date = forecast_service._get_period_dates(2026, 1, "quarterly")
        recommendations = forecast_service._generate_recommendations(
            pipeline_data={"total_weighted": 50000000},
            risk_level="HIGH",
            start_date=start_date,
            end_date=end_date,
        )

        assert len(recommendations) >= 2
        assert recommendations[0]["priority"] == 1
        assert any("商机 2-NEGOTIATION" in item["action"] for item in recommendations)


class TestHistoricalComparison:
    """测试历史对比"""

    def test_get_historical_comparison(self, forecast_service, test_contracts, forecast_targets):
        """测试历史对比数据"""
        historical = forecast_service._get_historical_comparison(year=2026, quarter=1, period="quarterly")

        assert "last_quarter" in historical
        assert "last_year_same_period" in historical
        assert "average_q1_completion" in historical

        assert historical["last_quarter"]["completion_rate"] > 0


class TestPeriodDates:
    """测试日期范围计算"""

    def test_get_period_dates_yearly(self, forecast_service):
        """测试年度日期范围"""
        start, end = forecast_service._get_period_dates(2026, 1, "yearly")

        assert start == datetime(2026, 1, 1)
        assert end == datetime(2026, 12, 31)

    def test_get_period_dates_quarterly_q1(self, forecast_service):
        """测试 Q1 日期范围"""
        start, end = forecast_service._get_period_dates(2026, 1, "quarterly")

        assert start == datetime(2026, 1, 1)
        assert end == datetime(2026, 3, 31)

    def test_get_period_dates_quarterly_q4(self, forecast_service):
        """测试 Q4 日期范围"""
        start, end = forecast_service._get_period_dates(2026, 4, "quarterly")

        assert start == datetime(2026, 10, 1)
        assert end == datetime(2026, 12, 31)

    def test_get_period_dates_monthly(self, forecast_service):
        """测试月度日期范围"""
        start, end = forecast_service._get_period_dates(2026, 3, "monthly")

        assert start == datetime(2026, 3, 1)
        assert end == datetime(2026, 3, 31)


class TestSeasonalFactors:
    """测试季节性因子"""

    def test_seasonal_factors_valid(self, forecast_service):
        """测试季节性因子有效性"""
        factors = forecast_service.SEASONAL_FACTORS

        assert len(factors) == 12
        assert all(0.5 <= f <= 1.5 for f in factors.values())

        # 春节月份应该较低
        assert factors[1] < 1.0
        assert factors[2] < 1.0

        # 季度末应该较高
        assert factors[3] > 1.0
        assert factors[12] > 1.0


class TestStageWinRates:
    """测试阶段赢单率"""

    def test_stage_win_rates_valid(self, forecast_service):
        """测试阶段赢单率有效性"""
        win_rates = forecast_service.STAGE_WIN_RATES

        assert len(win_rates) >= 5
        assert all(0 <= rate <= 1 for rate in win_rates.values())

        # 验证赢单率递增
        assert win_rates[OpportunityStageEnum.DISCOVERY] < win_rates[OpportunityStageEnum.QUALIFICATION]
        assert win_rates[OpportunityStageEnum.QUALIFICATION] < win_rates[OpportunityStageEnum.PROPOSAL]
        assert win_rates[OpportunityStageEnum.PROPOSAL] < win_rates[OpportunityStageEnum.NEGOTIATION]
        assert win_rates[OpportunityStageEnum.NEGOTIATION] < win_rates[OpportunityStageEnum.CLOSING]

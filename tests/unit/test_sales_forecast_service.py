# -*- coding: utf-8 -*-
"""
销售预测服务测试
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract
from app.models.sales.leads import Opportunity
from app.models.project.customer import Customer
from app.models.enums.sales import OpportunityStageEnum
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
            customer_id=test_customer.id,
            total_amount=Decimal("5000000"),
            signing_date=datetime.now() - timedelta(days=30),
            status="ACTIVE",
        ),
        Contract(
            contract_code="TEST-CONT-002",
            contract_name="测试合同 2",
            customer_id=test_customer.id,
            total_amount=Decimal("3000000"),
            signing_date=datetime.now() - timedelta(days=15),
            status="ACTIVE",
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
            opportunity_code="TEST-OPP-001",
            customer_id=test_customer.id,
            name="商机 1-PROPOSAL",
            estimated_amount=Decimal("2000000"),
            stage=OpportunityStageEnum.PROPOSAL,
            outcome=None,
        ),
        Opportunity(
            opportunity_code="TEST-OPP-002",
            customer_id=test_customer.id,
            name="商机 2-NEGOTIATION",
            estimated_amount=Decimal("3000000"),
            stage=OpportunityStageEnum.NEGOTIATION,
            outcome=None,
        ),
        Opportunity(
            opportunity_code="TEST-OPP-003",
            customer_id=test_customer.id,
            name="商机 3-CLOSING",
            estimated_amount=Decimal("1500000"),
            stage=OpportunityStageEnum.CLOSING,
            outcome=None,
        ),
        Opportunity(
            opportunity_code="TEST-OPP-004",
            customer_id=test_customer.id,
            name="商机 4-QUALIFICATION",
            estimated_amount=Decimal("4000000"),
            stage=OpportunityStageEnum.QUALIFICATION,
            outcome=None,
        ),
    ]
    db_session.add_all(opportunities)
    db_session.flush()
    return opportunities


class TestSalesForecastServiceInit:
    """测试初始化"""

    def test_init(self, forecast_service, db_session):
        assert forecast_service.db == db_session
        assert OpportunityStageEnum.DISCOVERY in forecast_service.STAGE_WIN_RATES
        assert 1 in forecast_service.SEASONAL_FACTORS


class TestGetCompanyForecast:
    """测试公司预测"""

    def test_get_company_forecast_quarterly(
        self, forecast_service, test_contracts, test_opportunities
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
        assert result["targets"]["quarterly_target"] > 0
        assert result["targets"]["actual_revenue"] >= 8000000  # 两个合同 800 万

        # 验证预测
        assert result["prediction"]["predicted_revenue"] > 0
        assert 0 <= result["prediction"]["confidence_level"] <= 100
        assert result["prediction"]["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

        # 验证漏斗贡献
        assert "total_weighted" in result["funnel_contribution"]
        assert result["funnel_contribution"]["total_weighted"] > 0

    def test_get_company_forecast_yearly(self, forecast_service):
        """测试年度预测"""
        result = forecast_service.get_company_forecast(period="yearly", year=2026)

        assert result["period_type"] == "yearly"
        assert result["targets"]["quarterly_target"] == 200_000_000  # 年度目标 2 亿

    def test_get_company_forecast_monthly(self, forecast_service):
        """测试月度预测"""
        result = forecast_service.get_company_forecast(period="monthly", year=2026, quarter=3)

        assert result["period_type"] == "monthly"
        assert "2026-03" in result["period"]


class TestPipelineAnalysis:
    """测试漏斗分析"""

    def test_get_pipeline_analysis(self, forecast_service, test_opportunities):
        """测试漏斗分析"""
        pipeline = forecast_service._get_pipeline_analysis()

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
        pipeline = forecast_service._get_pipeline_analysis()

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
        pipeline_data = forecast_service._get_pipeline_analysis()

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() + timedelta(days=60)

        predicted = forecast_service._calculate_predicted_revenue(
            actual_revenue, pipeline_data, start_date, end_date
        )

        assert predicted > actual_revenue
        assert predicted < actual_revenue + pipeline_data["total_weighted"]


class TestConfidenceAndRisk:
    """测试置信度和风险评估"""

    def test_calculate_confidence_level(self, forecast_service, test_opportunities):
        """测试置信水平计算"""
        pipeline = forecast_service._get_pipeline_analysis()
        confidence = forecast_service._calculate_confidence_level(pipeline)

        assert 50 <= confidence <= 100

    def test_calculate_confidence_interval(self, forecast_service, test_opportunities):
        """测试置信区间计算"""
        pipeline = forecast_service._get_pipeline_analysis()
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
        pipeline = forecast_service._get_pipeline_analysis()
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

    def test_identify_key_drivers(self, forecast_service):
        """测试关键驱动因素识别"""
        drivers = forecast_service._identify_key_drivers(
            pipeline_data={"total_weighted": 50000000},
            actual_revenue=30000000,
            target=50000000,
        )

        assert isinstance(drivers, list)
        # 至少应该有季节性因素或大客户因素
        assert len(drivers) >= 1

    def test_identify_risks_low_completion(self, forecast_service):
        """测试低风险完成率识别"""
        risks = forecast_service._identify_risks(
            completion_rate=40,
            predicted_completion=75,
            pipeline_data={"total_weighted": 10000000},
        )

        assert len(risks) > 0
        assert any(r["risk"] == "当前完成率偏低" for r in risks)

    def test_generate_recommendations_high_risk(self, forecast_service):
        """测试高风险时的建议生成"""
        recommendations = forecast_service._generate_recommendations(
            pipeline_data={"total_weighted": 50000000},
            risk_level="HIGH",
        )

        assert len(recommendations) >= 2
        assert recommendations[0]["priority"] == 1


class TestHistoricalComparison:
    """测试历史对比"""

    def test_get_historical_comparison(self, forecast_service):
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

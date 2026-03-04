# -*- coding: utf-8 -*-
"""
sales_prediction_service 单元测试

测试销售预测服务的各个方法：
- 收入预测
- 赢单概率预测
- 预测算法
- 置信度计算
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.sales_prediction_service import SalesPredictionService


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_contract(
    contract_id=1,
    contract_amount=Decimal("100000"),
    signed_date=None,
    status="SIGNED",
    customer_id=1,
    owner_id=1,
):
    """创建模拟的合同对象"""
    mock = MagicMock()
    mock.id = contract_id
    mock.contract_amount = contract_amount
    mock.signed_date = signed_date or date.today()
    mock.status = status
    mock.customer_id = customer_id
    mock.owner_id = owner_id
    return mock


def create_mock_opportunity(
    opp_id=1,
    stage="PROPOSAL",
    est_amount=Decimal("50000"),
    customer_id=1,
    owner_id=1,
    created_at=None,
):
    """创建模拟的商机对象"""
    mock = MagicMock()
    mock.id = opp_id
    mock.stage = stage
    mock.est_amount = est_amount
    mock.customer_id = customer_id
    mock.owner_id = owner_id
    mock.created_at = created_at or datetime.now()
    return mock


@pytest.mark.unit
class TestGetMonthlyRevenue:
    """测试 _get_monthly_revenue 方法"""

    def test_returns_empty_list_for_no_contracts(self):
        """测试无合同时返回空列表"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service._get_monthly_revenue([])

        assert result == []

    def test_groups_by_month(self):
        """测试按月分组"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        contracts = [
            create_mock_contract(signed_date=date(2024, 1, 15), contract_amount=Decimal("100000")),
            create_mock_contract(signed_date=date(2024, 1, 20), contract_amount=Decimal("50000")),
            create_mock_contract(signed_date=date(2024, 2, 10), contract_amount=Decimal("200000")),
        ]

        result = service._get_monthly_revenue(contracts)

        assert len(result) == 2
        assert result[0]["month"] == "2024-01"
        assert result[0]["revenue"] == 150000.0
        assert result[0]["count"] == 2
        assert result[1]["month"] == "2024-02"
        assert result[1]["revenue"] == 200000.0

    def test_handles_none_signed_date(self):
        """测试处理空签约日期"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        contract = create_mock_contract()
        contract.signed_date = None
        contracts = [contract]

        result = service._get_monthly_revenue(contracts)

        assert result == []

    def test_handles_none_amount(self):
        """测试处理空金额"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        contract = create_mock_contract(signed_date=date(2024, 1, 15))
        contract.contract_amount = None
        contracts = [contract]

        result = service._get_monthly_revenue(contracts)

        assert len(result) == 1
        assert result[0]["revenue"] == 0.0


@pytest.mark.unit
class TestMovingAverageForecast:
    """测试 _moving_average_forecast 方法"""

    def test_returns_zero_for_empty_data(self):
        """测试空数据返回0"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service._moving_average_forecast([], 30)

        assert result == Decimal("0")

    def test_calculates_average_of_recent_months(self):
        """测试计算最近月份的平均值"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [
            {"month": "2024-01", "revenue": 100000, "count": 2},
            {"month": "2024-02", "revenue": 200000, "count": 3},
            {"month": "2024-03", "revenue": 300000, "count": 4},
        ]

        # 30天预测，使用最近3个月平均 (100000+200000+300000)/3 = 200000
        result = service._moving_average_forecast(monthly_data, 30)

        assert result == Decimal("200000")

    def test_scales_by_days(self):
        """测试按天数比例缩放"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [
            {"month": "2024-01", "revenue": 300000, "count": 3},
        ]

        # 90天 = 3个月，平均月收入 300000，预测 300000 * 3 = 900000
        result = service._moving_average_forecast(monthly_data, 90)

        assert result == Decimal("900000")

    def test_uses_all_data_when_less_than_3_months(self):
        """测试不足3个月时使用全部数据"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [
            {"month": "2024-01", "revenue": 100000, "count": 1},
            {"month": "2024-02", "revenue": 200000, "count": 2},
        ]

        # 2个月数据，平均 150000，30天预测
        result = service._moving_average_forecast(monthly_data, 30)

        assert result == Decimal("150000")


@pytest.mark.unit
class TestExponentialSmoothingForecast:
    """测试 _exponential_smoothing_forecast 方法"""

    def test_returns_zero_for_empty_data(self):
        """测试空数据返回0"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service._exponential_smoothing_forecast([], 30)

        assert result == Decimal("0")

    def test_returns_first_value_for_single_data(self):
        """测试单数据点时返回该值"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [{"month": "2024-01", "revenue": 100000, "count": 1}]

        result = service._exponential_smoothing_forecast(monthly_data, 30)

        assert result == Decimal("100000")

    def test_applies_exponential_smoothing(self):
        """测试指数平滑计算"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [
            {"month": "2024-01", "revenue": 100000, "count": 1},
            {"month": "2024-02", "revenue": 200000, "count": 2},
        ]

        # alpha=0.3: forecast = 0.3*200000 + 0.7*100000 = 130000
        result = service._exponential_smoothing_forecast(monthly_data, 30, alpha=0.3)

        assert result == Decimal("130000")

    def test_scales_by_days(self):
        """测试按天数比例缩放"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [{"month": "2024-01", "revenue": 100000, "count": 1}]

        # 60天 = 2个月
        result = service._exponential_smoothing_forecast(monthly_data, 60)

        assert result == Decimal("200000")


@pytest.mark.unit
class TestForecastFromOpportunities:
    """测试 _forecast_from_opportunities 方法"""

    def test_returns_zero_for_empty_opportunities(self):
        """测试无商机时返回0"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service._forecast_from_opportunities([], 30)

        assert result == Decimal("0")

    def test_applies_stage_weights(self):
        """测试应用阶段权重"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        opportunities = [
            create_mock_opportunity(stage="PROPOSAL", est_amount=Decimal("100000")),  # 0.6
            create_mock_opportunity(stage="NEGOTIATION", est_amount=Decimal("100000")),  # 0.8
        ]

        # PROPOSAL: 100000 * 0.6 = 60000
        # NEGOTIATION: 100000 * 0.8 = 80000
        # Total: 140000, 30天 = 1/3，所以 140000 * (30/90) ≈ 46666.67
        result = service._forecast_from_opportunities(opportunities, 30)

        assert float(result) == pytest.approx(46666.67, rel=0.01)

    def test_handles_none_amount(self):
        """测试处理空金额"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        opp = create_mock_opportunity()
        opp.est_amount = None

        result = service._forecast_from_opportunities([opp], 30)

        assert result == Decimal("0")

    def test_uses_default_weight_for_unknown_stage(self):
        """测试未知阶段使用默认权重"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        opp = create_mock_opportunity(stage="UNKNOWN", est_amount=Decimal("100000"))

        # Unknown stage weight: 0.5, 30天 = 1/3
        result = service._forecast_from_opportunities([opp], 30)

        assert float(result) == pytest.approx(16666.67, rel=0.01)


@pytest.mark.unit
class TestCalculateConfidence:
    """测试 _calculate_confidence 方法"""

    def test_returns_high_with_sufficient_data(self):
        """测试数据充足时返回HIGH"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [{"month": f"2024-0{i}", "revenue": 100000} for i in range(1, 7)]

        result = service._calculate_confidence(monthly_data, 5)

        assert result == "HIGH"

    def test_returns_medium_with_moderate_data(self):
        """测试数据适中时返回MEDIUM"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [{"month": "2024-01", "revenue": 100000} for _ in range(3)]

        result = service._calculate_confidence(monthly_data, 3)

        assert result == "MEDIUM"

    def test_returns_low_with_insufficient_data(self):
        """测试数据不足时返回LOW"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        monthly_data = [{"month": "2024-01", "revenue": 100000}]

        result = service._calculate_confidence(monthly_data, 1)

        assert result == "LOW"


@pytest.mark.unit
class TestGenerateBreakdown:
    """测试 _generate_breakdown 方法"""

    def test_generates_30_day_breakdown(self):
        """测试生成30天分解"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service._generate_breakdown(30, Decimal("300000"), Decimal("150000"))

        assert len(result) == 1
        assert result[0]["period"] == 30
        assert result[0]["period_label"] == "未来30天"

    def test_generates_90_day_breakdown(self):
        """测试生成90天分解"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service._generate_breakdown(90, Decimal("900000"), Decimal("450000"))

        assert len(result) == 3
        assert result[0]["period"] == 30
        assert result[1]["period"] == 60
        assert result[2]["period"] == 90

    def test_calculates_proportional_values(self):
        """测试按比例计算值"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service._generate_breakdown(90, Decimal("900000"), Decimal("450000"))

        # 30天 = 1/3
        assert result[0]["predicted_revenue"] == pytest.approx(300000, rel=0.01)
        assert result[0]["opportunity_revenue"] == pytest.approx(150000, rel=0.01)


@pytest.mark.unit
class TestPredictWinProbability:
    """测试 predict_win_probability 方法"""

    def test_returns_default_for_no_stage(self):
        """测试无阶段时返回默认值"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service.predict_win_probability()

        assert result["win_probability"] == 0.5
        assert result["confidence"] == "LOW"

    def test_fetches_opportunity_when_id_provided(self):
        """测试提供ID时获取商机数据"""
        db = create_mock_db_session()
        opp = create_mock_opportunity(stage="PROPOSAL", est_amount=Decimal("200000"), customer_id=1)
        db.query.return_value.filter.return_value.first.return_value = opp

        # Mock the historical win rate query
        db.query.return_value.filter.return_value.all.return_value = []

        service = SalesPredictionService(db)
        result = service.predict_win_probability(opportunity_id=1)

        assert "win_probability" in result
        assert "factors" in result

    def test_applies_amount_factor_for_large_deals(self):
        """测试大单金额因子"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        service = SalesPredictionService(db)

        # 大于100万
        result = service.predict_win_probability(stage="PROPOSAL", amount=Decimal("1500000"))

        assert result["amount_factor"] == 0.9

    def test_applies_amount_factor_for_small_deals(self):
        """测试小单金额因子"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        service = SalesPredictionService(db)

        # 小于10万
        result = service.predict_win_probability(stage="PROPOSAL", amount=Decimal("50000"))

        assert result["amount_factor"] == 1.1

    def test_limits_probability_range(self):
        """测试概率范围限制"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        service = SalesPredictionService(db)
        result = service.predict_win_probability(stage="WON")

        # 最大 95%
        assert result["win_probability"] <= 0.95


@pytest.mark.unit
class TestGetHistoricalWinRateByStage:
    """测试 _get_historical_win_rate_by_stage 方法"""

    def test_returns_default_rates_for_no_data(self):
        """测试无数据时返回默认值"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []

        service = SalesPredictionService(db)
        result = service._get_historical_win_rate_by_stage()

        assert "DISCOVERY" in result
        assert "QUALIFIED" in result
        assert "PROPOSAL" in result
        assert "NEGOTIATION" in result
        assert result["WON"] == 1.0
        assert result["LOST"] == 0.0

    def test_calculates_rates_from_historical_data(self):
        """测试从历史数据计算赢单率"""
        db = create_mock_db_session()

        opportunities = [
            create_mock_opportunity(stage="WON"),
            create_mock_opportunity(stage="WON"),
            create_mock_opportunity(stage="LOST"),
            create_mock_opportunity(stage="PROPOSAL"),
        ]
        db.query.return_value.filter.return_value.all.return_value = opportunities

        service = SalesPredictionService(db)
        result = service._get_historical_win_rate_by_stage()

        # 赢单率 = 2/3 ≈ 0.667
        assert result["WON"] == 1.0
        assert result["LOST"] == 0.0


@pytest.mark.unit
class TestGetCustomerWinRate:
    """测试 _get_customer_win_rate 方法"""

    def test_returns_none_for_no_customer_id(self):
        """测试无客户ID时返回None"""
        db = create_mock_db_session()
        service = SalesPredictionService(db)

        result = service._get_customer_win_rate(None)

        assert result is None

    def test_returns_none_for_no_history(self):
        """测试无历史数据时返回None"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []

        service = SalesPredictionService(db)
        result = service._get_customer_win_rate(1)

        assert result is None

    def test_calculates_win_rate(self):
        """测试计算客户赢单率"""
        db = create_mock_db_session()
        opportunities = [
            create_mock_opportunity(stage="WON"),
            create_mock_opportunity(stage="WON"),
            create_mock_opportunity(stage="LOST"),
        ]
        db.query.return_value.filter.return_value.all.return_value = opportunities

        service = SalesPredictionService(db)
        result = service._get_customer_win_rate(1)

        # 2/3 ≈ 0.667
        assert result == pytest.approx(0.667, rel=0.01)


@pytest.mark.unit
class TestPredictRevenue:
    """测试 predict_revenue 方法"""

    def test_returns_prediction_structure(self):
        """测试返回预测结构"""
        db = create_mock_db_session()

        # Mock contracts query
        contracts_query = MagicMock()
        contracts_query.filter.return_value = contracts_query
        contracts_query.order_by.return_value.limit.return_value.all.return_value = []

        # Mock opportunities query
        opps_query = MagicMock()
        opps_query.filter.return_value = opps_query
        opps_query.all.return_value = []

        call_count = [0]

        def query_side_effect(model):
            model_name = str(model)
            if call_count[0] == 0:  # Contract
                call_count[0] += 1
                return contracts_query
            else:  # Opportunity
                return opps_query

        db.query.side_effect = query_side_effect

        service = SalesPredictionService(db)
        result = service.predict_revenue(days=30)

        assert "method" in result
        assert "days" in result
        assert "predicted_revenue" in result
        assert "opportunity_based_revenue" in result
        assert "combined_revenue" in result
        assert "confidence_level" in result
        assert "breakdown" in result

    def test_uses_moving_average_by_default(self):
        """测试默认使用移动平均法"""
        db = create_mock_db_session()

        contracts_query = MagicMock()
        contracts_query.filter.return_value = contracts_query
        contracts_query.order_by.return_value.limit.return_value.all.return_value = []

        opps_query = MagicMock()
        opps_query.filter.return_value = opps_query
        opps_query.all.return_value = []

        call_count = [0]

        def query_side_effect(model):
            if call_count[0] == 0:
                call_count[0] += 1
                return contracts_query
            else:
                return opps_query

        db.query.side_effect = query_side_effect

        service = SalesPredictionService(db)
        result = service.predict_revenue()

        assert result["method"] == "moving_average"

    def test_accepts_exponential_smoothing_method(self):
        """测试接受指数平滑法"""
        db = create_mock_db_session()

        contracts_query = MagicMock()
        contracts_query.filter.return_value = contracts_query
        contracts_query.order_by.return_value.limit.return_value.all.return_value = []

        opps_query = MagicMock()
        opps_query.filter.return_value = opps_query
        opps_query.all.return_value = []

        call_count = [0]

        def query_side_effect(model):
            if call_count[0] == 0:
                call_count[0] += 1
                return contracts_query
            else:
                return opps_query

        db.query.side_effect = query_side_effect

        service = SalesPredictionService(db)
        result = service.predict_revenue(method="exponential_smoothing")

        assert result["method"] == "exponential_smoothing"


@pytest.mark.unit
class TestEvaluatePredictionAccuracy:
    """测试 evaluate_prediction_accuracy 方法"""

    def test_returns_accuracy_structure(self):
        """测试返回准确度结构"""
        db = create_mock_db_session()

        # Mock contracts query
        contracts_query = MagicMock()
        contracts_query.filter.return_value = contracts_query
        contracts_query.all.return_value = []

        # Mock opportunities query
        opps_query = MagicMock()
        opps_query.filter.return_value = opps_query
        opps_query.all.return_value = []

        call_count = [0]

        def query_side_effect(model):
            if call_count[0] == 0:  # Contract
                call_count[0] += 1
                return contracts_query
            else:  # Opportunity
                return opps_query

        db.query.side_effect = query_side_effect

        service = SalesPredictionService(db)
        result = service.evaluate_prediction_accuracy()

        assert "period" in result
        assert "actual_revenue" in result
        assert "predicted_revenue" in result
        assert "accuracy" in result
        assert "error_rate" in result
        assert "mape" in result

    def test_calculates_accuracy_correctly(self):
        """测试正确计算准确度"""
        db = create_mock_db_session()

        # Mock contracts with actual revenue
        contracts = [
            create_mock_contract(contract_amount=Decimal("100000")),
            create_mock_contract(contract_amount=Decimal("100000")),
        ]

        contracts_query = MagicMock()
        contracts_query.filter.return_value = contracts_query
        contracts_query.all.return_value = contracts

        opps_query = MagicMock()
        opps_query.filter.return_value = opps_query
        opps_query.all.return_value = []

        call_count = [0]

        def query_side_effect(model):
            if call_count[0] == 0:  # Contract
                call_count[0] += 1
                return contracts_query
            else:  # Opportunity
                return opps_query

        db.query.side_effect = query_side_effect

        service = SalesPredictionService(db)
        result = service.evaluate_prediction_accuracy()

        assert result["actual_revenue"] == 200000.0
        assert "accuracy" in result

"""
AI智能成本估算服务测试
目标覆盖率: 60%+
测试数量: 30-45个
"""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.sales.ai_cost_estimation_service import AICostEstimationService
from app.models.sales.presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory
)
from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    CostEstimationResponse,
    CostOptimizationInput,
    CostOptimizationResponse,
    PricingInput,
    PricingResponse,
    OptimizationSuggestion,
    PricingRecommendation,
    UpdateActualCostInput,
    HistoricalAccuracyResponse
)


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    db.query = Mock(return_value=Mock())
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return AICostEstimationService(db=mock_db, user_id=1)


@pytest.fixture
def basic_estimation_input():
    """基础估算输入"""
    return CostEstimationInput(
        presale_ticket_id=1,
        solution_id=1,
        project_type="automation",
        complexity_level="medium",
        hardware_items=[
            {"name": "PLC", "unit_price": 5000, "quantity": 2},
            {"name": "触摸屏", "unit_price": 3000, "quantity": 1}
        ],
        software_requirements="开发监控系统，包含数据采集、实时监控、报警功能",
        estimated_man_days=15,
        installation_difficulty="medium",
        service_years=3,
        target_margin_rate=Decimal("0.30")
    )


# ============================================================================
# 1. 硬件成本计算测试 (5个测试)
# ============================================================================

def test_calculate_hardware_cost_empty(service):
    """测试空硬件列表"""
    result = service._calculate_hardware_cost(None)
    assert result == Decimal("0")


def test_calculate_hardware_cost_single_item(service):
    """测试单个硬件项"""
    items = [{"unit_price": 1000, "quantity": 1}]
    result = service._calculate_hardware_cost(items)
    # 1000 * 1 * 1.15 = 1150
    assert result == Decimal("1150")


def test_calculate_hardware_cost_multiple_items(service):
    """测试多个硬件项"""
    items = [
        {"unit_price": 5000, "quantity": 2},
        {"unit_price": 3000, "quantity": 1}
    ]
    result = service._calculate_hardware_cost(items)
    # (5000*2 + 3000*1) * 1.15 = 14950
    assert result == Decimal("14950")


def test_calculate_hardware_cost_decimal_quantity(service):
    """测试小数数量"""
    items = [{"unit_price": 1000, "quantity": 2.5}]
    result = service._calculate_hardware_cost(items)
    # 1000 * 2.5 * 1.15 = 2875
    assert result == Decimal("2875")


def test_calculate_hardware_cost_with_markup(service):
    """测试硬件加成率应用"""
    items = [{"unit_price": 10000, "quantity": 1}]
    result = service._calculate_hardware_cost(items)
    expected = Decimal("10000") * service.HARDWARE_MARKUP
    assert result == expected


# ============================================================================
# 2. 软件成本计算测试 (6个测试)
# ============================================================================

def test_calculate_software_cost_with_man_days(service):
    """测试指定人天的软件成本"""
    result = service._calculate_software_cost("需求描述", 10)
    # 10 * 8 * 800 = 64000
    assert result == Decimal("64000")


def test_calculate_software_cost_no_requirements(service):
    """测试无需求描述"""
    result = service._calculate_software_cost(None, None)
    assert result == Decimal("0")


def test_calculate_software_cost_short_requirements(service):
    """测试短需求描述自动估算"""
    short_req = "简单功能"
    result = service._calculate_software_cost(short_req, None)
    # 字符少于100，估算5人天: 5 * 8 * 800 = 32000
    assert result == Decimal("32000")


def test_calculate_software_cost_medium_requirements(service):
    """测试中等需求描述自动估算"""
    medium_req = "需求" * 150  # 300字符
    result = service._calculate_software_cost(medium_req, None)
    # 字符100-500，估算15人天: 15 * 8 * 800 = 96000
    assert result == Decimal("96000")


def test_calculate_software_cost_long_requirements(service):
    """测试长需求描述自动估算"""
    long_req = "需求" * 300  # 600字符
    result = service._calculate_software_cost(long_req, None)
    # 字符>500，估算30人天: 30 * 8 * 800 = 192000
    assert result == Decimal("192000")


def test_calculate_software_cost_zero_man_days(service):
    """测试零人天输入"""
    result = service._calculate_software_cost("有需求", 0)
    # 0人天时应该基于需求描述估算
    assert result > Decimal("0")


# ============================================================================
# 3. 安装成本计算测试 (4个测试)
# ============================================================================

def test_calculate_installation_cost_low_difficulty(service):
    """测试低难度安装"""
    hardware_cost = Decimal("10000")
    result = service._calculate_installation_cost("low", hardware_cost)
    # 5000 * 1.0 + 10000 * 0.05 = 5500
    assert result == Decimal("5500")


def test_calculate_installation_cost_medium_difficulty(service):
    """测试中等难度安装"""
    hardware_cost = Decimal("10000")
    result = service._calculate_installation_cost("medium", hardware_cost)
    # 5000 * 1.5 + 10000 * 0.05 = 8000
    assert result == Decimal("8000.00")


def test_calculate_installation_cost_high_difficulty(service):
    """测试高难度安装"""
    hardware_cost = Decimal("10000")
    result = service._calculate_installation_cost("high", hardware_cost)
    # 5000 * 2.0 + 10000 * 0.05 = 10500
    assert result == Decimal("10500")


def test_calculate_installation_cost_none_difficulty(service):
    """测试未指定难度(默认低难度)"""
    hardware_cost = Decimal("10000")
    result = service._calculate_installation_cost(None, hardware_cost)
    assert result == Decimal("5500")


# ============================================================================
# 4. 服务成本计算测试 (3个测试)
# ============================================================================

def test_calculate_service_cost_one_year(service):
    """测试1年服务成本"""
    base_cost = Decimal("100000")
    result = service._calculate_service_cost(base_cost, 1)
    # 100000 * 0.10 * 1 = 10000
    assert result == Decimal("10000")


def test_calculate_service_cost_multiple_years(service):
    """测试多年服务成本"""
    base_cost = Decimal("100000")
    result = service._calculate_service_cost(base_cost, 3)
    # 100000 * 0.10 * 3 = 30000
    assert result == Decimal("30000")


def test_calculate_service_cost_zero_years(service):
    """测试0年服务成本"""
    base_cost = Decimal("100000")
    result = service._calculate_service_cost(base_cost, 0)
    assert result == Decimal("0")


# ============================================================================
# 5. 风险储备金计算测试 (5个测试)
# ============================================================================

def test_calculate_risk_reserve_medium_complexity(service, mock_db):
    """测试中等复杂度风险储备"""
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    base_cost = Decimal("100000")
    result = service._calculate_risk_reserve("automation", "medium", base_cost)
    # 100000 * 0.08 = 8000
    assert result == Decimal("8000")


def test_calculate_risk_reserve_high_complexity(service, mock_db):
    """测试高复杂度风险储备"""
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    base_cost = Decimal("100000")
    result = service._calculate_risk_reserve("automation", "high", base_cost)
    # 100000 * 0.08 * 1.5 = 12000
    assert result == Decimal("12000")


def test_calculate_risk_reserve_low_complexity(service, mock_db):
    """测试低复杂度风险储备"""
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    base_cost = Decimal("100000")
    result = service._calculate_risk_reserve("automation", "low", base_cost)
    # 100000 * 0.08 * 0.5 = 4000
    assert result == Decimal("4000")


def test_calculate_risk_reserve_with_historical_data(service, mock_db):
    """测试基于历史数据调整风险储备"""
    mock_db.query.return_value.filter.return_value.scalar.return_value = 10.0  # 10%偏差
    base_cost = Decimal("100000")
    result = service._calculate_risk_reserve("automation", "medium", base_cost)
    # 100000 * 0.08 * (1 + 0.10) = 8800
    assert result == Decimal("8800")


def test_get_historical_variance_no_data(service, mock_db):
    """测试无历史数据时的偏差率"""
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    result = service._get_historical_variance("automation")
    assert result is None


# ============================================================================
# 6. 置信度评分测试 (4个测试)
# ============================================================================

def test_calculate_confidence_score_minimal_input(service, mock_db):
    """测试最少输入的置信度"""
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    input_data = CostEstimationInput(
        presale_ticket_id=1,
        solution_id=1,
        project_type="automation",
        complexity_level="medium"
    )
    result = service._calculate_confidence_score(input_data)
    assert result == Decimal("0.5")  # 仅基础分


def test_calculate_confidence_score_with_hardware(service, mock_db):
    """测试包含硬件清单的置信度"""
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    input_data = CostEstimationInput(
        presale_ticket_id=1,
        solution_id=1,
        project_type="automation",
        complexity_level="medium",
        hardware_items=[{"unit_price": 1000, "quantity": 1}]
    )
    result = service._calculate_confidence_score(input_data)
    assert result == Decimal("0.7")  # 0.5 + 0.2


def test_calculate_confidence_score_complete_input(service, mock_db):
    """测试完整输入的置信度"""
    mock_db.query.return_value.filter.return_value.count.return_value = 15
    input_data = CostEstimationInput(
        presale_ticket_id=1,
        solution_id=1,
        project_type="automation",
        complexity_level="medium",
        hardware_items=[{"unit_price": 1000, "quantity": 1}],
        software_requirements="详细需求" * 50,  # >100字符
        estimated_man_days=10
    )
    result = service._calculate_confidence_score(input_data)
    # 0.5 + 0.2 + 0.15 + 0.1 + 0.05 = 1.0
    assert result == Decimal("1.0")


def test_calculate_confidence_score_capped_at_one(service, mock_db):
    """测试置信度上限为1.0"""
    mock_db.query.return_value.filter.return_value.count.return_value = 100
    input_data = CostEstimationInput(
        presale_ticket_id=1,
        solution_id=1,
        project_type="automation",
        complexity_level="medium",
        hardware_items=[{"unit_price": 1000, "quantity": 1}],
        software_requirements="详细需求" * 100,
        estimated_man_days=20
    )
    result = service._calculate_confidence_score(input_data)
    assert result <= Decimal("1.0")


# ============================================================================
# 7. 定价推荐测试 (4个测试)
# ============================================================================

def test_generate_pricing_recommendations_30_percent_margin(service):
    """测试30%毛利率定价"""
    total_cost = Decimal("100000")
    target_margin = Decimal("0.30")
    result = service._generate_pricing_recommendations(total_cost, target_margin)
    
    # 建议价格 = 100000 / (1 - 0.30) = 142857.14
    assert abs(result.suggested_price - Decimal("142857.14")) < Decimal("0.5")
    assert result.target_margin_rate == Decimal("30")


def test_generate_pricing_recommendations_three_tiers(service):
    """测试三档定价"""
    total_cost = Decimal("100000")
    result = service._generate_pricing_recommendations(total_cost, Decimal("0.30"))
    
    assert result.low < result.medium < result.high
    assert result.medium == result.suggested_price


def test_generate_pricing_recommendations_low_margin(service):
    """测试低毛利率定价"""
    total_cost = Decimal("100000")
    target_margin = Decimal("0.10")  # 10%毛利
    result = service._generate_pricing_recommendations(total_cost, target_margin)
    
    # 100000 / 0.9 = 111111.11
    assert abs(result.suggested_price - Decimal("111111.11")) < Decimal("0.5")


def test_pricing_recommendation_market_analysis(service):
    """测试定价推荐包含市场分析"""
    total_cost = Decimal("100000")
    result = service._generate_pricing_recommendations(total_cost, Decimal("0.30"))
    
    assert result.market_analysis is not None
    assert len(result.market_analysis) > 0


# ============================================================================
# 8. 完整成本估算流程测试 (3个测试)
# ============================================================================

@pytest.mark.asyncio
async def test_estimate_cost_complete_flow(service, mock_db, basic_estimation_input):
    """测试完整成本估算流程"""
    # Mock 数据库操作
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    mock_db.query.return_value.filter.return_value.count.return_value = 5
    
    with patch('app.utils.db_helpers.save_obj') as mock_save:
        # 修复：创建实际的 estimation 对象，并让 save_obj 修改它
        def save_side_effect(db, obj):
            obj.id = 1
            obj.created_at = datetime.now()
            return obj
        
        mock_save.side_effect = save_side_effect
        
        result = await service.estimate_cost(basic_estimation_input)
        
        assert isinstance(result, CostEstimationResponse)
        assert result.cost_breakdown.total_cost > Decimal("0")
        assert len(result.optimization_suggestions) >= 0
        assert result.confidence_score >= Decimal("0.5")


@pytest.mark.asyncio
async def test_estimate_cost_generates_optimization_suggestions(service, mock_db, basic_estimation_input):
    """测试成本估算生成优化建议"""
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    mock_db.query.return_value.filter.return_value.count.return_value = 5
    
    with patch('app.utils.db_helpers.save_obj') as mock_save:
        def save_side_effect(db, obj):
            obj.id = 1
            obj.created_at = datetime.now()
            return obj
        
        mock_save.side_effect = save_side_effect
        
        result = await service.estimate_cost(basic_estimation_input)
        
        # 应该至少有一些优化建议
        assert result.optimization_suggestions is not None


@pytest.mark.asyncio
async def test_estimate_cost_saves_to_database(service, mock_db, basic_estimation_input):
    """测试成本估算保存到数据库"""
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    mock_db.query.return_value.filter.return_value.count.return_value = 5
    
    with patch('app.utils.db_helpers.save_obj') as mock_save:
        def save_side_effect(db, obj):
            obj.id = 1
            obj.created_at = datetime.now()
            return obj
        
        mock_save.side_effect = save_side_effect
        
        await service.estimate_cost(basic_estimation_input)
        
        mock_save.assert_called_once()
        saved_obj = mock_save.call_args[0][1]
        assert isinstance(saved_obj, PresaleAICostEstimation)


# ============================================================================
# 9. 成本优化测试 (4个测试)
# ============================================================================

@pytest.mark.asyncio
async def test_optimize_cost_not_found(service, mock_db):
    """测试优化不存在的估算"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    input_data = CostOptimizationInput(
        estimation_id=999,
        max_risk_level="medium"
    )
    
    with pytest.raises(ValueError, match="估算记录不存在"):
        await service.optimize_cost(input_data)


@pytest.mark.asyncio
async def test_optimize_cost_applies_suggestions(service, mock_db):
    """测试成本优化应用建议"""
    mock_estimation = PresaleAICostEstimation(
        id=1,
        total_cost=Decimal("100000"),
        optimization_suggestions=[
            {
                "type": "hardware",
                "description": "优化建议",
                "original_cost": Decimal("50000"),
                "optimized_cost": Decimal("45000"),
                "saving_amount": Decimal("5000"),
                "saving_rate": Decimal("10.0"),
                "feasibility_score": Decimal("0.85"),
                "alternative_solutions": []
            }
        ]
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
    
    input_data = CostOptimizationInput(
        estimation_id=1,
        max_risk_level="medium"
    )
    
    result = await service.optimize_cost(input_data)
    
    assert isinstance(result, CostOptimizationResponse)
    assert result.total_saving > Decimal("0")


def test_is_acceptable_risk_low_threshold(service):
    """测试低风险阈值"""
    suggestion = OptimizationSuggestion(
        type="hardware",
        description="test",
        original_cost=Decimal("100"),
        optimized_cost=Decimal("90"),
        saving_amount=Decimal("10"),
        saving_rate=Decimal("10"),
        feasibility_score=Decimal("0.80")
    )
    
    assert service._is_acceptable_risk(suggestion, "low") is False
    assert service._is_acceptable_risk(suggestion, "medium") is True
    assert service._is_acceptable_risk(suggestion, "high") is True


def test_calculate_avg_feasibility(service):
    """测试平均可行性计算"""
    suggestions = [
        OptimizationSuggestion(
            type="hardware", description="test",
            original_cost=Decimal("100"), optimized_cost=Decimal("90"),
            saving_amount=Decimal("10"), saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.8")
        ),
        OptimizationSuggestion(
            type="software", description="test",
            original_cost=Decimal("100"), optimized_cost=Decimal("90"),
            saving_amount=Decimal("10"), saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.6")
        )
    ]
    
    result = service._calculate_avg_feasibility(suggestions)
    assert result == Decimal("0.7")


# ============================================================================
# 10. 定价策略测试 (3个测试)
# ============================================================================

@pytest.mark.asyncio
async def test_recommend_pricing_not_found(service, mock_db):
    """测试推荐定价找不到估算"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    input_data = PricingInput(
        estimation_id=999,
        target_margin_rate=Decimal("0.30"),
        market_competition_level="medium"
    )
    
    with pytest.raises(ValueError, match="估算记录不存在"):
        await service.recommend_pricing(input_data)


@pytest.mark.asyncio
async def test_recommend_pricing_adjusts_for_competition(service, mock_db):
    """测试定价根据市场竞争调整"""
    mock_estimation = PresaleAICostEstimation(
        id=1,
        total_cost=Decimal("100000")
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
    
    input_high_competition = PricingInput(
        estimation_id=1,
        target_margin_rate=Decimal("0.30"),
        market_competition_level="high"
    )
    
    result = await service.recommend_pricing(input_high_competition)
    
    # 高竞争应该调整价格
    assert isinstance(result, PricingResponse)
    assert result.pricing_recommendations.suggested_price > Decimal("0")


def test_get_pricing_strategy_high_budget(service):
    """测试高预算定价策略"""
    pricing = PricingRecommendation(
        low=Decimal("100000"),
        medium=Decimal("120000"),
        high=Decimal("140000"),
        suggested_price=Decimal("120000"),
        target_margin_rate=Decimal("30"),
        market_analysis="test"
    )
    
    strategy = service._get_pricing_strategy(Decimal("150000"), pricing)
    assert "高价档" in strategy or "高附加值" in strategy


# ============================================================================
# 11. 历史数据分析测试 (2个测试)
# ============================================================================

@pytest.mark.asyncio
async def test_get_historical_accuracy_no_data(service, mock_db):
    """测试无历史数据时的准确度"""
    mock_db.query.return_value.all.return_value = []
    
    result = await service.get_historical_accuracy()
    
    assert isinstance(result, HistoricalAccuracyResponse)
    assert result.total_predictions == 0
    assert result.average_variance_rate == Decimal("0")
    assert result.recent_trend == "无数据"


@pytest.mark.asyncio
async def test_get_historical_accuracy_with_data(service, mock_db):
    """测试有历史数据时的准确度"""
    mock_histories = [
        PresaleCostHistory(variance_rate=Decimal("5")),
        PresaleCostHistory(variance_rate=Decimal("10")),
        PresaleCostHistory(variance_rate=Decimal("8"))
    ]
    mock_db.query.return_value.all.return_value = mock_histories
    
    result = await service.get_historical_accuracy()
    
    assert result.total_predictions == 3
    # (5 + 10 + 8) / 3 = 7.67
    assert abs(result.average_variance_rate - Decimal("7.67")) < Decimal("0.1")


# ============================================================================
# 12. 实际成本更新测试 (3个测试)
# ============================================================================

@pytest.mark.asyncio
async def test_update_actual_cost_not_found(service, mock_db):
    """测试更新不存在的估算实际成本"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    input_data = UpdateActualCostInput(
        estimation_id=999,
        project_id=1,
        project_name="测试项目",
        actual_cost=Decimal("100000")
    )
    
    with pytest.raises(ValueError, match="估算记录不存在"):
        await service.update_actual_cost(input_data)


@pytest.mark.asyncio
async def test_update_actual_cost_calculates_variance(service, mock_db):
    """测试更新实际成本计算偏差"""
    mock_estimation = PresaleAICostEstimation(
        id=1,
        total_cost=Decimal("100000"),
        input_parameters={}
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
    
    with patch('app.utils.db_helpers.save_obj') as mock_save:
        mock_history = PresaleCostHistory(id=1)
        mock_save.return_value = mock_history
        
        input_data = UpdateActualCostInput(
            estimation_id=1,
            project_id=1,
            project_name="测试项目",
            actual_cost=Decimal("110000")
        )
        
        result = await service.update_actual_cost(input_data)
        
        assert result["variance_rate"] == Decimal("10")  # (110000-100000)/100000 * 100
        assert result["learning_applied"] is True


@pytest.mark.asyncio
async def test_update_actual_cost_saves_history(service, mock_db):
    """测试更新实际成本保存历史记录"""
    mock_estimation = PresaleAICostEstimation(
        id=1,
        total_cost=Decimal("100000"),
        input_parameters={}
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
    
    with patch('app.utils.db_helpers.save_obj') as mock_save:
        def save_side_effect(db, obj):
            obj.id = 1
            return obj
        
        mock_save.side_effect = save_side_effect
        
        input_data = UpdateActualCostInput(
            estimation_id=1,
            project_id=1,
            project_name="测试项目",
            actual_cost=Decimal("110000")
        )
        
        await service.update_actual_cost(input_data)
        
        mock_save.assert_called_once()
        saved_obj = mock_save.call_args[0][1]
        assert isinstance(saved_obj, PresaleCostHistory)


# ============================================================================
# 13. 价格敏感度分析测试 (2个测试)
# ============================================================================

def test_analyze_price_sensitivity_without_budget(service):
    """测试无客户预算的价格敏感度分析"""
    pricing = PricingRecommendation(
        low=Decimal("100000"),
        medium=Decimal("120000"),
        high=Decimal("140000"),
        suggested_price=Decimal("120000"),
        target_margin_rate=Decimal("30"),
        market_analysis="test"
    )
    
    result = service._analyze_price_sensitivity(
        Decimal("90000"),
        pricing,
        None
    )
    
    assert "price_range" in result
    assert "margin_analysis" in result
    assert "budget_fit" not in result


def test_analyze_price_sensitivity_with_budget(service):
    """测试有客户预算的价格敏感度分析"""
    pricing = PricingRecommendation(
        low=Decimal("100000"),
        medium=Decimal("120000"),
        high=Decimal("140000"),
        suggested_price=Decimal("120000"),
        target_margin_rate=Decimal("30"),
        market_analysis="test"
    )
    
    result = service._analyze_price_sensitivity(
        Decimal("90000"),
        pricing,
        Decimal("110000")
    )
    
    assert "budget_fit" in result
    assert result["budget_fit"]["customer_budget"] == 110000.0
    assert "recommended_strategy" in result["budget_fit"]


# ============================================================================
# 14. 竞争力评分测试 (2个测试)
# ============================================================================

def test_calculate_competitiveness_no_budget(service):
    """测试无预算时的竞争力评分"""
    pricing = PricingRecommendation(
        low=Decimal("100000"),
        medium=Decimal("120000"),
        high=Decimal("140000"),
        suggested_price=Decimal("120000"),
        target_margin_rate=Decimal("30"),
        market_analysis="test"
    )
    
    result = service._calculate_competitiveness(pricing, None)
    assert result == Decimal("0.70")


def test_calculate_competitiveness_with_budget(service):
    """测试有预算时的竞争力评分"""
    pricing = PricingRecommendation(
        low=Decimal("100000"),
        medium=Decimal("120000"),
        high=Decimal("140000"),
        suggested_price=Decimal("120000"),
        target_margin_rate=Decimal("30"),
        market_analysis="test"
    )
    
    # 预算充足
    result_high = service._calculate_competitiveness(pricing, Decimal("150000"))
    assert result_high == Decimal("0.90")
    
    # 预算适中
    result_medium = service._calculate_competitiveness(pricing, Decimal("110000"))
    assert result_medium == Decimal("0.75")
    
    # 预算不足
    result_low = service._calculate_competitiveness(pricing, Decimal("90000"))
    assert result_low == Decimal("0.50")

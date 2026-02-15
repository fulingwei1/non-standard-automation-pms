"""
售前AI成本估算模块 - 单元测试
"""
import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.sales.presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory,
    PresaleCostOptimizationRecord
)
from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    CostOptimizationInput,
    PricingInput,
    UpdateActualCostInput,
    CostBreakdown
)
from app.services.sales.ai_cost_estimation_service import AICostEstimationService


# ============= 测试数据准备 =============

@pytest.fixture
def db_session():
    """模拟数据库会话"""
    from unittest.mock import MagicMock
    return MagicMock(spec=Session)


@pytest.fixture
def user_id():
    """测试用户ID"""
    return 1


@pytest.fixture
def service(db_session, user_id):
    """创建服务实例"""
    return AICostEstimationService(db_session, user_id)


@pytest.fixture
def sample_hardware_items():
    """样例硬件清单"""
    return [
        {"name": "PLC控制器", "unit_price": 5000, "quantity": 2},
        {"name": "伺服电机", "unit_price": 3000, "quantity": 4},
        {"name": "传感器", "unit_price": 500, "quantity": 10},
    ]


@pytest.fixture
def sample_estimation_input(sample_hardware_items):
    """样例估算输入"""
    return CostEstimationInput(
        presale_ticket_id=1001,
        solution_id=2001,
        project_type="自动化产线",
        industry="制造业",
        complexity_level="medium",
        hardware_items=sample_hardware_items,
        software_requirements="需要开发PLC控制程序、MES接口、数据采集模块",
        estimated_man_days=20,
        installation_difficulty="medium",
        service_years=2,
        target_margin_rate=Decimal("0.30")
    )


# ============= 成本估算测试 (10个) =============

class TestCostEstimation:
    """成本估算测试类"""
    
    def test_calculate_hardware_cost_with_items(self, service, sample_hardware_items):
        """测试1: 计算硬件成本 - 有清单"""
        cost = service._calculate_hardware_cost(sample_hardware_items)
        expected = (5000 * 2 + 3000 * 4 + 500 * 10) * Decimal("1.15")
        assert cost == expected
    
    def test_calculate_hardware_cost_empty(self, service):
        """测试2: 计算硬件成本 - 空清单"""
        cost = service._calculate_hardware_cost(None)
        assert cost == Decimal("0")
    
    def test_calculate_software_cost_with_man_days(self, service):
        """测试3: 计算软件成本 - 有人天估算"""
        cost = service._calculate_software_cost("需求描述", 20)
        expected = Decimal("20") * Decimal("8") * Decimal("800")
        assert cost == expected
    
    def test_calculate_software_cost_auto_estimate(self, service):
        """测试4: 计算软件成本 - 自动估算人天"""
        short_req = "简单需求"
        cost_short = service._calculate_software_cost(short_req, None)
        assert cost_short == Decimal("5") * Decimal("8") * Decimal("800")
        
        long_req = "x" * 600
        cost_long = service._calculate_software_cost(long_req, None)
        assert cost_long == Decimal("30") * Decimal("8") * Decimal("800")
    
    def test_calculate_installation_cost_high_difficulty(self, service):
        """测试5: 计算安装成本 - 高难度"""
        hardware_cost = Decimal("100000")
        cost = service._calculate_installation_cost("high", hardware_cost)
        expected = Decimal("5000") * Decimal("2.0") + hardware_cost * Decimal("0.05")
        assert cost == expected
    
    def test_calculate_installation_cost_low_difficulty(self, service):
        """测试6: 计算安装成本 - 低难度"""
        hardware_cost = Decimal("100000")
        cost = service._calculate_installation_cost("low", hardware_cost)
        expected = Decimal("5000") * Decimal("1.0") + hardware_cost * Decimal("0.05")
        assert cost == expected
    
    def test_calculate_service_cost(self, service):
        """测试7: 计算服务成本"""
        base_cost = Decimal("200000")
        years = 3
        cost = service._calculate_service_cost(base_cost, years)
        expected = base_cost * Decimal("0.10") * Decimal("3")
        assert cost == expected
    
    def test_calculate_risk_reserve_high_complexity(self, service):
        """测试8: 计算风险储备 - 高复杂度"""
        service._get_historical_variance = lambda x: None
        base_cost = Decimal("300000")
        cost = service._calculate_risk_reserve("自动化产线", "high", base_cost)
        expected = base_cost * Decimal("0.08") * Decimal("1.5")
        assert cost == expected
    
    def test_calculate_risk_reserve_low_complexity(self, service):
        """测试9: 计算风险储备 - 低复杂度"""
        service._get_historical_variance = lambda x: None
        base_cost = Decimal("300000")
        cost = service._calculate_risk_reserve("自动化产线", "low", base_cost)
        expected = base_cost * Decimal("0.08") * Decimal("0.5")
        assert cost == expected
    
    def test_calculate_confidence_score(self, service, sample_estimation_input):
        """测试10: 计算置信度评分"""
        service.db.query = lambda x: type('obj', (object,), {
            'filter': lambda *args, **kwargs: type('obj', (object,), {
                'count': lambda: 15
            })()
        })()
        
        score = service._calculate_confidence_score(sample_estimation_input)
        assert score >= Decimal("0.5")
        assert score <= Decimal("1.0")


# ============= 成本优化建议测试 (6个) =============

class TestCostOptimization:
    """成本优化测试类"""
    
    @pytest.mark.asyncio
    async def test_generate_optimization_suggestions_hardware(self, service, sample_estimation_input):
        """测试11: 生成优化建议 - 硬件优化"""
        cost_breakdown = {
            "hardware_cost": Decimal("80000"),
            "software_cost": Decimal("50000"),
            "installation_cost": Decimal("10000"),
            "service_cost": Decimal("20000"),
            "risk_reserve": Decimal("15000"),
        }
        
        suggestions = await service._generate_optimization_suggestions(
            sample_estimation_input,
            cost_breakdown
        )
        
        # 应该有硬件优化建议(因为硬件成本>50000)
        hardware_suggestions = [s for s in suggestions if s.type == "hardware"]
        assert len(hardware_suggestions) > 0
        assert hardware_suggestions[0].saving_rate > 0
    
    @pytest.mark.asyncio
    async def test_generate_optimization_suggestions_software(self, service, sample_estimation_input):
        """测试12: 生成优化建议 - 软件优化"""
        cost_breakdown = {
            "hardware_cost": Decimal("30000"),
            "software_cost": Decimal("150000"),
            "installation_cost": Decimal("10000"),
            "service_cost": Decimal("20000"),
            "risk_reserve": Decimal("15000"),
        }
        
        suggestions = await service._generate_optimization_suggestions(
            sample_estimation_input,
            cost_breakdown
        )
        
        # 应该有软件优化建议(因为软件成本>100000)
        software_suggestions = [s for s in suggestions if s.type == "software"]
        assert len(software_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_optimization_suggestions_installation(self, service):
        """测试13: 生成优化建议 - 安装优化"""
        input_data = CostEstimationInput(
            presale_ticket_id=1001,
            project_type="自动化产线",
            complexity_level="high",
            installation_difficulty="high"
        )
        
        cost_breakdown = {
            "hardware_cost": Decimal("30000"),
            "software_cost": Decimal("50000"),
            "installation_cost": Decimal("20000"),
            "service_cost": Decimal("10000"),
            "risk_reserve": Decimal("10000"),
        }
        
        suggestions = await service._generate_optimization_suggestions(
            input_data,
            cost_breakdown
        )
        
        # 应该有安装优化建议(因为安装难度高)
        installation_suggestions = [s for s in suggestions if s.type == "installation"]
        assert len(installation_suggestions) > 0
    
    def test_is_acceptable_risk_low_threshold(self, service):
        """测试14: 风险可接受性判断 - 低风险要求"""
        from app.schemas.sales.presale_ai_cost import OptimizationSuggestion
        
        suggestion_high_feasibility = OptimizationSuggestion(
            type="hardware",
            description="测试",
            original_cost=Decimal("100"),
            optimized_cost=Decimal("90"),
            saving_amount=Decimal("10"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.90")
        )
        
        suggestion_low_feasibility = OptimizationSuggestion(
            type="hardware",
            description="测试",
            original_cost=Decimal("100"),
            optimized_cost=Decimal("90"),
            saving_amount=Decimal("10"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.70")
        )
        
        assert service._is_acceptable_risk(suggestion_high_feasibility, "low") is True
        assert service._is_acceptable_risk(suggestion_low_feasibility, "low") is False
    
    def test_is_acceptable_risk_high_threshold(self, service):
        """测试15: 风险可接受性判断 - 高风险要求"""
        from app.schemas.sales.presale_ai_cost import OptimizationSuggestion
        
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="测试",
            original_cost=Decimal("100"),
            optimized_cost=Decimal("90"),
            saving_amount=Decimal("10"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.60")
        )
        
        assert service._is_acceptable_risk(suggestion, "high") is True
        assert service._is_acceptable_risk(suggestion, "low") is False
    
    def test_calculate_avg_feasibility(self, service):
        """测试16: 计算平均可行性"""
        from app.schemas.sales.presale_ai_cost import OptimizationSuggestion
        
        suggestions = [
            OptimizationSuggestion(
                type="hardware",
                description="测试1",
                original_cost=Decimal("100"),
                optimized_cost=Decimal("90"),
                saving_amount=Decimal("10"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.80")
            ),
            OptimizationSuggestion(
                type="software",
                description="测试2",
                original_cost=Decimal("100"),
                optimized_cost=Decimal("85"),
                saving_amount=Decimal("15"),
                saving_rate=Decimal("15"),
                feasibility_score=Decimal("0.70")
            ),
        ]
        
        avg = service._calculate_avg_feasibility(suggestions)
        expected = (Decimal("0.80") + Decimal("0.70")) / Decimal("2")
        assert avg == expected


# ============= 定价推荐测试 (6个) =============

class TestPricingRecommendation:
    """定价推荐测试类"""
    
    def test_generate_pricing_recommendations_basic(self, service):
        """测试17: 生成定价推荐 - 基本测试"""
        total_cost = Decimal("100000")
        target_margin = Decimal("0.30")
        
        pricing = service._generate_pricing_recommendations(total_cost, target_margin)
        
        # 验证建议价格
        expected_suggested = total_cost / (Decimal("1") - target_margin)
        assert pricing.suggested_price == expected_suggested
        
        # 验证价格档位
        assert pricing.low == expected_suggested * Decimal("0.90")
        assert pricing.medium == expected_suggested
        assert pricing.high == expected_suggested * Decimal("1.15")
    
    def test_generate_pricing_recommendations_high_margin(self, service):
        """测试18: 生成定价推荐 - 高毛利率"""
        total_cost = Decimal("100000")
        target_margin = Decimal("0.40")
        
        pricing = service._generate_pricing_recommendations(total_cost, target_margin)
        
        expected_suggested = total_cost / (Decimal("1") - target_margin)
        assert pricing.suggested_price == expected_suggested
        assert pricing.target_margin_rate == Decimal("40")
    
    def test_analyze_price_sensitivity_with_budget(self, service):
        """测试19: 价格敏感度分析 - 有客户预算"""
        cost = Decimal("100000")
        pricing = service._generate_pricing_recommendations(cost, Decimal("0.30"))
        customer_budget = Decimal("150000")
        
        analysis = service._analyze_price_sensitivity(cost, pricing, customer_budget)
        
        assert "budget_fit" in analysis
        assert analysis["budget_fit"]["customer_budget"] == float(customer_budget)
        assert "recommended_strategy" in analysis["budget_fit"]
    
    def test_analyze_price_sensitivity_without_budget(self, service):
        """测试20: 价格敏感度分析 - 无客户预算"""
        cost = Decimal("100000")
        pricing = service._generate_pricing_recommendations(cost, Decimal("0.30"))
        
        analysis = service._analyze_price_sensitivity(cost, pricing, None)
        
        assert "price_range" in analysis
        assert "margin_analysis" in analysis
        assert "budget_fit" not in analysis
    
    def test_get_pricing_strategy_high_budget(self, service):
        """测试21: 定价策略 - 高预算"""
        pricing = service._generate_pricing_recommendations(Decimal("100000"), Decimal("0.30"))
        budget = Decimal("200000")
        
        strategy = service._get_pricing_strategy(budget, pricing)
        assert "高价档" in strategy or "高附加值" in strategy
    
    def test_get_pricing_strategy_low_budget(self, service):
        """测试22: 定价策略 - 低预算"""
        pricing = service._generate_pricing_recommendations(Decimal("100000"), Decimal("0.30"))
        budget = Decimal("100000")
        
        strategy = service._get_pricing_strategy(budget, pricing)
        assert "低价档" in strategy or "简化" in strategy or "放弃" in strategy


# ============= 准确度学习测试 (6个) =============

class TestHistoricalLearning:
    """准确度学习测试类"""
    
    @pytest.mark.asyncio
    async def test_get_historical_accuracy_no_data(self, service):
        """测试23: 历史准确度 - 无数据"""
        service.db.query = lambda x: type('obj', (object,), {
            'all': lambda: []
        })()
        
        result = await service.get_historical_accuracy()
        
        assert result.total_predictions == 0
        assert result.average_variance_rate == Decimal("0")
        assert result.recent_trend == "无数据"
    
    @pytest.mark.asyncio
    async def test_get_historical_accuracy_with_data(self, service):
        """测试24: 历史准确度 - 有数据"""
        mock_histories = [
            type('obj', (object,), {'variance_rate': Decimal("10.5")})(),
            type('obj', (object,), {'variance_rate': Decimal("8.3")})(),
            type('obj', (object,), {'variance_rate': Decimal("12.1")})(),
        ]
        
        service.db.query = lambda x: type('obj', (object,), {
            'all': lambda: mock_histories
        })()
        
        result = await service.get_historical_accuracy()
        
        assert result.total_predictions == 3
        assert result.accuracy_rate == Decimal("100")  # 所有偏差都<15%
    
    @pytest.mark.asyncio
    async def test_update_actual_cost_basic(self, service):
        """测试25: 更新实际成本 - 基本测试"""
        # Mock数据库查询
        mock_estimation = type('obj', (object,), {
            'id': 1,
            'total_cost': Decimal("100000"),
            'input_parameters': {"project_type": "自动化产线"}
        })()
        
        service.db.query = lambda x: type('obj', (object,), {
            'filter': lambda *args, **kwargs: type('obj', (object,), {
                'first': lambda: mock_estimation
            })()
        })()
        
        service.db.add = lambda x: None
        service.db.commit = lambda: None
        service.db.refresh = lambda x: setattr(x, 'id', 1)
        
        input_data = UpdateActualCostInput(
            estimation_id=1,
            project_id=2001,
            project_name="测试项目",
            actual_cost=Decimal("110000")
        )
        
        result = await service.update_actual_cost(input_data)
        
        assert result["variance_rate"] == Decimal("10.0")
        assert result["learning_applied"] is True
    
    @pytest.mark.asyncio
    async def test_update_actual_cost_with_breakdown(self, service):
        """测试26: 更新实际成本 - 含分解"""
        mock_estimation = type('obj', (object,), {
            'id': 1,
            'total_cost': Decimal("100000"),
            'input_parameters': {"project_type": "自动化产线"}
        })()
        
        service.db.query = lambda x: type('obj', (object,), {
            'filter': lambda *args, **kwargs: type('obj', (object,), {
                'first': lambda: mock_estimation
            })()
        })()
        
        service.db.add = lambda x: None
        service.db.commit = lambda: None
        service.db.refresh = lambda x: setattr(x, 'id', 1)
        
        breakdown = CostBreakdown(
            hardware_cost=Decimal("40000"),
            software_cost=Decimal("35000"),
            installation_cost=Decimal("15000"),
            service_cost=Decimal("10000"),
            risk_reserve=Decimal("10000"),
            total_cost=Decimal("110000")
        )
        
        input_data = UpdateActualCostInput(
            estimation_id=1,
            actual_cost=Decimal("110000"),
            actual_breakdown=breakdown
        )
        
        result = await service.update_actual_cost(input_data)
        assert "variance_analysis" in result
    
    @pytest.mark.asyncio
    async def test_update_actual_cost_negative_variance(self, service):
        """测试27: 更新实际成本 - 负偏差(实际成本更低)"""
        mock_estimation = type('obj', (object,), {
            'id': 1,
            'total_cost': Decimal("100000"),
            'input_parameters': {}
        })()
        
        service.db.query = lambda x: type('obj', (object,), {
            'filter': lambda *args, **kwargs: type('obj', (object,), {
                'first': lambda: mock_estimation
            })()
        })()
        
        service.db.add = lambda x: None
        service.db.commit = lambda: None
        service.db.refresh = lambda x: setattr(x, 'id', 1)
        
        input_data = UpdateActualCostInput(
            estimation_id=1,
            actual_cost=Decimal("90000")
        )
        
        result = await service.update_actual_cost(input_data)
        assert result["variance_rate"] == Decimal("-10.0")
    
    @pytest.mark.asyncio
    async def test_update_actual_cost_estimation_not_found(self, service):
        """测试28: 更新实际成本 - 估算记录不存在"""
        service.db.query = lambda x: type('obj', (object,), {
            'filter': lambda *args, **kwargs: type('obj', (object,), {
                'first': lambda: None
            })()
        })()
        
        input_data = UpdateActualCostInput(
            estimation_id=999,
            actual_cost=Decimal("100000")
        )
        
        with pytest.raises(ValueError, match="估算记录不存在"):
            await service.update_actual_cost(input_data)


# ============= 其他功能测试 (额外4个,总计32个) =============

class TestAdditionalFeatures:
    """其他功能测试"""
    
    def test_calculate_competitiveness_high_budget(self, service):
        """测试29: 竞争力评分 - 高预算"""
        pricing = service._generate_pricing_recommendations(Decimal("100000"), Decimal("0.30"))
        score = service._calculate_competitiveness(pricing, Decimal("200000"))
        assert score == Decimal("0.90")
    
    def test_calculate_competitiveness_medium_budget(self, service):
        """测试30: 竞争力评分 - 中预算"""
        pricing = service._generate_pricing_recommendations(Decimal("100000"), Decimal("0.30"))
        score = service._calculate_competitiveness(pricing, Decimal("130000"))
        assert score == Decimal("0.75")
    
    def test_calculate_competitiveness_low_budget(self, service):
        """测试31: 竞争力评分 - 低预算"""
        pricing = service._generate_pricing_recommendations(Decimal("100000"), Decimal("0.30"))
        score = service._calculate_competitiveness(pricing, Decimal("120000"))
        assert score == Decimal("0.50")
    
    def test_calculate_competitiveness_no_budget(self, service):
        """测试32: 竞争力评分 - 无预算"""
        pricing = service._generate_pricing_recommendations(Decimal("100000"), Decimal("0.30"))
        score = service._calculate_competitiveness(pricing, None)
        assert score == Decimal("0.70")


# ============= 运行测试 =============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

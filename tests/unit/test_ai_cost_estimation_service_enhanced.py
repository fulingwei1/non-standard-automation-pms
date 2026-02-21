# -*- coding: utf-8 -*-
"""
增强的AI成本估算服务单元测试

测试覆盖：
- 成本估算（多场景）
- 成本优化（多场景）
- 定价推荐（多场景）
- 历史准确度（多场景）
- 实际成本更新（多场景）
- 各类私有方法（边界条件）
- 异常处理（边界条件）

目标：30-40个测试用例，覆盖率70%+
"""

import unittest
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, AsyncMock
from typing import List, Dict, Any, Optional

from app.services.sales.ai_cost_estimation_service import AICostEstimationService
from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    CostEstimationResponse,
    CostOptimizationInput,
    CostOptimizationResponse,
    PricingInput,
    PricingResponse,
    UpdateActualCostInput,
    HistoricalAccuracyResponse,
    CostBreakdown,
    OptimizationSuggestion,
    PricingRecommendation
)


class TestAICostEstimationService(unittest.TestCase):
    """AI成本估算服务测试基类"""
    
    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.user_id = 1
        self.service = AICostEstimationService(self.db, self.user_id)
        
        # Mock save_obj - 修复Pydantic验证bug：设置id和created_at
        self.patcher_save = patch('app.services.sales.ai_cost_estimation_service.save_obj')
        self.mock_save = self.patcher_save.start()
        
        def save_side_effect(db, obj):
            if not hasattr(obj, 'id') or obj.id is None:
                obj.id = 1
            if not hasattr(obj, 'created_at') or obj.created_at is None:
                obj.created_at = datetime.now()
            return obj
        
        self.mock_save.side_effect = save_side_effect
    
    def tearDown(self):
        """测试后置清理"""
        self.patcher_save.stop()
        self.db.reset_mock()


class TestInitialization(TestAICostEstimationService):
    """测试初始化"""
    
    def test_init_with_user(self):
        """测试用户初始化"""
        service = AICostEstimationService(self.db, user_id=5)
        self.assertEqual(service.user_id, 5)
        self.assertIs(service.db, self.db)
    
    def test_init_constants(self):
        """测试常量初始化"""
        self.assertEqual(self.service.MODEL_VERSION, "v1.0.0")
        self.assertEqual(self.service.HARDWARE_MARKUP, Decimal("1.15"))
        self.assertEqual(self.service.SOFTWARE_HOURLY_RATE, Decimal("800"))
        self.assertEqual(self.service.INSTALLATION_BASE_COST, Decimal("5000"))
        self.assertEqual(self.service.SERVICE_ANNUAL_RATE, Decimal("0.10"))
        self.assertEqual(self.service.RISK_RESERVE_RATE, Decimal("0.08"))


class TestHardwareCostCalculation(TestAICostEstimationService):
    """测试硬件成本计算"""
    
    def test_calculate_hardware_cost_empty_list(self):
        """测试空硬件列表"""
        result = self.service._calculate_hardware_cost(None)
        self.assertEqual(result, Decimal("0"))
        
        result = self.service._calculate_hardware_cost([])
        self.assertEqual(result, Decimal("0"))
    
    def test_calculate_hardware_cost_single_item(self):
        """测试单个硬件项"""
        items = [{"unit_price": 1000, "quantity": 2}]
        result = self.service._calculate_hardware_cost(items)
        # 1000 * 2 * 1.15 = 2300
        self.assertEqual(result, Decimal("2300"))
    
    def test_calculate_hardware_cost_multiple_items(self):
        """测试多个硬件项"""
        items = [
            {"unit_price": 1000, "quantity": 2},
            {"unit_price": 500, "quantity": 5},
            {"unit_price": 200, "quantity": 10}
        ]
        result = self.service._calculate_hardware_cost(items)
        # (1000*2 + 500*5 + 200*10) * 1.15 = 6500 * 1.15 = 7475
        self.assertEqual(result, Decimal("7475.00"))
    
    def test_calculate_hardware_cost_missing_fields(self):
        """测试缺失字段"""
        items = [{"unit_price": 1000}]  # 缺少quantity
        result = self.service._calculate_hardware_cost(items)
        # 1000 * 1 * 1.15 = 1150 (默认quantity=1)
        self.assertEqual(result, Decimal("1150"))
    
    def test_calculate_hardware_cost_decimal_values(self):
        """测试小数值"""
        items = [{"unit_price": 1234.56, "quantity": 3}]
        result = self.service._calculate_hardware_cost(items)
        # 1234.56 * 3 * 1.15 = 4259.232
        self.assertEqual(result, Decimal("4259.232"))


class TestSoftwareCostCalculation(TestAICostEstimationService):
    """测试软件成本计算"""
    
    def test_calculate_software_cost_with_man_days(self):
        """测试有明确人天"""
        result = self.service._calculate_software_cost("Some requirements", 10)
        # 10 * 8 * 800 = 64000
        self.assertEqual(result, Decimal("64000"))
    
    def test_calculate_software_cost_no_requirements_no_man_days(self):
        """测试无需求无人天"""
        result = self.service._calculate_software_cost(None, None)
        self.assertEqual(result, Decimal("0"))
    
    def test_calculate_software_cost_short_requirements(self):
        """测试短需求描述"""
        short_req = "A" * 50  # 50字符
        result = self.service._calculate_software_cost(short_req, None)
        # 自动估算5人天：5 * 8 * 800 = 32000
        self.assertEqual(result, Decimal("32000"))
    
    def test_calculate_software_cost_medium_requirements(self):
        """测试中等需求描述"""
        medium_req = "A" * 200  # 200字符
        result = self.service._calculate_software_cost(medium_req, None)
        # 自动估算15人天：15 * 8 * 800 = 96000
        self.assertEqual(result, Decimal("96000"))
    
    def test_calculate_software_cost_long_requirements(self):
        """测试长需求描述"""
        long_req = "A" * 600  # 600字符
        result = self.service._calculate_software_cost(long_req, None)
        # 自动估算30人天：30 * 8 * 800 = 192000
        self.assertEqual(result, Decimal("192000"))


class TestInstallationCostCalculation(TestAICostEstimationService):
    """测试安装成本计算"""
    
    def test_calculate_installation_cost_low_difficulty(self):
        """测试低难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("low", hardware_cost)
        # 5000 * 1.0 + 10000 * 0.05 = 5500
        self.assertEqual(result, Decimal("5500"))
    
    def test_calculate_installation_cost_medium_difficulty(self):
        """测试中等难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("medium", hardware_cost)
        # 5000 * 1.5 + 10000 * 0.05 = 8000
        self.assertEqual(result, Decimal("8000"))
    
    def test_calculate_installation_cost_high_difficulty(self):
        """测试高难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("high", hardware_cost)
        # 5000 * 2.0 + 10000 * 0.05 = 10500
        self.assertEqual(result, Decimal("10500"))
    
    def test_calculate_installation_cost_no_difficulty(self):
        """测试无难度指定"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost(None, hardware_cost)
        # 5000 * 1.0 + 10000 * 0.05 = 5500 (默认为低难度)
        self.assertEqual(result, Decimal("5500"))


class TestServiceCostCalculation(TestAICostEstimationService):
    """测试服务成本计算"""
    
    def test_calculate_service_cost_one_year(self):
        """测试1年服务"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 1)
        # 100000 * 0.10 * 1 = 10000
        self.assertEqual(result, Decimal("10000"))
    
    def test_calculate_service_cost_multiple_years(self):
        """测试多年服务"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 3)
        # 100000 * 0.10 * 3 = 30000
        self.assertEqual(result, Decimal("30000"))
    
    def test_calculate_service_cost_zero_years(self):
        """测试0年服务"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 0)
        self.assertEqual(result, Decimal("0"))


class TestRiskReserveCalculation(TestAICostEstimationService):
    """测试风险储备金计算"""
    
    def test_calculate_risk_reserve_medium_complexity(self):
        """测试中等复杂度"""
        # Mock数据库查询返回None（无历史数据）
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("IT", "medium", base_cost)
        # 100000 * 0.08 = 8000 (无历史数据时)
        self.assertEqual(result, Decimal("8000"))
    
    def test_calculate_risk_reserve_high_complexity(self):
        """测试高复杂度"""
        # Mock数据库查询返回None（无历史数据）
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("IT", "high", base_cost)
        # 100000 * 0.08 * 1.5 = 12000 (无历史数据时)
        self.assertEqual(result, Decimal("12000"))
    
    def test_calculate_risk_reserve_low_complexity(self):
        """测试低复杂度"""
        # Mock数据库查询返回None（无历史数据）
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("IT", "low", base_cost)
        # 100000 * 0.08 * 0.5 = 4000 (无历史数据时)
        self.assertEqual(result, Decimal("4000"))
    
    def test_calculate_risk_reserve_with_historical_variance(self):
        """测试有历史偏差数据"""
        # Mock数据库查询返回历史偏差
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.scalar.return_value = 10.5  # 10.5%偏差
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("IT", "medium", base_cost)
        
        # 应该根据历史数据调整
        self.assertIsInstance(result, Decimal)


class TestHistoricalVariance(TestAICostEstimationService):
    """测试历史偏差获取"""
    
    def test_get_historical_variance_no_data(self):
        """测试无历史数据"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.scalar.return_value = None
        
        result = self.service._get_historical_variance("IT")
        self.assertIsNone(result)
    
    def test_get_historical_variance_with_data(self):
        """测试有历史数据"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.scalar.return_value = 15.5
        
        result = self.service._get_historical_variance("IT")
        self.assertEqual(result, Decimal("0.155"))


class TestConfidenceScore(TestAICostEstimationService):
    """测试置信度计算"""
    
    def test_calculate_confidence_score_minimal_data(self):
        """测试最少数据"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IT",
            complexity_level="medium"
        )
        
        # Mock数据库查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.count.return_value = 0
        
        result = self.service._calculate_confidence_score(input_data)
        self.assertEqual(result, Decimal("0.5"))  # 仅基础分
    
    def test_calculate_confidence_score_with_hardware(self):
        """测试有硬件清单"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IT",
            complexity_level="medium",
            hardware_items=[{"unit_price": 1000, "quantity": 2}]
        )
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.count.return_value = 0
        
        result = self.service._calculate_confidence_score(input_data)
        self.assertEqual(result, Decimal("0.7"))  # 基础分 + 硬件分
    
    def test_calculate_confidence_score_full_data(self):
        """测试完整数据"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IT",
            complexity_level="medium",
            hardware_items=[{"unit_price": 1000, "quantity": 2}],
            software_requirements="A" * 200,
            estimated_man_days=10
        )
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.count.return_value = 15  # 足够的历史数据
        
        result = self.service._calculate_confidence_score(input_data)
        self.assertEqual(result, Decimal("1.0"))  # 满分


class TestPricingRecommendations(TestAICostEstimationService):
    """测试定价推荐"""
    
    def test_generate_pricing_recommendations_default_margin(self):
        """测试默认毛利率"""
        total_cost = Decimal("100000")
        target_margin = Decimal("0.30")
        
        result = self.service._generate_pricing_recommendations(total_cost, target_margin)
        
        # suggested_price = 100000 / (1 - 0.30) = 142857.14...
        self.assertIsInstance(result, PricingRecommendation)
        self.assertAlmostEqual(float(result.suggested_price), 142857.14, places=2)
        self.assertEqual(result.target_margin_rate, Decimal("30"))
    
    def test_generate_pricing_recommendations_high_margin(self):
        """测试高毛利率"""
        total_cost = Decimal("100000")
        target_margin = Decimal("0.50")
        
        result = self.service._generate_pricing_recommendations(total_cost, target_margin)
        
        # suggested_price = 100000 / (1 - 0.50) = 200000
        self.assertEqual(result.suggested_price, Decimal("200000"))
    
    def test_generate_pricing_recommendations_price_ranges(self):
        """测试价格区间"""
        total_cost = Decimal("100000")
        target_margin = Decimal("0.30")
        
        result = self.service._generate_pricing_recommendations(total_cost, target_margin)
        
        # 检查low < medium < high
        self.assertLess(result.low, result.medium)
        self.assertLess(result.medium, result.high)
        
        # 检查medium = suggested_price
        self.assertEqual(result.medium, result.suggested_price)


class TestPricingSensitivity(TestAICostEstimationService):
    """测试价格敏感度分析"""
    
    def test_analyze_price_sensitivity_no_budget(self):
        """测试无客户预算"""
        cost = Decimal("100000")
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._analyze_price_sensitivity(cost, pricing, None)
        
        self.assertIn("cost_base", result)
        self.assertIn("price_range", result)
        self.assertIn("margin_analysis", result)
        self.assertNotIn("budget_fit", result)
    
    def test_analyze_price_sensitivity_with_budget(self):
        """测试有客户预算"""
        cost = Decimal("100000")
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        customer_budget = Decimal("150000")
        
        result = self.service._analyze_price_sensitivity(cost, pricing, customer_budget)
        
        self.assertIn("budget_fit", result)
        self.assertEqual(result["budget_fit"]["customer_budget"], 150000.0)


class TestPricingStrategy(TestAICostEstimationService):
    """测试定价策略"""
    
    def test_get_pricing_strategy_high_budget(self):
        """测试高预算"""
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._get_pricing_strategy(Decimal("170000"), pricing)
        self.assertIn("高价档", result)
    
    def test_get_pricing_strategy_medium_budget(self):
        """测试中等预算"""
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._get_pricing_strategy(Decimal("150000"), pricing)
        self.assertIn("标准报价", result)
    
    def test_get_pricing_strategy_low_budget(self):
        """测试低预算"""
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._get_pricing_strategy(Decimal("135000"), pricing)
        self.assertIn("低价档", result)
    
    def test_get_pricing_strategy_insufficient_budget(self):
        """测试预算不足"""
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._get_pricing_strategy(Decimal("120000"), pricing)
        self.assertIn("低于成本", result)


class TestCompetitiveness(TestAICostEstimationService):
    """测试竞争力评分"""
    
    def test_calculate_competitiveness_no_budget(self):
        """测试无预算"""
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._calculate_competitiveness(pricing, None)
        self.assertEqual(result, Decimal("0.70"))
    
    def test_calculate_competitiveness_high_budget(self):
        """测试高预算"""
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._calculate_competitiveness(pricing, Decimal("150000"))
        self.assertEqual(result, Decimal("0.90"))
    
    def test_calculate_competitiveness_medium_budget(self):
        """测试中等预算"""
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._calculate_competitiveness(pricing, Decimal("135000"))
        self.assertEqual(result, Decimal("0.75"))
    
    def test_calculate_competitiveness_low_budget(self):
        """测试低预算"""
        pricing = PricingRecommendation(
            low=Decimal("130000"),
            medium=Decimal("145000"),
            high=Decimal("165000"),
            suggested_price=Decimal("145000"),
            target_margin_rate=Decimal("30"),
            market_analysis="Test"
        )
        
        result = self.service._calculate_competitiveness(pricing, Decimal("120000"))
        self.assertEqual(result, Decimal("0.50"))


class TestRiskAcceptability(TestAICostEstimationService):
    """测试风险接受度"""
    
    def test_is_acceptable_risk_no_feasibility(self):
        """测试无可行性评分"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="Test",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=None
        )
        
        result = self.service._is_acceptable_risk(suggestion, "medium")
        self.assertTrue(result)
    
    def test_is_acceptable_risk_low_level(self):
        """测试低风险接受度"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="Test",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.80")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertFalse(result)  # 0.80 < 0.85
        
        suggestion.feasibility_score = Decimal("0.90")
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertTrue(result)
    
    def test_is_acceptable_risk_medium_level(self):
        """测试中等风险接受度"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="Test",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.75")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "medium")
        self.assertTrue(result)
    
    def test_is_acceptable_risk_high_level(self):
        """测试高风险接受度"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="Test",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.55")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "high")
        self.assertTrue(result)


class TestAverageFeasibility(TestAICostEstimationService):
    """测试平均可行性"""
    
    def test_calculate_avg_feasibility_empty(self):
        """测试空列表"""
        result = self.service._calculate_avg_feasibility([])
        self.assertEqual(result, Decimal("0"))
    
    def test_calculate_avg_feasibility_single(self):
        """测试单个建议"""
        suggestions = [
            OptimizationSuggestion(
                type="hardware",
                description="Test",
                original_cost=Decimal("1000"),
                optimized_cost=Decimal("900"),
                saving_amount=Decimal("100"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.85")
            )
        ]
        
        result = self.service._calculate_avg_feasibility(suggestions)
        self.assertEqual(result, Decimal("0.85"))
    
    def test_calculate_avg_feasibility_multiple(self):
        """测试多个建议"""
        suggestions = [
            OptimizationSuggestion(
                type="hardware",
                description="Test",
                original_cost=Decimal("1000"),
                optimized_cost=Decimal("900"),
                saving_amount=Decimal("100"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.80")
            ),
            OptimizationSuggestion(
                type="software",
                description="Test",
                original_cost=Decimal("2000"),
                optimized_cost=Decimal("1800"),
                saving_amount=Decimal("200"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.90")
            )
        ]
        
        result = self.service._calculate_avg_feasibility(suggestions)
        self.assertEqual(result, Decimal("0.85"))


class TestEstimateCostIntegration(TestAICostEstimationService):
    """测试成本估算集成"""
    
    @pytest.mark.asyncio
    @patch('app.services.sales.ai_cost_estimation_service.AICostEstimationService._generate_optimization_suggestions')
    async def test_estimate_cost_minimal_input(self, mock_suggestions):
        """测试最小输入"""
        mock_suggestions.return_value = []
        
        # Mock数据库查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.count.return_value = 0
        mock_query.filter.return_value.scalar.return_value = None
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IT",
            complexity_level="medium"
        )
        
        result = await self.service.estimate_cost(input_data)
        
        self.assertIsInstance(result, CostEstimationResponse)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.presale_ticket_id, 1)
        self.assertIsNotNone(result.cost_breakdown)
        self.assertIsNotNone(result.created_at)
    
    @pytest.mark.asyncio
    @patch('app.services.sales.ai_cost_estimation_service.AICostEstimationService._generate_optimization_suggestions')
    async def test_estimate_cost_full_input(self, mock_suggestions):
        """测试完整输入"""
        mock_suggestions.return_value = []
        
        # Mock数据库查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.count.return_value = 0
        mock_query.filter.return_value.scalar.return_value = None
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            solution_id=2,
            project_type="IT",
            industry="Finance",
            complexity_level="high",
            hardware_items=[
                {"unit_price": 1000, "quantity": 5},
                {"unit_price": 500, "quantity": 10}
            ],
            software_requirements="详细的软件需求描述" * 20,
            estimated_man_days=20,
            installation_difficulty="high",
            service_years=3,
            target_margin_rate=Decimal("0.35")
        )
        
        result = await self.service.estimate_cost(input_data)
        
        self.assertIsInstance(result, CostEstimationResponse)
        self.assertGreater(result.cost_breakdown.total_cost, Decimal("0"))
        self.assertGreater(result.cost_breakdown.hardware_cost, Decimal("0"))
        self.assertGreater(result.cost_breakdown.software_cost, Decimal("0"))


class TestOptimizeCostIntegration(TestAICostEstimationService):
    """测试成本优化集成"""
    
    @pytest.mark.asyncio
    async def test_optimize_cost_not_found(self):
        """测试估算记录不存在"""
        # Mock数据库查询返回None
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        input_data = CostOptimizationInput(estimation_id=999)
        
        with self.assertRaises(ValueError) as context:
            await self.service.optimize_cost(input_data)
        
        self.assertIn("不存在", str(context.exception))
    
    @pytest.mark.asyncio
    async def test_optimize_cost_no_suggestions(self):
        """测试无优化建议"""
        # Mock估算记录
        mock_estimation = MagicMock()
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        mock_estimation.optimization_suggestions = None
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_estimation
        
        input_data = CostOptimizationInput(estimation_id=1)
        
        result = await self.service.optimize_cost(input_data)
        
        self.assertIsInstance(result, CostOptimizationResponse)
        self.assertEqual(result.original_total_cost, Decimal("100000"))
        self.assertEqual(result.optimized_total_cost, Decimal("100000"))
        self.assertEqual(result.total_saving, Decimal("0"))


class TestRecommendPricingIntegration(TestAICostEstimationService):
    """测试定价推荐集成"""
    
    @pytest.mark.asyncio
    async def test_recommend_pricing_not_found(self):
        """测试估算记录不存在"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        input_data = PricingInput(estimation_id=999)
        
        with self.assertRaises(ValueError) as context:
            await self.service.recommend_pricing(input_data)
        
        self.assertIn("不存在", str(context.exception))
    
    @pytest.mark.asyncio
    async def test_recommend_pricing_basic(self):
        """测试基本定价推荐"""
        # Mock估算记录
        mock_estimation = MagicMock()
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_estimation
        
        input_data = PricingInput(
            estimation_id=1,
            target_margin_rate=Decimal("0.30")
        )
        
        result = await self.service.recommend_pricing(input_data)
        
        self.assertIsInstance(result, PricingResponse)
        self.assertEqual(result.cost_base, Decimal("100000"))
        self.assertIsNotNone(result.pricing_recommendations)


class TestHistoricalAccuracyIntegration(TestAICostEstimationService):
    """测试历史准确度集成"""
    
    @pytest.mark.asyncio
    async def test_get_historical_accuracy_no_data(self):
        """测试无历史数据"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.all.return_value = []
        
        result = await self.service.get_historical_accuracy()
        
        self.assertIsInstance(result, HistoricalAccuracyResponse)
        self.assertEqual(result.total_predictions, 0)
        self.assertEqual(result.average_variance_rate, Decimal("0"))
        self.assertEqual(result.accuracy_rate, Decimal("0"))
    
    @pytest.mark.asyncio
    async def test_get_historical_accuracy_with_data(self):
        """测试有历史数据"""
        # Mock历史记录
        mock_history1 = MagicMock()
        mock_history1.variance_rate = Decimal("10")
        
        mock_history2 = MagicMock()
        mock_history2.variance_rate = Decimal("5")
        
        mock_history3 = MagicMock()
        mock_history3.variance_rate = Decimal("-8")
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.all.return_value = [mock_history1, mock_history2, mock_history3]
        
        result = await self.service.get_historical_accuracy()
        
        self.assertIsInstance(result, HistoricalAccuracyResponse)
        self.assertEqual(result.total_predictions, 3)
        # 平均偏差率 = (10 + 5 - 8) / 3 = 2.33...
        self.assertAlmostEqual(float(result.average_variance_rate), 2.33, places=2)


class TestUpdateActualCostIntegration(TestAICostEstimationService):
    """测试更新实际成本集成"""
    
    @pytest.mark.asyncio
    async def test_update_actual_cost_not_found(self):
        """测试估算记录不存在"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        input_data = UpdateActualCostInput(
            estimation_id=999,
            actual_cost=Decimal("100000")
        )
        
        with self.assertRaises(ValueError) as context:
            await self.service.update_actual_cost(input_data)
        
        self.assertIn("不存在", str(context.exception))
    
    @pytest.mark.asyncio
    async def test_update_actual_cost_basic(self):
        """测试基本实际成本更新"""
        # Mock估算记录
        mock_estimation = MagicMock()
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        mock_estimation.input_parameters = {"project_type": "IT"}
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_estimation
        
        input_data = UpdateActualCostInput(
            estimation_id=1,
            project_id=1,
            project_name="Test Project",
            actual_cost=Decimal("110000")
        )
        
        result = await self.service.update_actual_cost(input_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["history_id"], 1)
        self.assertEqual(result["variance_rate"], Decimal("10"))  # (110000-100000)/100000*100


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)

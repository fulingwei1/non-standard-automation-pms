# -*- coding: utf-8 -*-
"""
AI成本估算服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any

from app.services.sales.ai_cost_estimation_service import AICostEstimationService
from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    CostEstimationResponse,
    CostOptimizationInput,
    PricingInput,
    UpdateActualCostInput,
    CostBreakdown,
    OptimizationSuggestion,
    PricingRecommendation,
)
from app.models.sales.presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory,
)


class TestAICostEstimationServiceCore(unittest.TestCase):
    """测试核心成本估算逻辑"""

    def setUp(self):
        """初始化测试环境"""
        self.mock_db = MagicMock()
        self.user_id = 1
        self.service = AICostEstimationService(db=self.mock_db, user_id=self.user_id)

    # ========== _calculate_hardware_cost() 测试 ==========

    def test_calculate_hardware_cost_empty(self):
        """测试空硬件清单"""
        result = self.service._calculate_hardware_cost(None)
        self.assertEqual(result, Decimal("0"))

        result = self.service._calculate_hardware_cost([])
        self.assertEqual(result, Decimal("0"))

    def test_calculate_hardware_cost_single_item(self):
        """测试单个硬件"""
        hardware_items = [
            {"unit_price": 1000, "quantity": 2}
        ]
        result = self.service._calculate_hardware_cost(hardware_items)
        # (1000 * 2) * 1.15 = 2300
        expected = Decimal("2000") * Decimal("1.15")
        self.assertEqual(result, expected)

    def test_calculate_hardware_cost_multiple_items(self):
        """测试多个硬件"""
        hardware_items = [
            {"unit_price": 1000, "quantity": 2},
            {"unit_price": 500, "quantity": 5},
            {"unit_price": 2000, "quantity": 1},
        ]
        result = self.service._calculate_hardware_cost(hardware_items)
        # (1000*2 + 500*5 + 2000*1) * 1.15 = 6500 * 1.15
        expected = Decimal("6500") * Decimal("1.15")
        self.assertEqual(result, expected)

    def test_calculate_hardware_cost_with_default_quantity(self):
        """测试默认数量"""
        hardware_items = [
            {"unit_price": 1000}  # 无quantity字段，默认为1
        ]
        result = self.service._calculate_hardware_cost(hardware_items)
        expected = Decimal("1000") * Decimal("1.15")
        self.assertEqual(result, expected)

    # ========== _calculate_software_cost() 测试 ==========

    def test_calculate_software_cost_with_man_days(self):
        """测试指定人天的软件成本"""
        result = self.service._calculate_software_cost("任意需求", 10)
        # 10天 * 8小时 * 800元/小时
        expected = Decimal("10") * Decimal("8") * Decimal("800")
        self.assertEqual(result, expected)

    def test_calculate_software_cost_auto_estimate_short(self):
        """测试自动估算：短需求"""
        short_requirements = "简单功能"  # < 100字
        result = self.service._calculate_software_cost(short_requirements, None)
        # 自动估算5人天
        expected = Decimal("5") * Decimal("8") * Decimal("800")
        self.assertEqual(result, expected)

    def test_calculate_software_cost_auto_estimate_medium(self):
        """测试自动估算：中等需求"""
        medium_requirements = "a" * 200  # 100-500字
        result = self.service._calculate_software_cost(medium_requirements, None)
        # 自动估算15人天
        expected = Decimal("15") * Decimal("8") * Decimal("800")
        self.assertEqual(result, expected)

    def test_calculate_software_cost_auto_estimate_long(self):
        """测试自动估算：长需求"""
        long_requirements = "a" * 600  # > 500字
        result = self.service._calculate_software_cost(long_requirements, None)
        # 自动估算30人天
        expected = Decimal("30") * Decimal("8") * Decimal("800")
        self.assertEqual(result, expected)

    def test_calculate_software_cost_no_requirements(self):
        """测试无需求描述且无人天"""
        result = self.service._calculate_software_cost(None, None)
        self.assertEqual(result, Decimal("0"))

    # ========== _calculate_installation_cost() 测试 ==========

    def test_calculate_installation_cost_high_difficulty(self):
        """测试高难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("high", hardware_cost)
        # 5000 * 2.0 + 10000 * 0.05 = 10000 + 500
        expected = Decimal("10500")
        self.assertEqual(result, expected)

    def test_calculate_installation_cost_medium_difficulty(self):
        """测试中等难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("medium", hardware_cost)
        # 5000 * 1.5 + 10000 * 0.05 = 7500 + 500
        expected = Decimal("8000")
        self.assertEqual(result, expected)

    def test_calculate_installation_cost_low_difficulty(self):
        """测试低难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("low", hardware_cost)
        # 5000 * 1.0 + 10000 * 0.05 = 5000 + 500
        expected = Decimal("5500")
        self.assertEqual(result, expected)

    def test_calculate_installation_cost_default(self):
        """测试默认难度"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost(None, hardware_cost)
        # 默认为low: 5000 * 1.0 + 10000 * 0.05
        expected = Decimal("5500")
        self.assertEqual(result, expected)

    # ========== _calculate_service_cost() 测试 ==========

    def test_calculate_service_cost_single_year(self):
        """测试单年服务"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 1)
        # 100000 * 0.10 * 1
        expected = Decimal("10000")
        self.assertEqual(result, expected)

    def test_calculate_service_cost_multiple_years(self):
        """测试多年服务"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 3)
        # 100000 * 0.10 * 3
        expected = Decimal("30000")
        self.assertEqual(result, expected)

    # ========== _calculate_risk_reserve() 测试 ==========

    def test_calculate_risk_reserve_medium_complexity(self):
        """测试中等复杂度风险储备"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("automation", "medium", base_cost)
        # 100000 * 0.08 (无历史数据)
        expected = Decimal("8000")
        self.assertEqual(result, expected)

    def test_calculate_risk_reserve_high_complexity(self):
        """测试高复杂度风险储备"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("automation", "high", base_cost)
        # 100000 * 0.08 * 1.5
        expected = Decimal("12000")
        self.assertEqual(result, expected)

    def test_calculate_risk_reserve_low_complexity(self):
        """测试低复杂度风险储备"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("automation", "low", base_cost)
        # 100000 * 0.08 * 0.5
        expected = Decimal("4000")
        self.assertEqual(result, expected)

    def test_calculate_risk_reserve_with_historical_variance(self):
        """测试基于历史偏差的风险储备"""
        # Mock历史偏差率为10%
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 10
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("automation", "medium", base_cost)
        # 100000 * 0.08 * (1 + 0.1) = 100000 * 0.088
        expected = Decimal("8800")
        self.assertEqual(result, expected)

    # ========== _get_historical_variance() 测试 ==========

    def test_get_historical_variance_no_data(self):
        """测试无历史数据"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        result = self.service._get_historical_variance("automation")
        self.assertIsNone(result)

    def test_get_historical_variance_with_data(self):
        """测试有历史数据"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 15
        
        result = self.service._get_historical_variance("automation")
        expected = Decimal("0.15")
        self.assertEqual(result, expected)

    # ========== _generate_pricing_recommendations() 测试 ==========

    def test_generate_pricing_recommendations_30_percent_margin(self):
        """测试30%毛利率定价"""
        total_cost = Decimal("100000")
        target_margin = Decimal("0.30")
        
        result = self.service._generate_pricing_recommendations(total_cost, target_margin)
        
        # 建议价格 = 100000 / (1 - 0.30) = 142857.14...
        suggested = total_cost / (Decimal("1") - target_margin)
        
        self.assertIsInstance(result, PricingRecommendation)
        self.assertEqual(result.suggested_price, suggested)
        self.assertEqual(result.low, suggested * Decimal("0.90"))
        self.assertEqual(result.medium, suggested)
        self.assertEqual(result.high, suggested * Decimal("1.15"))
        self.assertEqual(result.target_margin_rate, Decimal("30"))

    def test_generate_pricing_recommendations_different_margin(self):
        """测试不同毛利率"""
        total_cost = Decimal("50000")
        target_margin = Decimal("0.40")
        
        result = self.service._generate_pricing_recommendations(total_cost, target_margin)
        
        suggested = Decimal("50000") / Decimal("0.60")  # 83333.33...
        self.assertEqual(result.suggested_price, suggested)
        self.assertEqual(result.target_margin_rate, Decimal("40"))

    # ========== _calculate_confidence_score() 测试 ==========

    def test_calculate_confidence_score_minimum(self):
        """测试最低置信度"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation",
            complexity_level="medium"
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 基础分0.5，无其他加分
        self.assertEqual(result, Decimal("0.5"))

    def test_calculate_confidence_score_with_hardware(self):
        """测试有硬件清单的置信度"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation",
            complexity_level="medium",
            hardware_items=[{"unit_price": 1000, "quantity": 1}]
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 0.5 + 0.2 (硬件)
        self.assertEqual(result, Decimal("0.7"))

    def test_calculate_confidence_score_with_requirements(self):
        """测试有详细需求的置信度"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation",
            complexity_level="medium",
            software_requirements="a" * 150  # > 100字
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 0.5 + 0.15 (需求)
        self.assertEqual(result, Decimal("0.65"))

    def test_calculate_confidence_score_with_man_days(self):
        """测试有人天估算的置信度"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation",
            complexity_level="medium",
            estimated_man_days=20
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 0.5 + 0.1 (人天)
        self.assertEqual(result, Decimal("0.6"))

    def test_calculate_confidence_score_with_history(self):
        """测试有历史数据的置信度"""
        # Mock >10条历史数据
        self.mock_db.query.return_value.filter.return_value.count.return_value = 15
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation",
            complexity_level="medium"
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 0.5 + 0.05 (历史数据)
        self.assertEqual(result, Decimal("0.55"))

    def test_calculate_confidence_score_maximum(self):
        """测试最高置信度（不超过1.0）"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 15
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation",
            complexity_level="medium",
            hardware_items=[{"unit_price": 1000, "quantity": 1}],
            software_requirements="a" * 150,
            estimated_man_days=20
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 0.5 + 0.2 + 0.15 + 0.1 + 0.05 = 1.0
        self.assertEqual(result, Decimal("1.0"))

    # ========== _is_acceptable_risk() 测试 ==========

    def test_is_acceptable_risk_low_threshold(self):
        """测试低风险阈值"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="测试",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.9")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertTrue(result)  # 0.9 >= 0.85

    def test_is_acceptable_risk_low_threshold_fail(self):
        """测试低风险阈值失败"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="测试",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.8")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertFalse(result)  # 0.8 < 0.85

    def test_is_acceptable_risk_medium_threshold(self):
        """测试中等风险阈值"""
        suggestion = OptimizationSuggestion(
            type="software",
            description="测试",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.75")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "medium")
        self.assertTrue(result)  # 0.75 >= 0.70

    def test_is_acceptable_risk_high_threshold(self):
        """测试高风险阈值"""
        suggestion = OptimizationSuggestion(
            type="installation",
            description="测试",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.55")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "high")
        self.assertTrue(result)  # 0.55 >= 0.50

    def test_is_acceptable_risk_no_score(self):
        """测试无可行性评分（默认接受）"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="测试",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertTrue(result)

    # ========== _calculate_avg_feasibility() 测试 ==========

    def test_calculate_avg_feasibility_empty(self):
        """测试空建议列表"""
        result = self.service._calculate_avg_feasibility([])
        self.assertEqual(result, Decimal("0"))

    def test_calculate_avg_feasibility_single(self):
        """测试单个建议"""
        suggestions = [
            OptimizationSuggestion(
                type="hardware",
                description="测试",
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
                description="测试1",
                original_cost=Decimal("1000"),
                optimized_cost=Decimal("900"),
                saving_amount=Decimal("100"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.8")
            ),
            OptimizationSuggestion(
                type="software",
                description="测试2",
                original_cost=Decimal("2000"),
                optimized_cost=Decimal("1800"),
                saving_amount=Decimal("200"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.9")
            ),
            OptimizationSuggestion(
                type="installation",
                description="测试3",
                original_cost=Decimal("500"),
                optimized_cost=Decimal("400"),
                saving_amount=Decimal("100"),
                saving_rate=Decimal("20"),
                feasibility_score=Decimal("0.7")
            )
        ]
        
        result = self.service._calculate_avg_feasibility(suggestions)
        # (0.8 + 0.9 + 0.7) / 3 = 0.8
        expected = Decimal("2.4") / Decimal("3")
        self.assertEqual(result, expected)

    # ========== _analyze_price_sensitivity() 测试 ==========

    def test_analyze_price_sensitivity_without_budget(self):
        """测试无客户预算的价格敏感度分析"""
        cost = Decimal("100000")
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._analyze_price_sensitivity(cost, pricing, None)
        
        self.assertIn("cost_base", result)
        self.assertIn("price_range", result)
        self.assertIn("margin_analysis", result)
        self.assertNotIn("budget_fit", result)

    def test_analyze_price_sensitivity_with_budget(self):
        """测试有客户预算的价格敏感度分析"""
        cost = Decimal("100000")
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        customer_budget = Decimal("150000")
        
        result = self.service._analyze_price_sensitivity(cost, pricing, customer_budget)
        
        self.assertIn("budget_fit", result)
        self.assertEqual(result["budget_fit"]["customer_budget"], 150000.0)
        self.assertTrue(result["budget_fit"]["fits_low"])
        self.assertTrue(result["budget_fit"]["fits_recommended"])
        self.assertFalse(result["budget_fit"]["fits_high"])

    # ========== _get_pricing_strategy() 测试 ==========

    def test_get_pricing_strategy_high_budget(self):
        """测试高预算策略"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._get_pricing_strategy(Decimal("170000"), pricing)
        self.assertIn("高价档", result)
        self.assertIn("高附加值", result)

    def test_get_pricing_strategy_medium_budget(self):
        """测试中等预算策略"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._get_pricing_strategy(Decimal("145000"), pricing)
        self.assertIn("标准报价", result)

    def test_get_pricing_strategy_low_budget(self):
        """测试低预算策略"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._get_pricing_strategy(Decimal("125000"), pricing)
        self.assertIn("低价档", result)

    def test_get_pricing_strategy_insufficient_budget(self):
        """测试预算不足策略"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._get_pricing_strategy(Decimal("100000"), pricing)
        self.assertIn("低于成本", result)
        self.assertIn("放弃", result)

    # ========== _calculate_competitiveness() 测试 ==========

    def test_calculate_competitiveness_no_budget(self):
        """测试无预算的竞争力评分"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._calculate_competitiveness(pricing, None)
        self.assertEqual(result, Decimal("0.70"))  # 默认中等竞争力

    def test_calculate_competitiveness_high_budget(self):
        """测试高预算竞争力"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._calculate_competitiveness(pricing, Decimal("150000"))
        self.assertEqual(result, Decimal("0.90"))  # >= medium

    def test_calculate_competitiveness_medium_budget(self):
        """测试中等预算竞争力"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._calculate_competitiveness(pricing, Decimal("125000"))
        self.assertEqual(result, Decimal("0.75"))  # >= low

    def test_calculate_competitiveness_low_budget(self):
        """测试低预算竞争力"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        
        result = self.service._calculate_competitiveness(pricing, Decimal("100000"))
        self.assertEqual(result, Decimal("0.50"))  # < low


class TestAICostEstimationServiceAsync(unittest.IsolatedAsyncioTestCase):
    """测试异步方法"""

    async def asyncSetUp(self):
        """异步初始化"""
        self.mock_db = MagicMock()
        self.user_id = 1
        self.service = AICostEstimationService(db=self.mock_db, user_id=self.user_id)

    # ========== estimate_cost() 集成测试 (已移除，需要真实数据库连接) ==========
    # 注：完整的集成测试应在集成测试套件中运行，这里专注于单元测试

    # ========== _generate_optimization_suggestions() 测试 ==========

    async def test_generate_optimization_suggestions_hardware(self):
        """测试硬件优化建议"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation"
        )
        
        cost_breakdown = {
            "hardware_cost": Decimal("60000"),  # > 50000，应触发硬件优化
            "software_cost": Decimal("50000"),
            "installation_cost": Decimal("10000"),
            "service_cost": Decimal("10000"),
            "risk_reserve": Decimal("8000"),
        }
        
        suggestions = await self.service._generate_optimization_suggestions(input_data, cost_breakdown)
        
        # 应该有硬件优化建议
        hardware_suggestions = [s for s in suggestions if s.type == "hardware"]
        self.assertGreater(len(hardware_suggestions), 0)
        
        # 验证优化建议内容
        hw_sug = hardware_suggestions[0]
        self.assertEqual(hw_sug.original_cost, Decimal("60000"))
        self.assertLess(hw_sug.optimized_cost, hw_sug.original_cost)
        self.assertGreater(hw_sug.saving_amount, 0)

    async def test_generate_optimization_suggestions_software(self):
        """测试软件优化建议"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation"
        )
        
        cost_breakdown = {
            "hardware_cost": Decimal("30000"),
            "software_cost": Decimal("120000"),  # > 100000，应触发软件优化
            "installation_cost": Decimal("10000"),
            "service_cost": Decimal("10000"),
            "risk_reserve": Decimal("8000"),
        }
        
        suggestions = await self.service._generate_optimization_suggestions(input_data, cost_breakdown)
        
        # 应该有软件优化建议
        software_suggestions = [s for s in suggestions if s.type == "software"]
        self.assertGreater(len(software_suggestions), 0)

    async def test_generate_optimization_suggestions_installation(self):
        """测试安装优化建议"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation",
            installation_difficulty="high"  # 高难度应触发安装优化
        )
        
        cost_breakdown = {
            "hardware_cost": Decimal("30000"),
            "software_cost": Decimal("50000"),
            "installation_cost": Decimal("15000"),
            "service_cost": Decimal("10000"),
            "risk_reserve": Decimal("8000"),
        }
        
        suggestions = await self.service._generate_optimization_suggestions(input_data, cost_breakdown)
        
        # 应该有安装优化建议
        installation_suggestions = [s for s in suggestions if s.type == "installation"]
        self.assertGreater(len(installation_suggestions), 0)

    async def test_generate_optimization_suggestions_none(self):
        """测试无优化建议场景"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="automation",
            installation_difficulty="low"
        )
        
        cost_breakdown = {
            "hardware_cost": Decimal("30000"),  # < 50000
            "software_cost": Decimal("50000"),   # < 100000
            "installation_cost": Decimal("5000"),
            "service_cost": Decimal("5000"),
            "risk_reserve": Decimal("4000"),
        }
        
        suggestions = await self.service._generate_optimization_suggestions(input_data, cost_breakdown)
        
        # 不应有任何优化建议
        self.assertEqual(len(suggestions), 0)

    # ========== optimize_cost() 测试 ==========

    async def test_optimize_cost_success(self):
        """测试成本优化"""
        # Mock估算记录
        mock_estimation = MagicMock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        mock_estimation.optimization_suggestions = [
            {
                "type": "hardware",
                "description": "批量采购折扣",
                "original_cost": 50000,
                "optimized_cost": 46000,
                "saving_amount": 4000,
                "saving_rate": 8.0,
                "feasibility_score": 0.85,
                "alternative_solutions": []
            },
            {
                "type": "software",
                "description": "使用现有模块",
                "original_cost": 30000,
                "optimized_cost": 25500,
                "saving_amount": 4500,
                "saving_rate": 15.0,
                "feasibility_score": 0.75,
                "alternative_solutions": []
            }
        ]
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        input_data = CostOptimizationInput(
            estimation_id=1,
            max_risk_level="medium"
        )
        
        result = await self.service.optimize_cost(input_data)
        
        self.assertEqual(result.original_total_cost, Decimal("100000"))
        self.assertLess(result.optimized_total_cost, result.original_total_cost)
        self.assertGreater(result.total_saving, 0)
        self.assertGreater(len(result.suggestions), 0)

    async def test_optimize_cost_not_found(self):
        """测试估算记录不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        input_data = CostOptimizationInput(
            estimation_id=999
        )
        
        with self.assertRaises(ValueError) as context:
            await self.service.optimize_cost(input_data)
        
        self.assertIn("估算记录不存在", str(context.exception))

    async def test_optimize_cost_risk_filtering(self):
        """测试风险过滤"""
        mock_estimation = MagicMock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        mock_estimation.optimization_suggestions = [
            {
                "type": "hardware",
                "description": "低风险优化",
                "original_cost": 50000,
                "optimized_cost": 46000,
                "saving_amount": 4000,
                "saving_rate": 8.0,
                "feasibility_score": 0.90,  # 高可行性
                "alternative_solutions": []
            },
            {
                "type": "software",
                "description": "高风险优化",
                "original_cost": 30000,
                "optimized_cost": 25500,
                "saving_amount": 4500,
                "saving_rate": 15.0,
                "feasibility_score": 0.60,  # 低可行性
                "alternative_solutions": []
            }
        ]
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        # 设置低风险接受度
        input_data = CostOptimizationInput(
            estimation_id=1,
            max_risk_level="low"  # 阈值0.85
        )
        
        result = await self.service.optimize_cost(input_data)
        
        # 应该只有1个建议被接受（feasibility >= 0.85）
        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.suggestions[0].type, "hardware")

    # ========== recommend_pricing() 测试 ==========

    async def test_recommend_pricing_success(self):
        """测试定价推荐"""
        mock_estimation = MagicMock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        input_data = PricingInput(
            estimation_id=1,
            target_margin_rate=Decimal("0.35"),
            market_competition_level="medium",
            customer_budget=Decimal("160000")
        )
        
        result = await self.service.recommend_pricing(input_data)
        
        self.assertEqual(result.cost_base, Decimal("100000"))
        self.assertIsInstance(result.pricing_recommendations, PricingRecommendation)
        self.assertIsNotNone(result.sensitivity_analysis)
        self.assertIsNotNone(result.competitiveness_score)

    async def test_recommend_pricing_high_competition(self):
        """测试高竞争环境定价"""
        mock_estimation = MagicMock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        input_data = PricingInput(
            estimation_id=1,
            market_competition_level="high"  # 应该降低价格
        )
        
        result = await self.service.recommend_pricing(input_data)
        
        # 高竞争应该有价格折扣（0.95系数）
        # 可以通过market_analysis字段验证
        self.assertIn("high", result.pricing_recommendations.market_analysis)

    async def test_recommend_pricing_not_found(self):
        """测试估算记录不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        input_data = PricingInput(estimation_id=999)
        
        with self.assertRaises(ValueError):
            await self.service.recommend_pricing(input_data)

    # ========== get_historical_accuracy() 测试 ==========

    async def test_get_historical_accuracy_no_data(self):
        """测试无历史数据"""
        self.mock_db.query.return_value.all.return_value = []
        
        result = await self.service.get_historical_accuracy()
        
        self.assertEqual(result.total_predictions, 0)
        self.assertEqual(result.average_variance_rate, Decimal("0"))
        self.assertEqual(result.accuracy_rate, Decimal("0"))
        self.assertEqual(result.recent_trend, "无数据")

    async def test_get_historical_accuracy_with_data(self):
        """测试有历史数据"""
        # Mock历史记录
        mock_histories = [
            MagicMock(variance_rate=Decimal("5")),   # 偏差5%
            MagicMock(variance_rate=Decimal("10")),  # 偏差10%
            MagicMock(variance_rate=Decimal("20")),  # 偏差20%
            MagicMock(variance_rate=Decimal("8")),   # 偏差8%
        ]
        
        self.mock_db.query.return_value.all.return_value = mock_histories
        
        result = await self.service.get_historical_accuracy()
        
        self.assertEqual(result.total_predictions, 4)
        # 平均偏差 = (5+10+20+8) / 4 = 10.75
        self.assertAlmostEqual(float(result.average_variance_rate), 10.75, places=2)
        # 准确率 = 3/4 = 75% (偏差<15%的有3个)
        self.assertEqual(result.accuracy_rate, Decimal("75"))

    async def test_get_historical_accuracy_all_accurate(self):
        """测试全部准确的情况"""
        mock_histories = [
            MagicMock(variance_rate=Decimal("5")),
            MagicMock(variance_rate=Decimal("8")),
            MagicMock(variance_rate=Decimal("12")),
        ]
        
        self.mock_db.query.return_value.all.return_value = mock_histories
        
        result = await self.service.get_historical_accuracy()
        
        # 全部偏差<15%，准确率100%
        self.assertEqual(result.accuracy_rate, Decimal("100"))

    # ========== update_actual_cost() 集成测试 (已移除，需要真实数据库连接) ==========
    # 注：完整的集成测试应在集成测试套件中运行，这里专注于单元测试

    async def test_update_actual_cost_not_found(self):
        """测试估算记录不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        input_data = UpdateActualCostInput(
            estimation_id=999,
            actual_cost=Decimal("100000")
        )
        
        with self.assertRaises(ValueError):
            await self.service.update_actual_cost(input_data)


if __name__ == "__main__":
    unittest.main()

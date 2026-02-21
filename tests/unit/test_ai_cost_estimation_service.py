# -*- coding: utf-8 -*-
"""
AI成本估算服务单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
import asyncio
from unittest.mock import MagicMock, Mock, patch
from decimal import Decimal
from datetime import datetime

from app.services.sales.ai_cost_estimation_service import AICostEstimationService
from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    CostOptimizationInput,
    PricingInput,
    UpdateActualCostInput,
    CostBreakdown,
    OptimizationSuggestion,
    PricingRecommendation
)
from app.models.sales.presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory
)


class TestAICostEstimationService(unittest.TestCase):
    """AI成本估算服务测试"""

    def setUp(self):
        """每个测试前的初始化"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        self.user_id = 1
        self.service = AICostEstimationService(db=self.mock_db, user_id=self.user_id)

    # ========== 硬件成本计算测试 ==========

    def test_calculate_hardware_cost_empty(self):
        """测试空硬件清单"""
        result = self.service._calculate_hardware_cost(None)
        self.assertEqual(result, Decimal("0"))

        result = self.service._calculate_hardware_cost([])
        self.assertEqual(result, Decimal("0"))

    def test_calculate_hardware_cost_single_item(self):
        """测试单个硬件项"""
        hardware_items = [
            {"unit_price": 1000, "quantity": 2}
        ]
        result = self.service._calculate_hardware_cost(hardware_items)
        # 1000 * 2 * 1.15 = 2300
        expected = Decimal("2000") * Decimal("1.15")
        self.assertEqual(result, expected)

    def test_calculate_hardware_cost_multiple_items(self):
        """测试多个硬件项"""
        hardware_items = [
            {"unit_price": 1000, "quantity": 2},
            {"unit_price": 500, "quantity": 3},
            {"unit_price": 2000, "quantity": 1}
        ]
        result = self.service._calculate_hardware_cost(hardware_items)
        # (1000*2 + 500*3 + 2000*1) * 1.15 = 5500 * 1.15 = 6325
        total = Decimal("1000") * Decimal("2") + Decimal("500") * Decimal("3") + Decimal("2000") * Decimal("1")
        expected = total * Decimal("1.15")
        self.assertEqual(result, expected)

    def test_calculate_hardware_cost_missing_fields(self):
        """测试缺失字段的硬件项"""
        hardware_items = [
            {"unit_price": 1000},  # 缺quantity，默认为1
            {"quantity": 3}  # 缺unit_price，默认为0
        ]
        result = self.service._calculate_hardware_cost(hardware_items)
        # (1000 * 1 + 0 * 3) * 1.15 = 1150
        expected = Decimal("1000") * Decimal("1.15")
        self.assertEqual(result, expected)

    # ========== 软件成本计算测试 ==========

    def test_calculate_software_cost_with_man_days(self):
        """测试使用明确人天的软件成本"""
        result = self.service._calculate_software_cost("一些需求描述", 10)
        # 10天 * 8小时 * 800元 = 64000
        expected = Decimal("10") * Decimal("8") * Decimal("800")
        self.assertEqual(result, expected)

    def test_calculate_software_cost_no_man_days_short_requirements(self):
        """测试无人天、需求简短"""
        result = self.service._calculate_software_cost("简短需求", None)
        # 字数<100，估算5人天
        expected = Decimal("5") * Decimal("8") * Decimal("800")
        self.assertEqual(result, expected)

    def test_calculate_software_cost_no_man_days_medium_requirements(self):
        """测试无人天、需求中等"""
        requirements = "A" * 200  # 200字符
        result = self.service._calculate_software_cost(requirements, None)
        # 字数100-500，估算15人天
        expected = Decimal("15") * Decimal("8") * Decimal("800")
        self.assertEqual(result, expected)

    def test_calculate_software_cost_no_man_days_long_requirements(self):
        """测试无人天、需求长"""
        requirements = "A" * 600  # 600字符
        result = self.service._calculate_software_cost(requirements, None)
        # 字数>500，估算30人天
        expected = Decimal("30") * Decimal("8") * Decimal("800")
        self.assertEqual(result, expected)

    def test_calculate_software_cost_no_requirements_no_man_days(self):
        """测试无需求无人天"""
        result = self.service._calculate_software_cost(None, None)
        self.assertEqual(result, Decimal("0"))

        result = self.service._calculate_software_cost("", None)
        self.assertEqual(result, Decimal("0"))

    # ========== 安装成本计算测试 ==========

    def test_calculate_installation_cost_low_difficulty(self):
        """测试低难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("low", hardware_cost)
        # 5000 * 1.0 + 10000 * 0.05 = 5500
        expected = Decimal("5000") + hardware_cost * Decimal("0.05")
        self.assertEqual(result, expected)

    def test_calculate_installation_cost_medium_difficulty(self):
        """测试中等难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("medium", hardware_cost)
        # 5000 * 1.5 + 10000 * 0.05 = 8000
        expected = Decimal("5000") * Decimal("1.5") + hardware_cost * Decimal("0.05")
        self.assertEqual(result, expected)

    def test_calculate_installation_cost_high_difficulty(self):
        """测试高难度安装"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost("high", hardware_cost)
        # 5000 * 2.0 + 10000 * 0.05 = 10500
        expected = Decimal("5000") * Decimal("2.0") + hardware_cost * Decimal("0.05")
        self.assertEqual(result, expected)

    def test_calculate_installation_cost_none_difficulty(self):
        """测试无难度参数（默认为low）"""
        hardware_cost = Decimal("10000")
        result = self.service._calculate_installation_cost(None, hardware_cost)
        expected = Decimal("5000") + hardware_cost * Decimal("0.05")
        self.assertEqual(result, expected)

    # ========== 服务成本计算测试 ==========

    def test_calculate_service_cost_one_year(self):
        """测试1年服务成本"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 1)
        # 100000 * 0.10 * 1 = 10000
        expected = base_cost * Decimal("0.10")
        self.assertEqual(result, expected)

    def test_calculate_service_cost_multiple_years(self):
        """测试多年服务成本"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 3)
        # 100000 * 0.10 * 3 = 30000
        expected = base_cost * Decimal("0.10") * Decimal("3")
        self.assertEqual(result, expected)

    # ========== 风险储备金计算测试 ==========

    def test_calculate_risk_reserve_medium_complexity(self):
        """测试中等复杂度风险储备金"""
        # Mock历史偏差率查询
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("IoT", "medium", base_cost)
        # 100000 * 0.08 = 8000
        expected = base_cost * Decimal("0.08")
        self.assertEqual(result, expected)

    def test_calculate_risk_reserve_high_complexity(self):
        """测试高复杂度风险储备金"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("IoT", "high", base_cost)
        # 100000 * 0.08 * 1.5 = 12000
        expected = base_cost * Decimal("0.08") * Decimal("1.5")
        self.assertEqual(result, expected)

    def test_calculate_risk_reserve_low_complexity(self):
        """测试低复杂度风险储备金"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("IoT", "low", base_cost)
        # 100000 * 0.08 * 0.5 = 4000
        expected = base_cost * Decimal("0.08") * Decimal("0.5")
        self.assertEqual(result, expected)

    def test_calculate_risk_reserve_with_historical_variance(self):
        """测试使用历史偏差率"""
        # Mock历史偏差率为10%
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 10.0
        
        base_cost = Decimal("100000")
        result = self.service._calculate_risk_reserve("IoT", "medium", base_cost)
        # 100000 * 0.08 * (1 + 0.1) = 8800
        expected = base_cost * Decimal("0.08") * (Decimal("1") + Decimal("0.1"))
        self.assertEqual(result, expected)

    # ========== 历史偏差率查询测试 ==========

    def test_get_historical_variance_exists(self):
        """测试获取历史偏差率-存在数据"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 15.5
        
        result = self.service._get_historical_variance("IoT")
        self.assertEqual(result, Decimal("0.155"))

    def test_get_historical_variance_not_exists(self):
        """测试获取历史偏差率-无数据"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        result = self.service._get_historical_variance("IoT")
        self.assertIsNone(result)

    # ========== 定价推荐生成测试 ==========

    def test_generate_pricing_recommendations_default_margin(self):
        """测试默认毛利率的定价推荐"""
        total_cost = Decimal("100000")
        target_margin = Decimal("0.30")
        
        result = self.service._generate_pricing_recommendations(total_cost, target_margin)
        
        # suggested_price = 100000 / (1 - 0.30) = 142857.14
        suggested = total_cost / (Decimal("1") - target_margin)
        
        self.assertIsInstance(result, PricingRecommendation)
        self.assertAlmostEqual(float(result.suggested_price), float(suggested), places=2)
        self.assertAlmostEqual(float(result.low), float(suggested * Decimal("0.90")), places=2)
        self.assertAlmostEqual(float(result.medium), float(suggested), places=2)
        self.assertAlmostEqual(float(result.high), float(suggested * Decimal("1.15")), places=2)
        self.assertEqual(result.target_margin_rate, Decimal("30.0"))

    def test_generate_pricing_recommendations_high_margin(self):
        """测试高毛利率的定价推荐"""
        total_cost = Decimal("50000")
        target_margin = Decimal("0.50")  # 50%毛利
        
        result = self.service._generate_pricing_recommendations(total_cost, target_margin)
        
        # suggested_price = 50000 / (1 - 0.50) = 100000
        suggested = Decimal("100000")
        
        self.assertAlmostEqual(float(result.suggested_price), float(suggested), places=2)
        self.assertEqual(result.target_margin_rate, Decimal("50.0"))

    # ========== 置信度计算测试 ==========

    def test_calculate_confidence_score_minimal_data(self):
        """测试最少数据的置信度"""
        # Mock历史数据查询
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
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
            project_type="IoT",
            complexity_level="medium",
            hardware_items=[{"unit_price": 1000, "quantity": 2}]
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 基础分0.5 + 硬件0.2 = 0.7
        self.assertEqual(result, Decimal("0.7"))

    def test_calculate_confidence_score_with_software_requirements(self):
        """测试有软件需求的置信度"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        requirements = "A" * 150  # 超过100字符
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
            complexity_level="medium",
            software_requirements=requirements
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 基础分0.5 + 软件需求0.15 = 0.65
        self.assertEqual(result, Decimal("0.65"))

    def test_calculate_confidence_score_with_man_days(self):
        """测试有人天估算的置信度"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
            complexity_level="medium",
            estimated_man_days=10
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 基础分0.5 + 人天0.1 = 0.6
        self.assertEqual(result, Decimal("0.6"))

    def test_calculate_confidence_score_with_historical_data(self):
        """测试有历史数据的置信度"""
        # Mock历史数据>10条
        self.mock_db.query.return_value.filter.return_value.count.return_value = 15
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
            complexity_level="medium"
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 基础分0.5 + 历史数据0.05 = 0.55
        self.assertEqual(result, Decimal("0.55"))

    def test_calculate_confidence_score_max_score(self):
        """测试最大置信度（不超过1.0）"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 15
        
        requirements = "A" * 150
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
            complexity_level="medium",
            hardware_items=[{"unit_price": 1000, "quantity": 2}],
            software_requirements=requirements,
            estimated_man_days=10
        )
        
        result = self.service._calculate_confidence_score(input_data)
        # 0.5 + 0.2 + 0.15 + 0.1 + 0.05 = 1.0
        self.assertEqual(result, Decimal("1.0"))

    # ========== 优化建议生成测试 ==========

    def test_generate_optimization_suggestions_high_hardware_cost(self):
        """测试高硬件成本的优化建议"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
            complexity_level="medium",
            installation_difficulty="low"
        )
        cost_breakdown = {
            "hardware_cost": Decimal("60000"),
            "software_cost": Decimal("50000"),
            "installation_cost": Decimal("5000"),
            "service_cost": Decimal("10000"),
            "risk_reserve": Decimal("5000")
        }
        
        suggestions = asyncio.run(self.service._generate_optimization_suggestions(input_data, cost_breakdown))
        
        # 应该包含硬件优化建议
        hardware_suggestions = [s for s in suggestions if s.type == "hardware"]
        self.assertGreater(len(hardware_suggestions), 0)
        self.assertEqual(hardware_suggestions[0].saving_rate, Decimal("8.0"))

    def test_generate_optimization_suggestions_high_software_cost(self):
        """测试高软件成本的优化建议"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
            complexity_level="medium",
            installation_difficulty="low"
        )
        cost_breakdown = {
            "hardware_cost": Decimal("40000"),
            "software_cost": Decimal("150000"),
            "installation_cost": Decimal("5000"),
            "service_cost": Decimal("10000"),
            "risk_reserve": Decimal("5000")
        }
        
        suggestions = asyncio.run(self.service._generate_optimization_suggestions(input_data, cost_breakdown))
        
        # 应该包含软件优化建议
        software_suggestions = [s for s in suggestions if s.type == "software"]
        self.assertGreater(len(software_suggestions), 0)
        self.assertEqual(software_suggestions[0].saving_rate, Decimal("15.0"))

    def test_generate_optimization_suggestions_high_installation_difficulty(self):
        """测试高安装难度的优化建议"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
            complexity_level="medium",
            installation_difficulty="high"
        )
        cost_breakdown = {
            "hardware_cost": Decimal("40000"),
            "software_cost": Decimal("50000"),
            "installation_cost": Decimal("15000"),
            "service_cost": Decimal("10000"),
            "risk_reserve": Decimal("5000")
        }
        
        suggestions = asyncio.run(self.service._generate_optimization_suggestions(input_data, cost_breakdown))
        
        # 应该包含安装优化建议
        install_suggestions = [s for s in suggestions if s.type == "installation"]
        self.assertGreater(len(install_suggestions), 0)
        self.assertEqual(install_suggestions[0].saving_rate, Decimal("20.0"))

    def test_generate_optimization_suggestions_multiple(self):
        """测试多个优化建议"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="IoT",
            complexity_level="medium",
            installation_difficulty="high"
        )
        cost_breakdown = {
            "hardware_cost": Decimal("60000"),
            "software_cost": Decimal("150000"),
            "installation_cost": Decimal("15000"),
            "service_cost": Decimal("10000"),
            "risk_reserve": Decimal("5000")
        }
        
        suggestions = asyncio.run(self.service._generate_optimization_suggestions(input_data, cost_breakdown))
        
        # 应该包含3种优化建议
        self.assertEqual(len(suggestions), 3)

    # ========== 风险可接受性判断测试 ==========

    def test_is_acceptable_risk_low_threshold(self):
        """测试低风险接受度"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="测试",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.90")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertTrue(result)  # 0.90 >= 0.85
        
        suggestion.feasibility_score = Decimal("0.80")
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertFalse(result)  # 0.80 < 0.85

    def test_is_acceptable_risk_medium_threshold(self):
        """测试中等风险接受度"""
        suggestion = OptimizationSuggestion(
            type="hardware",
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
        """测试高风险接受度"""
        suggestion = OptimizationSuggestion(
            type="hardware",
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
        """测试无可行性评分的建议"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="测试",
            original_cost=Decimal("1000"),
            optimized_cost=Decimal("900"),
            saving_amount=Decimal("100"),
            saving_rate=Decimal("10"),
            feasibility_score=None
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertTrue(result)  # 无评分时默认接受

    # ========== 平均可行性计算测试 ==========

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
                feasibility_score=Decimal("0.80")
            ),
            OptimizationSuggestion(
                type="software",
                description="测试2",
                original_cost=Decimal("2000"),
                optimized_cost=Decimal("1800"),
                saving_amount=Decimal("200"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.90")
            )
        ]
        
        result = self.service._calculate_avg_feasibility(suggestions)
        # (0.80 + 0.90) / 2 = 0.85
        self.assertEqual(result, Decimal("0.85"))

    # ========== 价格敏感度分析测试 ==========

    def test_analyze_price_sensitivity_without_budget(self):
        """测试无客户预算的敏感度分析"""
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
        
        self.assertEqual(result["cost_base"], 100000.0)
        self.assertIn("price_range", result)
        self.assertIn("margin_analysis", result)
        self.assertNotIn("budget_fit", result)

    def test_analyze_price_sensitivity_with_budget(self):
        """测试有客户预算的敏感度分析"""
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

    # ========== 定价策略测试 ==========

    def test_get_pricing_strategy_high_budget(self):
        """测试高预算定价策略"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        budget = Decimal("170000")
        
        result = self.service._get_pricing_strategy(budget, pricing)
        self.assertIn("高价档", result)

    def test_get_pricing_strategy_medium_budget(self):
        """测试中等预算定价策略"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        budget = Decimal("145000")
        
        result = self.service._get_pricing_strategy(budget, pricing)
        self.assertIn("标准报价", result)

    def test_get_pricing_strategy_low_budget(self):
        """测试低预算定价策略"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        budget = Decimal("125000")
        
        result = self.service._get_pricing_strategy(budget, pricing)
        self.assertIn("低价档", result)

    def test_get_pricing_strategy_very_low_budget(self):
        """测试极低预算定价策略"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        budget = Decimal("110000")
        
        result = self.service._get_pricing_strategy(budget, pricing)
        self.assertIn("低于成本", result)

    # ========== 竞争力评分测试 ==========

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
        self.assertEqual(result, Decimal("0.70"))

    def test_calculate_competitiveness_high_budget(self):
        """测试高预算的竞争力评分"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        budget = Decimal("150000")
        
        result = self.service._calculate_competitiveness(pricing, budget)
        self.assertEqual(result, Decimal("0.90"))

    def test_calculate_competitiveness_medium_budget(self):
        """测试中等预算的竞争力评分"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        budget = Decimal("125000")
        
        result = self.service._calculate_competitiveness(pricing, budget)
        self.assertEqual(result, Decimal("0.75"))

    def test_calculate_competitiveness_low_budget(self):
        """测试低预算的竞争力评分"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30"),
            market_analysis="测试"
        )
        budget = Decimal("110000")
        
        result = self.service._calculate_competitiveness(pricing, budget)
        self.assertEqual(result, Decimal("0.50"))

    # ========== 成本优化测试 ==========

    def test_optimize_cost_estimation_not_found(self):
        """测试估算记录不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        input_data = CostOptimizationInput(estimation_id=999)
        
        with self.assertRaises(ValueError) as ctx:
            asyncio.run(self.service.optimize_cost(input_data))
        
        self.assertIn("估算记录不存在", str(ctx.exception))

    def test_optimize_cost_no_suggestions(self):
        """测试无优化建议"""
        mock_estimation = Mock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        mock_estimation.optimization_suggestions = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        input_data = CostOptimizationInput(estimation_id=1)
        result = asyncio.run(self.service.optimize_cost(input_data))
        
        self.assertEqual(result.original_total_cost, Decimal("100000"))
        self.assertEqual(result.optimized_total_cost, Decimal("100000"))
        self.assertEqual(result.total_saving, Decimal("0"))

    def test_optimize_cost_with_suggestions(self):
        """测试有优化建议"""
        mock_estimation = Mock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        mock_estimation.optimization_suggestions = [
            {
                "type": "hardware",
                "description": "测试优化",
                "original_cost": 60000,
                "optimized_cost": 55200,
                "saving_amount": 4800,
                "saving_rate": 8.0,
                "feasibility_score": 0.85
            }
        ]
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        input_data = CostOptimizationInput(estimation_id=1, max_risk_level="low")
        result = asyncio.run(self.service.optimize_cost(input_data))
        
        self.assertEqual(result.original_total_cost, Decimal("100000"))
        self.assertEqual(result.optimized_total_cost, Decimal("95200"))
        self.assertEqual(result.total_saving, Decimal("4800"))

    # ========== 定价推荐测试 ==========

    def test_recommend_pricing_estimation_not_found(self):
        """测试估算记录不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        input_data = PricingInput(estimation_id=999)
        
        with self.assertRaises(ValueError) as ctx:
            asyncio.run(self.service.recommend_pricing(input_data))
        
        self.assertIn("估算记录不存在", str(ctx.exception))

    def test_recommend_pricing_low_competition(self):
        """测试低竞争环境定价"""
        mock_estimation = Mock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        input_data = PricingInput(
            estimation_id=1,
            target_margin_rate=Decimal("0.30"),
            market_competition_level="low"
        )
        result = asyncio.run(self.service.recommend_pricing(input_data))
        
        # 低竞争时价格上调5%
        base_price = Decimal("100000") / Decimal("0.7")
        expected_medium = base_price * Decimal("1.05")
        
        self.assertAlmostEqual(float(result.pricing_recommendations.medium), float(expected_medium), places=2)
        self.assertEqual(result.cost_base, Decimal("100000"))

    def test_recommend_pricing_high_competition(self):
        """测试高竞争环境定价"""
        mock_estimation = Mock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        input_data = PricingInput(
            estimation_id=1,
            target_margin_rate=Decimal("0.30"),
            market_competition_level="high"
        )
        result = asyncio.run(self.service.recommend_pricing(input_data))
        
        # 高竞争时价格下调5%
        base_price = Decimal("100000") / Decimal("0.7")
        expected_medium = base_price * Decimal("0.95")
        
        self.assertAlmostEqual(float(result.pricing_recommendations.medium), float(expected_medium), places=2)

    # ========== 历史准确度测试 ==========

    def test_get_historical_accuracy_no_data(self):
        """测试无历史数据"""
        self.mock_db.query.return_value.all.return_value = []
        
        result = asyncio.run(self.service.get_historical_accuracy())
        
        self.assertEqual(result.total_predictions, 0)
        self.assertEqual(result.average_variance_rate, Decimal("0"))
        self.assertEqual(result.accuracy_rate, Decimal("0"))
        self.assertEqual(result.recent_trend, "无数据")

    def test_get_historical_accuracy_with_data(self):
        """测试有历史数据"""
        mock_history1 = Mock(spec=PresaleCostHistory)
        mock_history1.variance_rate = Decimal("10.0")
        
        mock_history2 = Mock(spec=PresaleCostHistory)
        mock_history2.variance_rate = Decimal("5.0")
        
        mock_history3 = Mock(spec=PresaleCostHistory)
        mock_history3.variance_rate = Decimal("-8.0")
        
        self.mock_db.query.return_value.all.return_value = [
            mock_history1, mock_history2, mock_history3
        ]
        
        result = asyncio.run(self.service.get_historical_accuracy())
        
        self.assertEqual(result.total_predictions, 3)
        # 平均偏差率 = (10 + 5 - 8) / 3 = 2.33...
        self.assertAlmostEqual(float(result.average_variance_rate), 7.0 / 3, places=2)
        # 准确率 = 3/3 * 100 = 100% (所有偏差<15%)
        self.assertEqual(result.accuracy_rate, Decimal("100"))

    # ========== 更新实际成本测试 ==========

    def test_update_actual_cost_estimation_not_found(self):
        """测试估算记录不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        input_data = UpdateActualCostInput(
            estimation_id=999,
            actual_cost=Decimal("95000")
        )
        
        with self.assertRaises(ValueError) as ctx:
            asyncio.run(self.service.update_actual_cost(input_data))
        
        self.assertIn("估算记录不存在", str(ctx.exception))

    def test_update_actual_cost_success(self):
        """测试成功更新实际成本"""
        mock_estimation = Mock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        mock_estimation.input_parameters = {"project_type": "IoT"}
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        # Mock save_obj的行为（需要设置history.id）
        def mock_save(db, obj):
            obj.id = 123
        
        with patch('app.services.sales.ai_cost_estimation_service.save_obj', side_effect=mock_save):
            input_data = UpdateActualCostInput(
                estimation_id=1,
                project_id=100,
                project_name="测试项目",
                actual_cost=Decimal("95000")
            )
            
            result = asyncio.run(self.service.update_actual_cost(input_data))
        
        self.assertEqual(result["history_id"], 123)
        # 偏差率 = (95000 - 100000) / 100000 * 100 = -5%
        self.assertEqual(result["variance_rate"], Decimal("-5"))
        self.assertTrue(result["learning_applied"])

    def test_update_actual_cost_higher_than_estimated(self):
        """测试实际成本高于估算"""
        mock_estimation = Mock(spec=PresaleAICostEstimation)
        mock_estimation.id = 1
        mock_estimation.total_cost = Decimal("100000")
        mock_estimation.input_parameters = {"project_type": "IoT"}
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_estimation
        
        def mock_save(db, obj):
            obj.id = 124
        
        with patch('app.services.sales.ai_cost_estimation_service.save_obj', side_effect=mock_save):
            input_data = UpdateActualCostInput(
                estimation_id=1,
                project_id=100,
                project_name="测试项目",
                actual_cost=Decimal("110000")
            )
            
            result = asyncio.run(self.service.update_actual_cost(input_data))
        
        # 偏差率 = (110000 - 100000) / 100000 * 100 = 10%
        self.assertEqual(result["variance_rate"], Decimal("10"))

    # ========== 完整流程集成测试 ==========

    def test_estimate_cost_full_workflow(self):
        """测试完整成本估算流程"""
        # Mock历史数据查询
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        # Mock save_obj
        def mock_save(db, obj):
            obj.id = 1
            obj.created_at = datetime.now()
        
        with patch('app.services.sales.ai_cost_estimation_service.save_obj', side_effect=mock_save):
            input_data = CostEstimationInput(
                presale_ticket_id=1,
                solution_id=1,
                project_type="IoT",
                complexity_level="medium",
                hardware_items=[
                    {"unit_price": 1000, "quantity": 10}
                ],
                software_requirements="开发智能监控系统，需要实现数据采集、分析和可视化功能",
                estimated_man_days=20,
                installation_difficulty="medium",
                service_years=2,
                target_margin_rate=Decimal("0.30")
            )
            
            result = asyncio.run(self.service.estimate_cost(input_data))
        
        # 验证结果
        self.assertIsNotNone(result.id)
        self.assertEqual(result.presale_ticket_id, 1)
        self.assertGreater(result.cost_breakdown.total_cost, Decimal("0"))
        self.assertIsNotNone(result.pricing_recommendations)
        self.assertGreater(result.confidence_score, Decimal("0"))


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)

"""
AI Cost Estimation Service 增强单元测试
覆盖率目标: 70%+
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any

from app.services.sales.ai_cost_estimation_service import AICostEstimationService
from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    CostEstimationResponse,
    CostOptimizationInput,
    CostOptimizationResponse,
    PricingInput,
    PricingResponse,
    OptimizationSuggestion,
    PricingRecommendation,
    CostBreakdown,
    UpdateActualCostInput,
    HistoricalAccuracyResponse
)
from app.models.sales.presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory,
    PresaleCostOptimizationRecord
)


class TestAICostEstimationService(unittest.TestCase):
    """AI成本估算服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.user_id = 1
        self.service = AICostEstimationService(db=self.db, user_id=self.user_id)
    
    def tearDown(self):
        """测试后清理"""
        self.db.reset_mock()
    
    # ==================== 硬件成本计算测试 ====================
    
    def test_calculate_hardware_cost_with_items(self):
        """测试硬件成本计算 - 正常情况"""
        hardware_items = [
            {"unit_price": 1000, "quantity": 2},
            {"unit_price": 500, "quantity": 3}
        ]
        
        result = self.service._calculate_hardware_cost(hardware_items)
        
        # (1000*2 + 500*3) * 1.15 = 3500 * 1.15 = 4025
        expected = Decimal("4025.00")
        self.assertEqual(result, expected)
    
    def test_calculate_hardware_cost_empty_list(self):
        """测试硬件成本计算 - 空列表"""
        result = self.service._calculate_hardware_cost([])
        self.assertEqual(result, Decimal("0"))
    
    def test_calculate_hardware_cost_none(self):
        """测试硬件成本计算 - None输入"""
        result = self.service._calculate_hardware_cost(None)
        self.assertEqual(result, Decimal("0"))
    
    def test_calculate_hardware_cost_decimal_precision(self):
        """测试硬件成本计算 - Decimal精度"""
        hardware_items = [
            {"unit_price": 999.99, "quantity": 1}
        ]
        
        result = self.service._calculate_hardware_cost(hardware_items)
        
        # 999.99 * 1.15 = 1149.9885
        expected = Decimal("999.99") * Decimal("1.15")
        self.assertEqual(result, expected)
    
    # ==================== 软件成本计算测试 ====================
    
    def test_calculate_software_cost_with_man_days(self):
        """测试软件成本计算 - 提供人天数"""
        result = self.service._calculate_software_cost("需求描述", 10)
        
        # 10 * 8 * 800 = 64000
        expected = Decimal("64000")
        self.assertEqual(result, expected)
    
    def test_calculate_software_cost_estimate_low(self):
        """测试软件成本计算 - 自动估算人天(少量需求)"""
        requirements = "简单需求"  # < 100字符
        result = self.service._calculate_software_cost(requirements, None)
        
        # 自动估算5人天: 5 * 8 * 800 = 32000
        expected = Decimal("32000")
        self.assertEqual(result, expected)
    
    def test_calculate_software_cost_estimate_medium(self):
        """测试软件成本计算 - 自动估算人天(中等需求)"""
        requirements = "需求" * 60  # 120字符, 100-500之间
        result = self.service._calculate_software_cost(requirements, None)
        
        # 自动估算15人天: 15 * 8 * 800 = 96000
        expected = Decimal("96000")
        self.assertEqual(result, expected)
    
    def test_calculate_software_cost_estimate_high(self):
        """测试软件成本计算 - 自动估算人天(大量需求)"""
        requirements = "需求" * 300  # 600字符, > 500
        result = self.service._calculate_software_cost(requirements, None)
        
        # 自动估算30人天: 30 * 8 * 800 = 192000
        expected = Decimal("192000")
        self.assertEqual(result, expected)
    
    def test_calculate_software_cost_no_requirements(self):
        """测试软件成本计算 - 无需求描述"""
        result = self.service._calculate_software_cost(None, None)
        self.assertEqual(result, Decimal("0"))
    
    # ==================== 安装成本计算测试 ====================
    
    def test_calculate_installation_cost_high_difficulty(self):
        """测试安装成本计算 - 高难度"""
        hardware_cost = Decimal("100000")
        result = self.service._calculate_installation_cost("high", hardware_cost)
        
        # 5000 * 2.0 + 100000 * 0.05 = 10000 + 5000 = 15000
        expected = Decimal("15000")
        self.assertEqual(result, expected)
    
    def test_calculate_installation_cost_medium_difficulty(self):
        """测试安装成本计算 - 中等难度"""
        hardware_cost = Decimal("100000")
        result = self.service._calculate_installation_cost("medium", hardware_cost)
        
        # 5000 * 1.5 + 100000 * 0.05 = 7500 + 5000 = 12500
        expected = Decimal("12500")
        self.assertEqual(result, expected)
    
    def test_calculate_installation_cost_low_difficulty(self):
        """测试安装成本计算 - 低难度"""
        hardware_cost = Decimal("100000")
        result = self.service._calculate_installation_cost("low", hardware_cost)
        
        # 5000 * 1.0 + 100000 * 0.05 = 5000 + 5000 = 10000
        expected = Decimal("10000")
        self.assertEqual(result, expected)
    
    def test_calculate_installation_cost_none_difficulty(self):
        """测试安装成本计算 - 未指定难度"""
        hardware_cost = Decimal("100000")
        result = self.service._calculate_installation_cost(None, hardware_cost)
        
        # 默认为低难度
        expected = Decimal("10000")
        self.assertEqual(result, expected)
    
    # ==================== 服务成本计算测试 ====================
    
    def test_calculate_service_cost_one_year(self):
        """测试服务成本计算 - 1年"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 1)
        
        # 100000 * 0.10 * 1 = 10000
        expected = Decimal("10000")
        self.assertEqual(result, expected)
    
    def test_calculate_service_cost_multiple_years(self):
        """测试服务成本计算 - 多年"""
        base_cost = Decimal("100000")
        result = self.service._calculate_service_cost(base_cost, 3)
        
        # 100000 * 0.10 * 3 = 30000
        expected = Decimal("30000")
        self.assertEqual(result, expected)
    
    # ==================== 风险储备金计算测试 ====================
    
    def test_calculate_risk_reserve_high_complexity(self):
        """测试风险储备金计算 - 高复杂度"""
        with patch.object(self.service, '_get_historical_variance', return_value=None):
            base_cost = Decimal("100000")
            result = self.service._calculate_risk_reserve("project_a", "high", base_cost)
            
            # 100000 * 0.08 * 1.5 = 12000
            expected = Decimal("12000")
            self.assertEqual(result, expected)
    
    def test_calculate_risk_reserve_low_complexity(self):
        """测试风险储备金计算 - 低复杂度"""
        with patch.object(self.service, '_get_historical_variance', return_value=None):
            base_cost = Decimal("100000")
            result = self.service._calculate_risk_reserve("project_a", "low", base_cost)
            
            # 100000 * 0.08 * 0.5 = 4000
            expected = Decimal("4000")
            self.assertEqual(result, expected)
    
    def test_calculate_risk_reserve_with_historical_variance(self):
        """测试风险储备金计算 - 有历史偏差数据"""
        with patch.object(self.service, '_get_historical_variance', return_value=Decimal("0.1")):
            base_cost = Decimal("100000")
            result = self.service._calculate_risk_reserve("project_a", "medium", base_cost)
            
            # 100000 * 0.08 * (1 + 0.1) = 8800
            expected = Decimal("8800")
            self.assertEqual(result, expected)
    
    # ==================== 历史偏差获取测试 ====================
    
    def test_get_historical_variance_with_data(self):
        """测试获取历史偏差 - 有数据"""
        # Mock数据库查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 15.5
        
        result = self.service._get_historical_variance("project_type_a")
        
        expected = Decimal("0.155")  # 15.5 / 100
        self.assertEqual(result, expected)
    
    def test_get_historical_variance_no_data(self):
        """测试获取历史偏差 - 无数据"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        result = self.service._get_historical_variance("project_type_b")
        
        self.assertIsNone(result)
    
    # ==================== 置信度评分测试 ====================
    
    def test_calculate_confidence_score_full_info(self):
        """测试置信度评分 - 完整信息"""
        # Mock数据库查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 15
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="project_a",
            complexity_level="medium",
            hardware_items=[{"unit_price": 1000, "quantity": 1}],
            software_requirements="需求" * 60,
            estimated_man_days=10
        )
        
        result = self.service._calculate_confidence_score(input_data)
        
        # 0.5 + 0.2 + 0.15 + 0.1 + 0.05 = 1.0
        expected = Decimal("1.0")
        self.assertEqual(result, expected)
    
    def test_calculate_confidence_score_minimal_info(self):
        """测试置信度评分 - 最少信息"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="project_a",
            complexity_level="medium"
        )
        
        result = self.service._calculate_confidence_score(input_data)
        
        # 只有基础分 0.5
        expected = Decimal("0.5")
        self.assertEqual(result, expected)
    
    # ==================== 定价推荐生成测试 ====================
    
    def test_generate_pricing_recommendations(self):
        """测试生成定价推荐"""
        total_cost = Decimal("100000")
        target_margin_rate = Decimal("0.30")
        
        result = self.service._generate_pricing_recommendations(total_cost, target_margin_rate)
        
        # suggested_price = 100000 / (1 - 0.30) = 142857.14...
        suggested_price = total_cost / (Decimal("1") - target_margin_rate)
        
        self.assertIsInstance(result, PricingRecommendation)
        self.assertEqual(result.suggested_price, suggested_price)
        self.assertEqual(result.low, suggested_price * Decimal("0.90"))
        self.assertEqual(result.medium, suggested_price)
        self.assertEqual(result.high, suggested_price * Decimal("1.15"))
        self.assertEqual(result.target_margin_rate, Decimal("30"))
    
    # ==================== 风险接受度判断测试 ====================
    
    def test_is_acceptable_risk_low_threshold(self):
        """测试风险接受度判断 - 低风险阈值"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="建议",
            original_cost=Decimal("100"),
            optimized_cost=Decimal("90"),
            saving_amount=Decimal("10"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.90")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertTrue(result)
    
    def test_is_acceptable_risk_too_risky(self):
        """测试风险接受度判断 - 风险过高"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="建议",
            original_cost=Decimal("100"),
            optimized_cost=Decimal("90"),
            saving_amount=Decimal("10"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.60")
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertFalse(result)
    
    def test_is_acceptable_risk_no_score(self):
        """测试风险接受度判断 - 无评分"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="建议",
            original_cost=Decimal("100"),
            optimized_cost=Decimal("90"),
            saving_amount=Decimal("10"),
            saving_rate=Decimal("10"),
            feasibility_score=None
        )
        
        result = self.service._is_acceptable_risk(suggestion, "low")
        self.assertTrue(result)  # 无评分则默认接受
    
    # ==================== 平均可行性计算测试 ====================
    
    def test_calculate_avg_feasibility_with_suggestions(self):
        """测试平均可行性计算 - 有建议"""
        suggestions = [
            OptimizationSuggestion(
                type="hardware",
                description="建议1",
                original_cost=Decimal("100"),
                optimized_cost=Decimal("90"),
                saving_amount=Decimal("10"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.8")
            ),
            OptimizationSuggestion(
                type="software",
                description="建议2",
                original_cost=Decimal("200"),
                optimized_cost=Decimal("180"),
                saving_amount=Decimal("20"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.6")
            )
        ]
        
        result = self.service._calculate_avg_feasibility(suggestions)
        
        # (0.8 + 0.6) / 2 = 0.7
        expected = Decimal("0.7")
        self.assertEqual(result, expected)
    
    def test_calculate_avg_feasibility_empty(self):
        """测试平均可行性计算 - 空列表"""
        result = self.service._calculate_avg_feasibility([])
        self.assertEqual(result, Decimal("0"))
    
    # ==================== 价格敏感度分析测试 ====================
    
    def test_analyze_price_sensitivity_with_budget(self):
        """测试价格敏感度分析 - 有预算"""
        cost = Decimal("100000")
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        customer_budget = Decimal("150000")
        
        result = self.service._analyze_price_sensitivity(cost, pricing, customer_budget)
        
        self.assertIn("cost_base", result)
        self.assertIn("price_range", result)
        self.assertIn("margin_analysis", result)
        self.assertIn("budget_fit", result)
        self.assertEqual(result["budget_fit"]["customer_budget"], float(customer_budget))
        self.assertTrue(result["budget_fit"]["fits_recommended"])
    
    def test_analyze_price_sensitivity_no_budget(self):
        """测试价格敏感度分析 - 无预算"""
        cost = Decimal("100000")
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        
        result = self.service._analyze_price_sensitivity(cost, pricing, None)
        
        self.assertIn("cost_base", result)
        self.assertIn("price_range", result)
        self.assertIn("margin_analysis", result)
        self.assertNotIn("budget_fit", result)
    
    # ==================== 定价策略获取测试 ====================
    
    def test_get_pricing_strategy_high_budget(self):
        """测试定价策略 - 高预算"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        budget = Decimal("170000")
        
        result = self.service._get_pricing_strategy(budget, pricing)
        
        self.assertIn("高价档", result)
    
    def test_get_pricing_strategy_medium_budget(self):
        """测试定价策略 - 中等预算"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        budget = Decimal("145000")
        
        result = self.service._get_pricing_strategy(budget, pricing)
        
        self.assertIn("标准报价", result)
    
    def test_get_pricing_strategy_low_budget(self):
        """测试定价策略 - 低预算"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        budget = Decimal("125000")
        
        result = self.service._get_pricing_strategy(budget, pricing)
        
        self.assertIn("低价档", result)
    
    def test_get_pricing_strategy_insufficient_budget(self):
        """测试定价策略 - 预算不足"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        budget = Decimal("100000")
        
        result = self.service._get_pricing_strategy(budget, pricing)
        
        self.assertIn("低于成本", result)
    
    # ==================== 竞争力评分测试 ====================
    
    def test_calculate_competitiveness_high(self):
        """测试竞争力评分 - 高竞争力"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        customer_budget = Decimal("150000")
        
        result = self.service._calculate_competitiveness(pricing, customer_budget)
        
        self.assertEqual(result, Decimal("0.90"))
    
    def test_calculate_competitiveness_medium(self):
        """测试竞争力评分 - 中等竞争力"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        customer_budget = Decimal("130000")
        
        result = self.service._calculate_competitiveness(pricing, customer_budget)
        
        self.assertEqual(result, Decimal("0.75"))
    
    def test_calculate_competitiveness_low(self):
        """测试竞争力评分 - 低竞争力"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        customer_budget = Decimal("100000")
        
        result = self.service._calculate_competitiveness(pricing, customer_budget)
        
        self.assertEqual(result, Decimal("0.50"))
    
    def test_calculate_competitiveness_no_budget(self):
        """测试竞争力评分 - 无预算"""
        pricing = PricingRecommendation(
            low=Decimal("120000"),
            medium=Decimal("140000"),
            high=Decimal("160000"),
            suggested_price=Decimal("140000"),
            target_margin_rate=Decimal("30")
        )
        
        result = self.service._calculate_competitiveness(pricing, None)
        
        self.assertEqual(result, Decimal("0.70"))
    
    # ==================== 成本估算集成测试 ====================
    
    @patch('app.utils.db_helpers.save_obj')
    async def test_estimate_cost_success(self, mock_save_obj):
        """测试成本估算 - 成功场景"""
        # Mock数据库查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.scalar.return_value = None
        
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            solution_id=1,
            project_type="project_a",
            complexity_level="medium",
            hardware_items=[{"unit_price": 1000, "quantity": 2}],
            software_requirements="需求描述" * 30,
            estimated_man_days=10,
            installation_difficulty="medium",
            service_years=2,
            target_margin_rate=Decimal("0.30")
        )
        
        # Mock保存对象，设置ID
        def set_id(db, obj):
            obj.id = 1
            obj.created_at = datetime.now()
        
        mock_save_obj.side_effect = set_id
        
        result = await self.service.estimate_cost(input_data)
        
        self.assertIsInstance(result, CostEstimationResponse)
        self.assertEqual(result.presale_ticket_id, 1)
        self.assertIsNotNone(result.cost_breakdown)
        self.assertIsNotNone(result.pricing_recommendations)
        self.assertGreater(result.confidence_score, Decimal("0"))
    
    # ==================== 成本优化测试 ====================
    
    async def test_optimize_cost_success(self):
        """测试成本优化 - 成功场景"""
        # 创建Mock的估算对象
        mock_estimation = PresaleAICostEstimation(
            id=1,
            presale_ticket_id=1,
            total_cost=Decimal("100000"),
            optimization_suggestions=[
                {
                    "type": "hardware",
                    "description": "硬件优化",
                    "original_cost": "50000",
                    "optimized_cost": "45000",
                    "saving_amount": "5000",
                    "saving_rate": "10.0",
                    "feasibility_score": "0.85"
                }
            ]
        )
        
        # Mock数据库查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_estimation
        
        input_data = CostOptimizationInput(
            estimation_id=1,
            max_risk_level="medium"
        )
        
        result = await self.service.optimize_cost(input_data)
        
        self.assertIsInstance(result, CostOptimizationResponse)
        self.assertEqual(result.original_total_cost, Decimal("100000"))
        self.assertGreater(len(result.suggestions), 0)
    
    async def test_optimize_cost_not_found(self):
        """测试成本优化 - 记录不存在"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        input_data = CostOptimizationInput(
            estimation_id=999,
            max_risk_level="medium"
        )
        
        with self.assertRaises(ValueError) as context:
            await self.service.optimize_cost(input_data)
        
        self.assertIn("估算记录不存在", str(context.exception))
    
    # ==================== 定价推荐测试 ====================
    
    async def test_recommend_pricing_success(self):
        """测试定价推荐 - 成功场景"""
        mock_estimation = PresaleAICostEstimation(
            id=1,
            presale_ticket_id=1,
            total_cost=Decimal("100000")
        )
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_estimation
        
        input_data = PricingInput(
            estimation_id=1,
            target_margin_rate=Decimal("0.30"),
            market_competition_level="medium",
            customer_budget=Decimal("150000")
        )
        
        result = await self.service.recommend_pricing(input_data)
        
        self.assertIsInstance(result, PricingResponse)
        self.assertEqual(result.cost_base, Decimal("100000"))
        self.assertIsNotNone(result.pricing_recommendations)
        self.assertIsNotNone(result.sensitivity_analysis)
    
    async def test_recommend_pricing_high_competition(self):
        """测试定价推荐 - 高竞争市场"""
        mock_estimation = PresaleAICostEstimation(
            id=1,
            presale_ticket_id=1,
            total_cost=Decimal("100000")
        )
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_estimation
        
        input_data = PricingInput(
            estimation_id=1,
            target_margin_rate=Decimal("0.30"),
            market_competition_level="high",
            customer_budget=Decimal("150000")
        )
        
        result = await self.service.recommend_pricing(input_data)
        
        # 高竞争应该降低价格 (0.95倍)
        base_price = Decimal("100000") / (Decimal("1") - Decimal("0.30"))
        expected_medium = base_price * Decimal("0.95")
        
        self.assertLess(
            result.pricing_recommendations.medium,
            base_price
        )
    
    # ==================== 历史准确度测试 ====================
    
    async def test_get_historical_accuracy_with_data(self):
        """测试获取历史准确度 - 有数据"""
        mock_histories = [
            MagicMock(variance_rate=Decimal("10.0")),
            MagicMock(variance_rate=Decimal("20.0")),
            MagicMock(variance_rate=Decimal("5.0")),
            MagicMock(variance_rate=Decimal("-8.0"))
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.all.return_value = mock_histories
        
        result = await self.service.get_historical_accuracy()
        
        self.assertIsInstance(result, HistoricalAccuracyResponse)
        self.assertEqual(result.total_predictions, 4)
        # 平均偏差: (10 + 20 + 5 + 8) / 4 = 10.75
        self.assertAlmostEqual(float(result.average_variance_rate), 6.75, places=2)
        # 准确率: 3个<15% / 4 = 75%
        self.assertEqual(result.accuracy_rate, Decimal("75"))
    
    async def test_get_historical_accuracy_no_data(self):
        """测试获取历史准确度 - 无数据"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.all.return_value = []
        
        result = await self.service.get_historical_accuracy()
        
        self.assertIsInstance(result, HistoricalAccuracyResponse)
        self.assertEqual(result.total_predictions, 0)
        self.assertEqual(result.average_variance_rate, Decimal("0"))
        self.assertEqual(result.accuracy_rate, Decimal("0"))
        self.assertEqual(result.recent_trend, "无数据")
    
    # ==================== 更新实际成本测试 ====================
    
    @patch('app.utils.db_helpers.save_obj')
    async def test_update_actual_cost_success(self, mock_save_obj):
        """测试更新实际成本 - 成功场景"""
        mock_estimation = PresaleAICostEstimation(
            id=1,
            presale_ticket_id=1,
            total_cost=Decimal("100000"),
            input_parameters={"project_type": "project_a"}
        )
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_estimation
        
        def set_id(db, obj):
            obj.id = 1
        
        mock_save_obj.side_effect = set_id
        
        input_data = UpdateActualCostInput(
            estimation_id=1,
            project_id=1,
            project_name="测试项目",
            actual_cost=Decimal("110000")
        )
        
        result = await self.service.update_actual_cost(input_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn("history_id", result)
        self.assertIn("variance_rate", result)
        # 偏差率: (110000 - 100000) / 100000 * 100 = 10%
        self.assertEqual(result["variance_rate"], Decimal("10"))
        self.assertTrue(result["learning_applied"])
    
    async def test_update_actual_cost_negative_variance(self):
        """测试更新实际成本 - 负偏差"""
        mock_estimation = PresaleAICostEstimation(
            id=1,
            presale_ticket_id=1,
            total_cost=Decimal("100000"),
            input_parameters={"project_type": "project_a"}
        )
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_estimation
        
        with patch('app.utils.db_helpers.save_obj') as mock_save_obj:
            def set_id(db, obj):
                obj.id = 1
            
            mock_save_obj.side_effect = set_id
            
            input_data = UpdateActualCostInput(
                estimation_id=1,
                project_id=1,
                project_name="测试项目",
                actual_cost=Decimal("90000")
            )
            
            result = await self.service.update_actual_cost(input_data)
            
            # 偏差率: (90000 - 100000) / 100000 * 100 = -10%
            self.assertEqual(result["variance_rate"], Decimal("-10"))
    
    # ==================== 优化建议生成测试 ====================
    
    async def test_generate_optimization_suggestions_hardware(self):
        """测试生成优化建议 - 硬件优化"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="project_a",
            complexity_level="medium"
        )
        
        cost_breakdown = {
            "hardware_cost": Decimal("60000"),
            "software_cost": Decimal("50000"),
            "installation_cost": Decimal("10000"),
            "service_cost": Decimal("5000"),
            "risk_reserve": Decimal("8000")
        }
        
        suggestions = await self.service._generate_optimization_suggestions(input_data, cost_breakdown)
        
        self.assertIsInstance(suggestions, list)
        # 硬件成本>50000应该有硬件优化建议
        hardware_suggestions = [s for s in suggestions if s.type == "hardware"]
        self.assertGreater(len(hardware_suggestions), 0)
    
    async def test_generate_optimization_suggestions_software(self):
        """测试生成优化建议 - 软件优化"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="project_a",
            complexity_level="medium"
        )
        
        cost_breakdown = {
            "hardware_cost": Decimal("30000"),
            "software_cost": Decimal("120000"),
            "installation_cost": Decimal("10000"),
            "service_cost": Decimal("5000"),
            "risk_reserve": Decimal("8000")
        }
        
        suggestions = await self.service._generate_optimization_suggestions(input_data, cost_breakdown)
        
        # 软件成本>100000应该有软件优化建议
        software_suggestions = [s for s in suggestions if s.type == "software"]
        self.assertGreater(len(software_suggestions), 0)
    
    async def test_generate_optimization_suggestions_installation(self):
        """测试生成优化建议 - 安装优化"""
        input_data = CostEstimationInput(
            presale_ticket_id=1,
            project_type="project_a",
            complexity_level="medium",
            installation_difficulty="high"
        )
        
        cost_breakdown = {
            "hardware_cost": Decimal("30000"),
            "software_cost": Decimal("50000"),
            "installation_cost": Decimal("15000"),
            "service_cost": Decimal("5000"),
            "risk_reserve": Decimal("8000")
        }
        
        suggestions = await self.service._generate_optimization_suggestions(input_data, cost_breakdown)
        
        # 高难度安装应该有安装优化建议
        installation_suggestions = [s for s in suggestions if s.type == "installation"]
        self.assertGreater(len(installation_suggestions), 0)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)

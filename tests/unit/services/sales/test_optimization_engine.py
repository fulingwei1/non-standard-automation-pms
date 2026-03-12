# -*- coding: utf-8 -*-
"""
成本优化引擎测试
"""

from decimal import Decimal

import pytest

from app.schemas.sales.presale_ai_cost import OptimizationSuggestion
from app.services.sales.cost.optimization_engine import OptimizationEngine


class TestOptimizationEngine:
    """OptimizationEngine 测试"""

    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        return OptimizationEngine()

    # ========== 风险可接受性测试 ==========
    def test_is_acceptable_risk_high_feasibility(self, engine):
        """高可行性建议在低风险下可接受"""
        suggestion = OptimizationSuggestion(
            type="hardware",
            description="测试建议",
            original_cost=Decimal("10000"),
            optimized_cost=Decimal("9000"),
            saving_amount=Decimal("1000"),
            saving_rate=Decimal("10"),
            feasibility_score=Decimal("0.90"),
            alternative_solutions=[],
        )
        assert engine.is_acceptable_risk(suggestion, "low") is True

    def test_is_acceptable_risk_medium_feasibility(self, engine):
        """中等可行性建议在中等风险下可接受"""
        suggestion = OptimizationSuggestion(
            type="software",
            description="测试建议",
            original_cost=Decimal("10000"),
            optimized_cost=Decimal("8500"),
            saving_amount=Decimal("1500"),
            saving_rate=Decimal("15"),
            feasibility_score=Decimal("0.75"),
            alternative_solutions=[],
        )
        assert engine.is_acceptable_risk(suggestion, "medium") is True
        assert engine.is_acceptable_risk(suggestion, "low") is False

    def test_is_acceptable_risk_low_feasibility(self, engine):
        """低可行性建议仅在高风险下可接受"""
        suggestion = OptimizationSuggestion(
            type="installation",
            description="测试建议",
            original_cost=Decimal("10000"),
            optimized_cost=Decimal("6000"),
            saving_amount=Decimal("4000"),
            saving_rate=Decimal("40"),
            feasibility_score=Decimal("0.55"),
            alternative_solutions=[],
        )
        assert engine.is_acceptable_risk(suggestion, "high") is True
        assert engine.is_acceptable_risk(suggestion, "medium") is False
        assert engine.is_acceptable_risk(suggestion, "low") is False

    def test_is_acceptable_risk_no_feasibility(self, engine):
        """无可行性评分时默认可接受"""
        suggestion = OptimizationSuggestion(
            type="other",
            description="测试建议",
            original_cost=Decimal("10000"),
            optimized_cost=Decimal("9000"),
            saving_amount=Decimal("1000"),
            saving_rate=Decimal("10"),
            feasibility_score=None,
            alternative_solutions=[],
        )
        assert engine.is_acceptable_risk(suggestion, "low") is True

    # ========== 平均可行性测试 ==========
    def test_calculate_avg_feasibility_empty(self, engine):
        """空列表返回0"""
        assert engine.calculate_avg_feasibility([]) == Decimal("0")

    def test_calculate_avg_feasibility_single(self, engine):
        """单个建议"""
        suggestions = [
            OptimizationSuggestion(
                type="hardware",
                description="测试",
                original_cost=Decimal("10000"),
                optimized_cost=Decimal("9000"),
                saving_amount=Decimal("1000"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.80"),
                alternative_solutions=[],
            )
        ]
        assert engine.calculate_avg_feasibility(suggestions) == Decimal("0.80")

    def test_calculate_avg_feasibility_multiple(self, engine):
        """多个建议取平均"""
        suggestions = [
            OptimizationSuggestion(
                type="hardware",
                description="测试1",
                original_cost=Decimal("10000"),
                optimized_cost=Decimal("9000"),
                saving_amount=Decimal("1000"),
                saving_rate=Decimal("10"),
                feasibility_score=Decimal("0.80"),
                alternative_solutions=[],
            ),
            OptimizationSuggestion(
                type="software",
                description="测试2",
                original_cost=Decimal("20000"),
                optimized_cost=Decimal("17000"),
                saving_amount=Decimal("3000"),
                saving_rate=Decimal("15"),
                feasibility_score=Decimal("0.60"),
                alternative_solutions=[],
            ),
        ]
        # (0.80 + 0.60) / 2 = 0.70
        assert engine.calculate_avg_feasibility(suggestions) == Decimal("0.70")

    def test_calculate_avg_feasibility_with_none(self, engine):
        """包含 None 的建议按 0 计算"""
        suggestions = [
            OptimizationSuggestion(
                type="hardware",
                description="测试",
                original_cost=Decimal("10000"),
                optimized_cost=Decimal("9000"),
                saving_amount=Decimal("1000"),
                saving_rate=Decimal("10"),
                feasibility_score=None,
                alternative_solutions=[],
            ),
            OptimizationSuggestion(
                type="software",
                description="测试",
                original_cost=Decimal("10000"),
                optimized_cost=Decimal("8500"),
                saving_amount=Decimal("1500"),
                saving_rate=Decimal("15"),
                feasibility_score=Decimal("0.80"),
                alternative_solutions=[],
            ),
        ]
        # (0 + 0.80) / 2 = 0.40
        assert engine.calculate_avg_feasibility(suggestions) == Decimal("0.40")

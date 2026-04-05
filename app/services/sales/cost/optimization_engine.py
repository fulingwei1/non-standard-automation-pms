# -*- coding: utf-8 -*-
"""
成本优化建议引擎

分析成本结构，生成优化建议。
"""

from decimal import Decimal
from typing import Dict, List

from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    OptimizationSuggestion,
)
from app.utils.decimal_helpers import parse_decimal


class OptimizationEngine:
    """成本优化建议引擎"""

    # 成本阈值
    HARDWARE_OPTIMIZATION_THRESHOLD = Decimal("50000")
    SOFTWARE_OPTIMIZATION_THRESHOLD = Decimal("100000")

    async def generate_suggestions(
        self,
        input_data: CostEstimationInput,
        cost_breakdown: Dict[str, Decimal]
    ) -> List[OptimizationSuggestion]:
        """
        生成成本优化建议

        Args:
            input_data: 估算输入数据
            cost_breakdown: 成本明细

        Returns:
            优化建议列表
        """
        suggestions = []

        # 1. 硬件优化
        if cost_breakdown["hardware_cost"] > self.HARDWARE_OPTIMIZATION_THRESHOLD:
            suggestions.append(
                OptimizationSuggestion(
                    type="hardware",
                    description="建议与供应商协商批量采购折扣",
                    original_cost=cost_breakdown["hardware_cost"],
                    optimized_cost=cost_breakdown["hardware_cost"] * Decimal("0.92"),
                    saving_amount=cost_breakdown["hardware_cost"] * Decimal("0.08"),
                    saving_rate=Decimal("8.0"),
                    feasibility_score=Decimal("0.85"),
                    alternative_solutions=[
                        "更换为性价比更高的同类产品",
                        "采用分期采购降低单次成本",
                    ],
                )
            )

        # 2. 软件优化
        if cost_breakdown["software_cost"] > self.SOFTWARE_OPTIMIZATION_THRESHOLD:
            suggestions.append(
                OptimizationSuggestion(
                    type="software",
                    description="考虑使用现有代码库模块,减少开发工时",
                    original_cost=cost_breakdown["software_cost"],
                    optimized_cost=cost_breakdown["software_cost"] * Decimal("0.85"),
                    saving_amount=cost_breakdown["software_cost"] * Decimal("0.15"),
                    saving_rate=Decimal("15.0"),
                    feasibility_score=Decimal("0.75"),
                    alternative_solutions=["采用低代码平台", "外包部分非核心功能"],
                )
            )

        # 3. 安装优化
        if input_data.installation_difficulty == "high":
            suggestions.append(
                OptimizationSuggestion(
                    type="installation",
                    description="提前进行现场勘查和方案优化,降低安装难度",
                    original_cost=cost_breakdown["installation_cost"],
                    optimized_cost=cost_breakdown["installation_cost"] * Decimal("0.80"),
                    saving_amount=cost_breakdown["installation_cost"] * Decimal("0.20"),
                    saving_rate=Decimal("20.0"),
                    feasibility_score=Decimal("0.90"),
                    alternative_solutions=["采用模块化设计", "提供远程技术支持"],
                )
            )

        return suggestions

    def is_acceptable_risk(
        self,
        suggestion: OptimizationSuggestion,
        max_risk_level: str
    ) -> bool:
        """
        判断风险是否可接受

        Args:
            suggestion: 优化建议
            max_risk_level: 最大风险等级

        Returns:
            是否可接受
        """
        if not suggestion.feasibility_score:
            return True

        risk_thresholds = {
            "low": Decimal("0.85"),
            "medium": Decimal("0.70"),
            "high": Decimal("0.50"),
        }

        threshold = risk_thresholds.get(max_risk_level, Decimal("0.70"))
        return suggestion.feasibility_score >= threshold

    def calculate_avg_feasibility(
        self,
        suggestions: List[OptimizationSuggestion]
    ) -> Decimal:
        """计算平均可行性"""
        if not suggestions:
            return Decimal("0")

        total = sum(s.feasibility_score or Decimal("0") for s in suggestions)
        return total / parse_decimal(len(suggestions))

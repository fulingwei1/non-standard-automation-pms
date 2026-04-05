# -*- coding: utf-8 -*-
"""
定价推荐引擎

基于成本和市场分析，生成定价建议。
"""

from decimal import Decimal
from typing import Any, Dict, Optional

from app.schemas.sales.presale_ai_cost import PricingRecommendation


class PricingEngine:
    """定价推荐引擎"""

    def generate_recommendations(
        self,
        total_cost: Decimal,
        target_margin_rate: Decimal
    ) -> PricingRecommendation:
        """
        生成定价推荐

        Args:
            total_cost: 总成本
            target_margin_rate: 目标毛利率（0-1）

        Returns:
            定价推荐
        """
        # 基于目标毛利率计算建议价格
        suggested_price = total_cost / (Decimal("1") - target_margin_rate)

        # 低中高三档
        low = suggested_price * Decimal("0.90")
        medium = suggested_price
        high = suggested_price * Decimal("1.15")

        return PricingRecommendation(
            low=low,
            medium=medium,
            high=high,
            suggested_price=suggested_price,
            target_margin_rate=target_margin_rate * Decimal("100"),
            market_analysis="基于行业标准毛利率和历史成交数据分析",
        )

    def adjust_for_competition(
        self,
        base_pricing: PricingRecommendation,
        competition_level: str
    ) -> PricingRecommendation:
        """
        根据市场竞争调整定价

        Args:
            base_pricing: 基础定价
            competition_level: 竞争等级（low/medium/high）

        Returns:
            调整后的定价
        """
        competition_factor = {
            "low": Decimal("1.05"),
            "medium": Decimal("1.0"),
            "high": Decimal("0.95"),
        }.get(competition_level, Decimal("1.0"))

        return PricingRecommendation(
            low=base_pricing.low * competition_factor,
            medium=base_pricing.medium * competition_factor,
            high=base_pricing.high * competition_factor,
            suggested_price=base_pricing.suggested_price * competition_factor,
            target_margin_rate=base_pricing.target_margin_rate,
            market_analysis=f"市场竞争程度: {competition_level}, 建议价格调整系数: {competition_factor}",
        )

    def analyze_sensitivity(
        self,
        cost: Decimal,
        pricing: PricingRecommendation,
        customer_budget: Optional[Decimal]
    ) -> Dict[str, Any]:
        """
        价格敏感度分析

        Args:
            cost: 总成本
            pricing: 定价推荐
            customer_budget: 客户预算

        Returns:
            敏感度分析结果
        """
        analysis = {
            "cost_base": float(cost),
            "price_range": {
                "min": float(pricing.low),
                "recommended": float(pricing.medium),
                "max": float(pricing.high),
            },
            "margin_analysis": {
                "low_price_margin": float((pricing.low - cost) / pricing.low * 100),
                "recommended_margin": float((pricing.medium - cost) / pricing.medium * 100),
                "high_price_margin": float((pricing.high - cost) / pricing.high * 100),
            },
        }

        if customer_budget:
            analysis["budget_fit"] = {
                "customer_budget": float(customer_budget),
                "fits_low": customer_budget >= pricing.low,
                "fits_recommended": customer_budget >= pricing.medium,
                "fits_high": customer_budget >= pricing.high,
                "recommended_strategy": self._get_pricing_strategy(customer_budget, pricing),
            }

        return analysis

    def _get_pricing_strategy(
        self,
        budget: Decimal,
        pricing: PricingRecommendation
    ) -> str:
        """获取定价策略"""
        if budget >= pricing.high:
            return "客户预算充足,可报高价档,强调高附加值服务"
        elif budget >= pricing.medium:
            return "客户预算适中,推荐标准报价,平衡利润与成交率"
        elif budget >= pricing.low:
            return "客户预算偏紧,可考虑低价档,但需简化部分服务"
        else:
            return "客户预算低于成本,建议优化方案或放弃该项目"

    def calculate_competitiveness(
        self,
        pricing: PricingRecommendation,
        customer_budget: Optional[Decimal]
    ) -> Decimal:
        """计算竞争力评分"""
        if not customer_budget:
            return Decimal("0.70")  # 默认中等竞争力

        if customer_budget >= pricing.medium:
            return Decimal("0.90")
        elif customer_budget >= pricing.low:
            return Decimal("0.75")
        else:
            return Decimal("0.50")

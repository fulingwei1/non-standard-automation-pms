# -*- coding: utf-8 -*-
"""
销售推荐引擎模块

提供各类销售策略推荐的独立引擎：
- FollowUpEngine: 跟进策略推荐
- PricingEngine: 报价优化建议
- RelationshipEngine: 客户关系维护建议
- CrossSellEngine: 交叉销售推荐
- RiskEngine: 风险预警推荐
"""

from app.services.sales.engines.base import (
    Recommendation,
    RecommendationPriority,
    RecommendationResult,
    RecommendationType,
)
from app.services.sales.engines.cross_sell_engine import CrossSellEngine
from app.services.sales.engines.follow_up_engine import FollowUpEngine
from app.services.sales.engines.pricing_engine import PricingEngine
from app.services.sales.engines.relationship_engine import RelationshipEngine
from app.services.sales.engines.risk_engine import RiskEngine

__all__ = [
    "Recommendation",
    "RecommendationPriority",
    "RecommendationResult",
    "RecommendationType",
    "FollowUpEngine",
    "PricingEngine",
    "RelationshipEngine",
    "CrossSellEngine",
    "RiskEngine",
]

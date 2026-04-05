# -*- coding: utf-8 -*-
"""
销售智能推荐服务

基于历史数据、行业知识和机器学习模型，为销售团队提供智能化建议：
- 商机跟进策略推荐
- 报价优化建议
- 客户关系维护建议
- 交叉销售/升级销售推荐
- 销售活动优先级排序
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

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

logger = logging.getLogger(__name__)


class SalesRecommendationService:
    """
    销售智能推荐服务

    提供基于规则和数据分析的销售策略推荐。

    Usage:
        service = SalesRecommendationService(db)
        result = service.get_recommendations(user_id=1)
        for rec in result.recommendations:
            print(f"{rec.priority}: {rec.title}")
    """

    def __init__(self, db: Session):
        self.db = db
        # 初始化各推荐引擎
        self._follow_up_engine = FollowUpEngine(db)
        self._pricing_engine = PricingEngine(db)
        self._relationship_engine = RelationshipEngine(db)
        self._cross_sell_engine = CrossSellEngine(db)
        self._risk_engine = RiskEngine(db)

    def get_recommendations(
        self,
        user_id: int,
        types: Optional[List[RecommendationType]] = None,
        limit: int = 20,
    ) -> RecommendationResult:
        """
        获取用户的销售推荐

        Args:
            user_id: 用户ID
            types: 推荐类型过滤
            limit: 返回数量限制

        Returns:
            推荐结果
        """
        recommendations: List[Recommendation] = []

        # 1. 跟进策略推荐
        if not types or RecommendationType.FOLLOW_UP in types:
            recommendations.extend(
                self._follow_up_engine.get_recommendations(user_id)
            )

        # 2. 报价优化建议
        if not types or RecommendationType.PRICING in types:
            recommendations.extend(
                self._pricing_engine.get_recommendations(user_id)
            )

        # 3. 客户关系维护建议
        if not types or RecommendationType.RELATIONSHIP in types:
            recommendations.extend(
                self._relationship_engine.get_recommendations(user_id)
            )

        # 4. 交叉销售推荐
        if not types or RecommendationType.CROSS_SELL in types:
            recommendations.extend(
                self._cross_sell_engine.get_recommendations(user_id)
            )

        # 5. 风险预警
        if not types or RecommendationType.RISK in types:
            recommendations.extend(
                self._risk_engine.get_recommendations(user_id)
            )

        # 按优先级排序
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
        }
        recommendations.sort(key=lambda r: (priority_order[r.priority], -r.confidence))

        # 限制数量
        recommendations = recommendations[:limit]

        # 生成摘要
        summary = self._generate_summary(recommendations)

        return RecommendationResult(
            user_id=user_id,
            generated_at=datetime.now(),
            recommendations=recommendations,
            summary=summary,
        )

    def _generate_summary(
        self, recommendations: List[Recommendation]
    ) -> Dict[str, Any]:
        """生成推荐摘要"""
        summary = {
            "total_count": len(recommendations),
            "by_type": {},
            "by_priority": {},
            "critical_count": 0,
            "high_count": 0,
        }

        for rec in recommendations:
            # 按类型统计
            type_key = rec.type.value
            if type_key not in summary["by_type"]:
                summary["by_type"][type_key] = 0
            summary["by_type"][type_key] += 1

            # 按优先级统计
            priority_key = rec.priority.value
            if priority_key not in summary["by_priority"]:
                summary["by_priority"][priority_key] = 0
            summary["by_priority"][priority_key] += 1

            # 紧急/高优先级计数
            if rec.priority == RecommendationPriority.CRITICAL:
                summary["critical_count"] += 1
            elif rec.priority == RecommendationPriority.HIGH:
                summary["high_count"] += 1

        return summary

    def get_opportunity_recommendations(
        self, opportunity_id: int
    ) -> List[Recommendation]:
        """
        获取针对特定商机的推荐

        Args:
            opportunity_id: 商机ID

        Returns:
            推荐列表
        """
        from app.models.sales import Opportunity

        recommendations = []

        try:
            opp = (
                self.db.query(Opportunity)
                .filter(Opportunity.id == opportunity_id)
                .first()
            )

            if not opp:
                return recommendations

            # 基于商机阶段的推荐
            stage_recommendations = {
                "DISCOVERY": [
                    ("确认客户痛点", "深入了解客户业务问题和需求"),
                    ("识别决策链", "明确决策者、影响者和使用者"),
                    ("评估预算", "确认客户预算范围和采购时间线"),
                ],
                "QUALIFICATION": [
                    ("验证技术可行性", "安排技术评估会议"),
                    ("竞争分析", "了解竞争对手情况，突出差异化优势"),
                    ("建立高层关系", "安排高层拜访建立信任"),
                ],
                "PROPOSAL": [
                    ("定制化方案", "根据客户需求定制解决方案"),
                    ("价值展示", "准备ROI分析和成功案例"),
                    ("内部审批准备", "确保报价符合公司政策"),
                ],
                "NEGOTIATION": [
                    ("灵活谈判", "准备多种报价方案和备选条款"),
                    ("处理异议", "预判客户可能的异议并准备回应"),
                    ("推动签约", "设置签约时间线，创造紧迫感"),
                ],
            }

            if opp.stage in stage_recommendations:
                for title, desc in stage_recommendations[opp.stage]:
                    recommendations.append(
                        Recommendation(
                            type=RecommendationType.FOLLOW_UP,
                            priority=RecommendationPriority.MEDIUM,
                            title=title,
                            description=desc,
                            action=f"针对{opp.stage}阶段的关键行动",
                            entity_type="opportunity",
                            entity_id=opp.id,
                            confidence=0.8,
                        )
                    )

            # 基于赢率的推荐
            probability = opp.probability or 0
            if probability < 30:
                recommendations.append(
                    Recommendation(
                        type=RecommendationType.RISK,
                        priority=RecommendationPriority.HIGH,
                        title="低赢率商机需关注",
                        description=f"当前赢率仅 {probability}%，需要采取行动提高成功率",
                        action="重新评估商机，考虑调整策略或重新分配资源",
                        entity_type="opportunity",
                        entity_id=opp.id,
                        confidence=0.85,
                        data={"probability": probability},
                    )
                )

        except Exception as e:
            logger.error(f"获取商机推荐失败: {e}")

        return recommendations

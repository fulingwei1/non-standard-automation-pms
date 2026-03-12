# -*- coding: utf-8 -*-
"""
跟进策略推荐引擎

分析商机状态，提供跟进策略建议：
- 预计成交日期临近提醒
- 商机停滞预警
- 高价值商机加速建议
"""

import logging
from datetime import date, datetime
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.services.sales.engines.base import (
    BaseRecommendationEngine,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)

logger = logging.getLogger(__name__)


class FollowUpEngine(BaseRecommendationEngine):
    """跟进策略推荐引擎"""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_recommendations(self, user_id: int) -> List[Recommendation]:
        """获取跟进策略推荐"""
        from app.models.sales import Opportunity

        recommendations = []
        today = date.today()

        try:
            # 查询用户负责的活跃商机（使用 joinedload 避免 N+1 查询）
            opportunities = (
                self.db.query(Opportunity)
                .options(
                    joinedload(Opportunity.customer),
                    joinedload(Opportunity.owner),
                )
                .filter(
                    Opportunity.owner_id == user_id,
                    Opportunity.stage.notin_(["WON", "LOST", "CANCELLED"]),
                )
                .all()
            )

            for opp in opportunities:
                # 规则1: 预计成交日期临近（7天内）
                recommendations.extend(
                    self._check_close_date_approaching(opp, today)
                )

                # 规则2: 商机停滞（超过14天无更新）
                recommendations.extend(
                    self._check_stagnant_opportunity(opp)
                )

                # 规则3: 高价值商机未进入谈判阶段
                recommendations.extend(
                    self._check_high_value_opportunity(opp)
                )

        except Exception as e:
            logger.error(f"获取跟进推荐失败: {e}")

        return recommendations

    def _check_close_date_approaching(
        self, opp, today: date
    ) -> List[Recommendation]:
        """检查预计成交日期是否临近"""
        recommendations = []

        if opp.expected_close_date:
            days_to_close = (opp.expected_close_date - today).days
            if 0 < days_to_close <= 7:
                recommendations.append(
                    Recommendation(
                        type=RecommendationType.FOLLOW_UP,
                        priority=RecommendationPriority.HIGH,
                        title=f"商机即将到期: {opp.opp_name}",
                        description=f"预计成交日期为 {opp.expected_close_date}，仅剩 {days_to_close} 天",
                        action="立即联系客户确认进度，推动成交或更新预计日期",
                        entity_type="opportunity",
                        entity_id=opp.id,
                        confidence=0.9,
                        expected_impact="避免商机流失",
                        data={"days_to_close": days_to_close},
                    )
                )

        return recommendations

    def _check_stagnant_opportunity(self, opp) -> List[Recommendation]:
        """检查商机是否停滞"""
        recommendations = []

        if opp.updated_at:
            days_since_update = (datetime.now() - opp.updated_at).days
            if days_since_update > 14:
                recommendations.append(
                    Recommendation(
                        type=RecommendationType.FOLLOW_UP,
                        priority=RecommendationPriority.MEDIUM,
                        title=f"商机停滞: {opp.opp_name}",
                        description=f"已 {days_since_update} 天没有更新",
                        action="检查商机状态，联系客户或考虑调整策略",
                        entity_type="opportunity",
                        entity_id=opp.id,
                        confidence=0.75,
                        expected_impact="激活停滞商机",
                        data={"days_since_update": days_since_update},
                    )
                )

        return recommendations

    def _check_high_value_opportunity(self, opp) -> List[Recommendation]:
        """检查高价值商机是否需要加速"""
        recommendations = []

        est_amount = opp.est_amount or 0
        if est_amount > 500000 and opp.stage in ["DISCOVERY", "QUALIFICATION"]:
            recommendations.append(
                Recommendation(
                    type=RecommendationType.FOLLOW_UP,
                    priority=RecommendationPriority.HIGH,
                    title=f"高价值商机需加速: {opp.opp_name}",
                    description=f"预估金额 ¥{est_amount:,.0f}，当前阶段为{opp.stage}",
                    action="安排高层拜访，加速推进商机进入提案阶段",
                    entity_type="opportunity",
                    entity_id=opp.id,
                    confidence=0.85,
                    expected_impact="提高大单转化率",
                    data={"est_amount": float(est_amount)},
                )
            )

        return recommendations

# -*- coding: utf-8 -*-
"""
报价优化推荐引擎

分析报价数据，提供定价优化建议：
- 毛利率过低预警
- 报价金额异常检测
"""

import logging
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.services.sales.engines.base import (
    BaseRecommendationEngine,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)

logger = logging.getLogger(__name__)


class PricingEngine(BaseRecommendationEngine):
    """报价优化推荐引擎"""

    # 毛利率阈值
    MIN_MARGIN_RATE = 15  # 最低毛利率要求（%）

    def __init__(self, db: Session):
        super().__init__(db)

    def get_recommendations(self, user_id: int) -> List[Recommendation]:
        """获取报价优化建议"""
        from app.models.sales import Quote

        recommendations = []

        try:
            # 查询用户负责的待审批报价，预加载版本信息避免 N+1 查询
            quotes = (
                self.db.query(Quote)
                .options(
                    joinedload(Quote.current_version),
                    joinedload(Quote.versions),
                )
                .filter(
                    Quote.owner_id == user_id,
                    Quote.status.in_(["DRAFT", "PENDING_APPROVAL"]),
                )
                .all()
            )

            for quote in quotes:
                # 使用预加载的版本信息获取最新版本
                latest_version = self._get_latest_version(quote)

                if not latest_version:
                    continue

                # 检查毛利率
                recommendations.extend(
                    self._check_low_margin(quote, latest_version)
                )

        except Exception as e:
            logger.error(f"获取报价推荐失败: {e}")

        return recommendations

    @staticmethod
    def _get_latest_version(quote):
        """从预加载的版本中获取最新版本"""
        if quote.current_version:
            return quote.current_version
        if quote.versions:
            # 按版本号降序排序，取最新的
            return max(quote.versions, key=lambda v: v.version_number or 0)
        return None

    def _check_low_margin(self, quote, version) -> List[Recommendation]:
        """检查毛利率是否过低"""
        recommendations = []

        margin = version.margin_rate or 0
        if margin < self.MIN_MARGIN_RATE:
            recommendations.append(
                Recommendation(
                    type=RecommendationType.PRICING,
                    priority=RecommendationPriority.HIGH,
                    title=f"报价毛利率过低: {quote.quote_code}",
                    description=f"当前毛利率仅 {margin:.1f}%，低于公司标准({self.MIN_MARGIN_RATE}%)",
                    action="审查成本结构，考虑调整定价或与客户协商",
                    entity_type="quote",
                    entity_id=quote.id,
                    confidence=0.95,
                    expected_impact="提高项目利润率",
                    data={"margin_rate": float(margin)},
                )
            )

        return recommendations

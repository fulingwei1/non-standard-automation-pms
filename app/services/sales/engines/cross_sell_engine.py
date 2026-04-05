# -*- coding: utf-8 -*-
"""
交叉销售推荐引擎

分析客户购买历史，提供交叉销售和升级销售建议：
- 近期成交客户的关联产品推荐
- 基于购买模式的产品推荐
"""

import logging
from datetime import datetime, timedelta
from typing import List, Set

from sqlalchemy.orm import Session, joinedload

from app.services.sales.engines.base import (
    BaseRecommendationEngine,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)

logger = logging.getLogger(__name__)


class CrossSellEngine(BaseRecommendationEngine):
    """交叉销售推荐引擎"""

    # 近期成交时间窗口（天）
    RECENT_DAYS = 90

    def __init__(self, db: Session):
        super().__init__(db)

    def get_recommendations(self, user_id: int) -> List[Recommendation]:
        """获取交叉销售推荐"""
        from app.models.sales import Contract

        recommendations = []

        try:
            # 查询近期成交的合同，预加载客户信息避免 N+1 查询
            recent_contracts = (
                self.db.query(Contract)
                .options(joinedload(Contract.customer))
                .filter(
                    Contract.sales_owner_id == user_id,
                    Contract.status.in_(["SIGNED", "ACTIVE", "EXECUTING"]),
                    Contract.created_at >= datetime.now() - timedelta(days=self.RECENT_DAYS),
                )
                .all()
            )

            processed_customers: Set[int] = set()

            for contract in recent_contracts:
                if contract.customer_id in processed_customers:
                    continue
                processed_customers.add(contract.customer_id)

                # 使用预加载的客户信息，无需额外查询
                customer = contract.customer
                if not customer:
                    continue

                # 生成交叉销售建议
                recommendations.extend(
                    self._generate_cross_sell_for_customer(customer, contract)
                )

        except Exception as e:
            logger.error(f"获取交叉销售推荐失败: {e}")

        return recommendations

    def _generate_cross_sell_for_customer(
        self, customer, recent_contract
    ) -> List[Recommendation]:
        """为客户生成交叉销售建议"""
        recommendations = []

        # 基础交叉销售推荐
        # 实际应用中应该基于产品关联分析和客户画像
        recommendations.append(
            Recommendation(
                type=RecommendationType.CROSS_SELL,
                priority=RecommendationPriority.LOW,
                title=f"交叉销售机会: {customer.customer_name}",
                description="近期签约客户，可推荐关联产品或服务",
                action="分析客户需求，准备关联产品方案进行二次销售",
                entity_type="customer",
                entity_id=customer.id,
                confidence=0.6,
                expected_impact="增加客户终身价值",
                data={"recent_contract_id": recent_contract.id},
            )
        )

        return recommendations

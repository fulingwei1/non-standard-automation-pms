# -*- coding: utf-8 -*-
"""
客户关系维护推荐引擎

分析客户互动历史，提供关系维护建议：
- 长期未联系的重要客户提醒
- 客户流失风险预警
"""

import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.services.sales.engines.base import (
    BaseRecommendationEngine,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)

logger = logging.getLogger(__name__)


class RelationshipEngine(BaseRecommendationEngine):
    """客户关系维护推荐引擎"""

    # 客户沉默阈值（天）
    CUSTOMER_SILENT_DAYS = 180

    def __init__(self, db: Session):
        super().__init__(db)

    def get_recommendations(self, user_id: int) -> List[Recommendation]:
        """获取客户关系维护建议"""
        from app.models.sales import Contract

        recommendations = []

        try:
            # 一次性查询所有用户负责的合同，预加载客户信息避免 N+1 查询
            contracts = (
                self.db.query(Contract)
                .options(joinedload(Contract.customer))
                .filter(Contract.sales_owner_id == user_id)
                .order_by(Contract.customer_id, Contract.created_at.desc())
                .all()
            )

            # 按客户分组，保留每个客户的最新合同
            latest_by_customer: dict = {}
            for contract in contracts:
                if contract.customer_id and contract.customer_id not in latest_by_customer:
                    latest_by_customer[contract.customer_id] = contract

            # 检查每个客户的最近业务往来
            for contract in latest_by_customer.values():
                recommendations.extend(
                    self._check_customer_activity(contract)
                )

        except Exception as e:
            logger.error(f"获取客户关系推荐失败: {e}")

        return recommendations

    def _check_customer_activity(self, latest_contract) -> List[Recommendation]:
        """检查客户最近业务活动（使用预加载的合同和客户数据）"""
        recommendations = []
        customer = latest_contract.customer

        if not customer or not latest_contract.created_at:
            return recommendations

        days_since_last = (datetime.now() - latest_contract.created_at).days

        if days_since_last > self.CUSTOMER_SILENT_DAYS:
            recommendations.append(
                Recommendation(
                    type=RecommendationType.RELATIONSHIP,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"客户关系需维护: {customer.customer_name}",
                    description=f"已 {days_since_last} 天没有新业务",
                    action="安排客户拜访，了解近期需求，维护客户关系",
                    entity_type="customer",
                    entity_id=customer.id,
                    confidence=0.7,
                    expected_impact="防止客户流失，挖掘新商机",
                    data={"days_since_last_contract": days_since_last},
                )
            )

        return recommendations

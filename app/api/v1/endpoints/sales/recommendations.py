# -*- coding: utf-8 -*-
"""
销售智能推荐 API

提供基于数据分析的销售策略推荐接口。
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.recommendation_service import (
    RecommendationType,
    SalesRecommendationService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/recommendations", response_model=ResponseModel)
def get_recommendations(
    db: Session = Depends(deps.get_db),
    types: Optional[List[str]] = Query(
        None,
        description="推荐类型过滤: follow_up, pricing, relationship, cross_sell, upsell, risk",
    ),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取当前用户的销售智能推荐

    基于用户负责的商机、合同、客户等数据，提供个性化的销售策略建议。

    推荐类型：
    - follow_up: 跟进策略（商机跟进、客户联系）
    - pricing: 报价优化（毛利率、定价策略）
    - relationship: 客户关系维护
    - cross_sell: 交叉销售机会
    - upsell: 升级销售机会
    - risk: 风险预警（合同到期、发票逾期）

    返回按优先级排序的推荐列表。
    """
    # 转换类型参数
    type_filters = None
    if types:
        type_filters = []
        for t in types:
            try:
                type_filters.append(RecommendationType(t))
            except ValueError:
                pass  # 忽略无效的类型

    service = SalesRecommendationService(db)
    result = service.get_recommendations(
        user_id=current_user.id,
        types=type_filters,
        limit=limit,
    )

    # 转换为字典格式
    recommendations_data = []
    for rec in result.recommendations:
        recommendations_data.append(
            {
                "type": rec.type.value,
                "priority": rec.priority.value,
                "title": rec.title,
                "description": rec.description,
                "action": rec.action,
                "entity_type": rec.entity_type,
                "entity_id": rec.entity_id,
                "confidence": rec.confidence,
                "expected_impact": rec.expected_impact,
                "data": rec.data,
            }
        )

    return ResponseModel(
        code=200,
        message="获取推荐成功",
        data={
            "user_id": result.user_id,
            "generated_at": result.generated_at.isoformat(),
            "recommendations": recommendations_data,
            "summary": result.summary,
        },
    )


@router.get("/recommendations/opportunity/{opportunity_id}", response_model=ResponseModel)
def get_opportunity_recommendations(
    opportunity_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取针对特定商机的智能推荐

    基于商机当前阶段、赢率、历史数据等，提供针对性的行动建议。
    """
    service = SalesRecommendationService(db)
    recommendations = service.get_opportunity_recommendations(opportunity_id)

    recommendations_data = []
    for rec in recommendations:
        recommendations_data.append(
            {
                "type": rec.type.value,
                "priority": rec.priority.value,
                "title": rec.title,
                "description": rec.description,
                "action": rec.action,
                "confidence": rec.confidence,
                "data": rec.data,
            }
        )

    return ResponseModel(
        code=200,
        message="获取商机推荐成功",
        data={
            "opportunity_id": opportunity_id,
            "recommendations": recommendations_data,
            "count": len(recommendations_data),
        },
    )


@router.get("/recommendations/summary", response_model=ResponseModel)
def get_recommendations_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取推荐摘要

    返回各类型推荐的数量统计，用于仪表盘展示。
    """
    service = SalesRecommendationService(db)
    result = service.get_recommendations(
        user_id=current_user.id,
        limit=100,  # 获取所有推荐用于统计
    )

    return ResponseModel(
        code=200,
        message="获取推荐摘要成功",
        data={
            "user_id": result.user_id,
            "generated_at": result.generated_at.isoformat(),
            "summary": result.summary,
            "action_required": result.summary.get("critical_count", 0)
            + result.summary.get("high_count", 0),
        },
    )

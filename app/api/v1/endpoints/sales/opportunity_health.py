# -*- coding: utf-8 -*-
"""
商机健康度 API

提供商机健康状态评估接口。
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.opportunity_health_service import (
    HealthLevel,
    OpportunityHealthService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/opportunities/{opp_id}/health", response_model=ResponseModel)
def get_opportunity_health(
    opp_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取单个商机的健康度评分

    返回多维度健康评估：
    - 跟进活跃度 (25%)
    - 阶段进展 (25%)
    - 信息完整度 (20%)
    - 客户互动 (15%)
    - 风险因素 (15%)

    每个维度包含得分、等级、详情和改进建议。
    """
    service = OpportunityHealthService(db)
    health = service.get_opportunity_health(opp_id)

    if not health:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 转换为字典
    dimension_details = []
    for ds in health.dimension_scores:
        dimension_details.append({
            "dimension": ds.dimension.value,
            "score": ds.score,
            "weight": ds.weight,
            "level": ds.level.value,
            "details": ds.details,
            "suggestions": ds.suggestions,
        })

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "opportunity_id": health.opportunity_id,
            "opportunity_code": health.opportunity_code,
            "opportunity_name": health.opportunity_name,
            "customer_name": health.customer_name,
            "stage": health.stage,
            "est_amount": health.est_amount,
            # 总体评分
            "total_score": health.total_score,
            "health_level": health.health_level.value,
            # 各维度得分
            "dimensions": dimension_details,
            # 关键问题和建议
            "key_issues": health.key_issues,
            "top_suggestions": health.top_suggestions,
            # 时间信息
            "last_activity_at": health.last_activity_at.isoformat() if health.last_activity_at else None,
            "days_in_stage": health.days_in_stage,
        },
    )


@router.get("/opportunities/health", response_model=ResponseModel)
def get_opportunities_health_list(
    db: Session = Depends(deps.get_db),
    level: Optional[str] = Query(
        None,
        description="健康等级过滤: excellent, good, warning, critical",
    ),
    include_closed: bool = Query(False, description="是否包含已关闭商机"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取当前用户所有商机的健康度列表

    按健康度得分升序排列（问题商机优先展示）。
    """
    service = OpportunityHealthService(db)
    health_list = service.get_user_opportunities_health(
        user_id=current_user.id,
        include_closed=include_closed,
        limit=limit,
    )

    # 按等级过滤
    if level:
        try:
            level_filter = HealthLevel(level)
            health_list = [h for h in health_list if h.health_level == level_filter]
        except ValueError:
            pass

    items = []
    for health in health_list:
        items.append({
            "opportunity_id": health.opportunity_id,
            "opportunity_code": health.opportunity_code,
            "opportunity_name": health.opportunity_name,
            "customer_name": health.customer_name,
            "stage": health.stage,
            "est_amount": health.est_amount,
            "total_score": health.total_score,
            "health_level": health.health_level.value,
            "key_issues": health.key_issues,
            "days_in_stage": health.days_in_stage,
        })

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": items,
            "total": len(items),
        },
    )


@router.get("/opportunities/health/summary", response_model=ResponseModel)
def get_opportunities_health_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取商机健康度汇总统计

    返回：
    - 各健康等级的商机数量和金额
    - 平均健康得分
    - 问题商机列表（warning + critical）

    适合在仪表盘展示整体商机健康状况。
    """
    service = OpportunityHealthService(db)
    summary = service.get_health_summary(current_user.id)

    return ResponseModel(
        code=200,
        message="获取成功",
        data=summary,
    )


@router.get("/opportunities/health/critical", response_model=ResponseModel)
def get_critical_opportunities(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取危险状态的商机列表

    仅返回健康等级为 critical 的商机，这些商机需要立即关注。
    """
    service = OpportunityHealthService(db)
    health_list = service.get_user_opportunities_health(
        user_id=current_user.id,
        limit=20,
    )

    critical_list = [h for h in health_list if h.health_level == HealthLevel.CRITICAL]

    items = []
    for health in critical_list:
        items.append({
            "opportunity_id": health.opportunity_id,
            "opportunity_code": health.opportunity_code,
            "opportunity_name": health.opportunity_name,
            "customer_name": health.customer_name,
            "stage": health.stage,
            "est_amount": health.est_amount,
            "total_score": health.total_score,
            "key_issues": health.key_issues,
            "top_suggestions": health.top_suggestions,
        })

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": items,
            "count": len(items),
            "tip": "这些商机需要立即关注和处理" if items else "暂无危险状态的商机 👍",
        },
    )

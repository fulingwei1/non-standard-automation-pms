# -*- coding: utf-8 -*-
"""
个人绩效 - 趋势分析
"""
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.performance import PerformancePeriod, PerformanceResult
from app.models.user import User
from app.schemas.performance import PerformanceTrendResponse

from .utils import _check_performance_view_permission

router = APIRouter()


@router.get("/trends/{user_id}", response_model=PerformanceTrendResponse, status_code=status.HTTP_200_OK)
def get_performance_trends(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    period_type: str = Query("MONTHLY", description="周期类型"),
    periods_count: int = Query(6, ge=1, le=12, description="查询期数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    绩效趋势分析（多期对比）
    """
    # 检查权限（只能查看自己或下属的绩效）
    if not _check_performance_view_permission(current_user, user_id, db):
        raise HTTPException(status_code=403, detail="您没有权限查看此用户的绩效")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取最近的几个周期
    periods = db.query(PerformancePeriod).filter(
        PerformancePeriod.period_type == period_type,
        PerformancePeriod.status == "FINALIZED"
    ).order_by(desc(PerformancePeriod.end_date)).limit(periods_count).all()

    periods_data = []
    scores = []

    for period in periods:
        result = db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period.id,
            PerformanceResult.user_id == user_id
        ).first()

        score = float(result.total_score) if result and result.total_score else 0
        scores.append(score)

        periods_data.append({
            "period_id": period.id,
            "period_name": period.period_name,
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
            "score": score,
            "level": result.level if result else "QUALIFIED"
        })

    # 计算趋势
    if len(scores) >= 2:
        recent_avg = sum(scores[:3]) / min(3, len(scores))
        earlier_avg = sum(scores[-3:]) / min(3, len(scores[-3:]))
        if recent_avg > earlier_avg * 1.05:
            trend_direction = "UP"
        elif recent_avg < earlier_avg * 0.95:
            trend_direction = "DOWN"
        else:
            trend_direction = "STABLE"
    else:
        trend_direction = "STABLE"

    avg_score = Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")
    max_score = Decimal(str(max(scores))) if scores else Decimal("0")
    min_score = Decimal(str(min(scores))) if scores else Decimal("0")

    return PerformanceTrendResponse(
        user_id=user_id,
        user_name=target_user.real_name or target_user.username,
        periods=periods_data,
        trend_direction=trend_direction,
        avg_score=avg_score,
        max_score=max_score,
        min_score=min_score
    )

# -*- coding: utf-8 -*-
"""
个人绩效 - 我的绩效
"""
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.performance import (
    PerformanceIndicator,
    PerformancePeriod,
    PerformanceResult,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.performance import PersonalPerformanceResponse

from app.models.performance import ProjectContribution

router = APIRouter()


@router.get("/my", response_model=PersonalPerformanceResponse, status_code=status.HTTP_200_OK)
def get_my_performance(
    *,
    db: Session = Depends(deps.get_db),
    period_type: str = Query("MONTHLY", description="周期类型：WEEKLY/MONTHLY/QUARTERLY/YEARLY"),
    period_id: Optional[int] = Query(None, description="周期ID（不提供则取最新）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    查看我的绩效（周/月/季度）
    """
    # 获取周期
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.period_type == period_type,
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()

    if not period:
        raise HTTPException(status_code=404, detail="未找到对应的考核周期")

    # 获取绩效结果
    result = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.user_id == current_user.id
    ).first()

    if not result:
        return PersonalPerformanceResponse(
            user_id=current_user.id,
            user_name=current_user.real_name or current_user.username,
            period_id=period.id,
            period_name=period.period_name,
            period_type=period.period_type,
            start_date=period.start_date,
            end_date=period.end_date,
            total_score=Decimal("0"),
            level="QUALIFIED",
            indicators=[],
            project_contributions=[]
        )

    # 获取指标明细
    indicators = []
    if result.indicator_scores:
        for ind_id, score in result.indicator_scores.items():
            indicator = db.query(PerformanceIndicator).filter(PerformanceIndicator.id == int(ind_id)).first()
            if indicator:
                indicators.append({
                    "indicator_id": indicator.id,
                    "indicator_name": indicator.indicator_name,
                    "indicator_type": indicator.indicator_type,
                    "score": float(score),
                    "weight": float(indicator.weight) if indicator.weight else 0
                })

    # 获取项目贡献
    contributions = db.query(ProjectContribution).filter(
        ProjectContribution.period_id == period.id,
        ProjectContribution.user_id == current_user.id
    ).all()

    project_contributions = []
    for contrib in contributions:
        project = db.query(Project).filter(Project.id == contrib.project_id).first()
        project_contributions.append({
            "project_id": contrib.project_id,
            "project_name": project.project_name if project else None,
            "contribution_score": float(contrib.contribution_score) if contrib.contribution_score else 0,
            "work_hours": float(contrib.hours_spent) if contrib.hours_spent else 0,
            "task_count": contrib.task_count or 0
        })

    # 计算排名
    rank = None
    all_results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id
    ).order_by(desc(PerformanceResult.total_score)).all()

    for idx, r in enumerate(all_results, 1):
        if r.user_id == current_user.id:
            rank = idx
            break

    return PersonalPerformanceResponse(
        user_id=current_user.id,
        user_name=current_user.real_name or current_user.username,
        period_id=period.id,
        period_name=period.period_name,
        period_type=period.period_type,
        start_date=period.start_date,
        end_date=period.end_date,
        total_score=result.total_score or Decimal("0"),
        level=result.level or "QUALIFIED",
        rank=rank,
        indicators=indicators,
        project_contributions=project_contributions
    )

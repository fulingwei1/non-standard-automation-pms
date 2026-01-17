# -*- coding: utf-8 -*-
"""
项目评价统计端点
"""

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project_evaluation import ProjectEvaluation
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project_evaluation import ProjectEvaluationStatisticsResponse

router = APIRouter()


@router.get("/evaluations/statistics", response_model=ResponseModel[ProjectEvaluationStatisticsResponse], status_code=status.HTTP_200_OK)
def get_evaluation_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    获取项目评价统计
    """
    query = db.query(ProjectEvaluation).filter(
        ProjectEvaluation.status == 'CONFIRMED'
    )

    if start_date:
        query = query.filter(ProjectEvaluation.evaluation_date >= start_date)
    if end_date:
        query = query.filter(ProjectEvaluation.evaluation_date <= end_date)

    total_evaluations = query.count()

    # 按等级统计
    by_level = {}
    level_counts = query.with_entities(
        ProjectEvaluation.evaluation_level,
        func.count(ProjectEvaluation.id)
    ).group_by(ProjectEvaluation.evaluation_level).all()

    for level, count in level_counts:
        by_level[level] = count

    # 平均得分
    avg_scores = query.with_entities(
        func.avg(ProjectEvaluation.total_score),
        func.avg(ProjectEvaluation.novelty_score),
        func.avg(ProjectEvaluation.new_tech_score),
        func.avg(ProjectEvaluation.difficulty_score),
        func.avg(ProjectEvaluation.workload_score),
        func.avg(ProjectEvaluation.amount_score)
    ).first()

    return ResponseModel(
        code=200,
        data=ProjectEvaluationStatisticsResponse(
            total_evaluations=total_evaluations,
            by_level=by_level,
            avg_total_score=avg_scores[0] or Decimal('0'),
            avg_novelty_score=avg_scores[1] or Decimal('0'),
            avg_new_tech_score=avg_scores[2] or Decimal('0'),
            avg_difficulty_score=avg_scores[3] or Decimal('0'),
            avg_workload_score=avg_scores[4] or Decimal('0'),
            avg_amount_score=avg_scores[5] or Decimal('0')
        )
    )

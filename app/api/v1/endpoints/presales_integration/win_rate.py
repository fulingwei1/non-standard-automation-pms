# -*- coding: utf-8 -*-
"""
中标率预测端点
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.presales import WinRatePredictionRequest, WinRatePredictionResponse

from .utils import calculate_win_rate, get_win_rate_recommendations

router = APIRouter()


@router.post("/predict-win-rate", response_model=ResponseModel[WinRatePredictionResponse])
async def predict_win_rate(
    request: WinRatePredictionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("presales_integration:create"))
) -> Any:
    """预测线索中标概率"""

    # 获取销售人员历史中标率
    salesperson_stats = db.query(
        func.count(Project.id).label('total'),
        func.sum(func.case((Project.outcome == LeadOutcomeEnum.WON.value, 1), else_=0)).label('won')
    ).filter(
        Project.salesperson_id == request.salesperson_id,
        Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
    ).first()

    total = salesperson_stats.total or 0
    won = salesperson_stats.won or 0
    salesperson_win_rate = won / total if total > 0 else 0.2

    # 获取客户历史合作次数
    customer_cooperation_count = 0
    if request.customer_id:
        customer_cooperation_count = db.query(func.count(Project.id)).filter(
            Project.customer_id == request.customer_id,
            Project.outcome == LeadOutcomeEnum.WON.value
        ).scalar() or 0

    # 计算预测中标率
    predicted_rate, level, factors = calculate_win_rate(
        dimension_scores=request.dimension_scores,
        salesperson_win_rate=salesperson_win_rate,
        customer_cooperation_count=customer_cooperation_count,
        competitor_count=request.competitor_count or 3,
        is_repeat_customer=request.is_repeat_customer
    )

    # 获取建议
    recommendations = get_win_rate_recommendations(predicted_rate, factors)

    # 查找相似线索
    similar_count = db.query(func.count(Project.id)).filter(
        Project.evaluation_score.between(
            request.dimension_scores.total_score - 10,
            request.dimension_scores.total_score + 10
        ),
        Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
    ).scalar() or 0

    similar_won = db.query(func.count(Project.id)).filter(
        Project.evaluation_score.between(
            request.dimension_scores.total_score - 10,
            request.dimension_scores.total_score + 10
        ),
        Project.outcome == LeadOutcomeEnum.WON.value
    ).scalar() or 0

    similar_win_rate = similar_won / similar_count if similar_count > 0 else None

    return ResponseModel(
        code=200,
        message="预测成功",
        data=WinRatePredictionResponse(
            predicted_win_rate=round(predicted_rate, 3),
            probability_level=level,
            confidence=0.7 if total > 10 else 0.5,
            factors=factors,
            recommendations=recommendations,
            similar_leads_count=similar_count,
            similar_leads_win_rate=round(similar_win_rate, 3) if similar_win_rate else None
        )
    )

# -*- coding: utf-8 -*-
"""
绩效反馈 API 端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.performance import PerformancePeriod
from app.services.performance_feedback_service import PerformanceFeedbackService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/feedback", tags=["绩效反馈"])


@router.get("/{engineer_id}", summary="获取绩效反馈")
async def get_engineer_feedback(
    engineer_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师的绩效反馈"""
    service = PerformanceFeedbackService(db)

    feedback = service.get_engineer_feedback(engineer_id, period_id)

    return ResponseModel(
        code=200,
        message="获取绩效反馈成功",
        data=feedback
    )


@router.get("/message/{engineer_id}", summary="生成反馈消息")
async def generate_feedback_message(
    engineer_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成绩效反馈消息（用于通知）"""
    service = PerformanceFeedbackService(db)

    message = service.generate_feedback_message(engineer_id, period_id)

    return ResponseModel(
        code=200,
        message="生成反馈消息成功",
        data={'message': message}
    )


@router.get("/trend/{engineer_id}", summary="获取五维得分趋势")
async def get_dimension_trend(
    engineer_id: int,
    periods: int = Query(6, ge=2, le=12, description="历史周期数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师五维得分趋势"""
    service = PerformanceFeedbackService(db)

    trends = service.get_dimension_trend(engineer_id, periods)

    return ResponseModel(
        code=200,
        message="获取趋势数据成功",
        data=trends
    )


@router.get("/ability-changes/{engineer_id}", summary="识别能力变化")
async def identify_ability_changes(
    engineer_id: int,
    periods: int = Query(6, ge=2, le=12, description="历史周期数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """识别工程师能力变化"""
    service = PerformanceFeedbackService(db)

    changes = service.identify_ability_changes(engineer_id, periods)

    return ResponseModel(
        code=200,
        message="识别能力变化成功",
        data=changes
    )

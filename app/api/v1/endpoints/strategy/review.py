# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - 战略审视与日历
"""

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.common import PageResponse
from app.schemas.strategy import (
    CalendarMonthResponse,
    CalendarYearResponse,
    HealthScoreResponse,
    RoutineManagementCycleResponse,
    StrategyCalendarEventCreate,
    StrategyCalendarEventResponse,
    StrategyCalendarEventUpdate,
    StrategyReviewCreate,
    StrategyReviewResponse,
    StrategyReviewUpdate,
)
from app.services import strategy as strategy_service

router = APIRouter()


# ============================================
# 战略审视
# ============================================

@router.post("/reviews", response_model=StrategyReviewResponse, status_code=status.HTTP_201_CREATED)
def create_strategy_review(
    data: StrategyReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建战略审视记录
    """
    # 验证战略是否存在
    strategy = strategy_service.get_strategy(db, data.strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的战略不存在"
        )

    review = strategy_service.create_strategy_review(db, data, current_user.id)
    return review


@router.get("/reviews", response_model=PageResponse[StrategyReviewResponse])
def list_strategy_reviews(
    strategy_id: int = Query(..., description="战略 ID"),
    review_type: Optional[str] = Query(None, description="审视类型筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
):
    """
    获取战略审视记录列表
    """
    items, total = strategy_service.list_strategy_reviews(
        db, strategy_id, review_type, skip, limit
    )

    responses = [
        StrategyReviewResponse(
            id=r.id,
            strategy_id=r.strategy_id,
            review_date=r.review_date,
            review_period=r.review_period,
            review_type=r.review_type,
            health_score=r.health_score,
            financial_score=r.financial_score,
            customer_score=r.customer_score,
            internal_score=r.internal_score,
            learning_score=r.learning_score,
            summary=r.summary,
            achievements=r.achievements,
            issues=r.issues,
            action_items=r.action_items,
            next_steps=r.next_steps,
            created_by=r.created_by,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in items
    ]

    return PageResponse(
        items=responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/reviews/latest/{strategy_id}", response_model=StrategyReviewResponse)
def get_latest_review(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取最新的战略审视记录
    """
    review = strategy_service.get_latest_review(db, strategy_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有审视记录"
        )
    return review


@router.get("/reviews/{review_id}", response_model=StrategyReviewResponse)
def get_strategy_review(
    review_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取战略审视记录详情
    """
    review = strategy_service.get_strategy_review(db, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审视记录不存在"
        )

    return StrategyReviewResponse(
        id=review.id,
        strategy_id=review.strategy_id,
        review_date=review.review_date,
        review_period=review.review_period,
        review_type=review.review_type,
        health_score=review.health_score,
        financial_score=review.financial_score,
        customer_score=review.customer_score,
        internal_score=review.internal_score,
        learning_score=review.learning_score,
        summary=review.summary,
        achievements=review.achievements,
        issues=review.issues,
        action_items=review.action_items,
        next_steps=review.next_steps,
        created_by=review.created_by,
        is_active=review.is_active,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.put("/reviews/{review_id}", response_model=StrategyReviewResponse)
def update_strategy_review(
    review_id: int,
    data: StrategyReviewUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新战略审视记录
    """
    review = strategy_service.update_strategy_review(db, review_id, data)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审视记录不存在"
        )

    return StrategyReviewResponse(
        id=review.id,
        strategy_id=review.strategy_id,
        review_date=review.review_date,
        review_period=review.review_period,
        review_type=review.review_type,
        health_score=review.health_score,
        financial_score=review.financial_score,
        customer_score=review.customer_score,
        internal_score=review.internal_score,
        learning_score=review.learning_score,
        summary=review.summary,
        achievements=review.achievements,
        issues=review.issues,
        action_items=review.action_items,
        next_steps=review.next_steps,
        created_by=review.created_by,
        is_active=review.is_active,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy_review(
    review_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除战略审视记录（软删除）
    """
    success = strategy_service.delete_strategy_review(db, review_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审视记录不存在"
        )
    return None


# ============================================
# 健康度
# ============================================

@router.get("/health/{strategy_id}", response_model=HealthScoreResponse)
def get_health_score(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取健康度汇总
    """
    return strategy_service.get_health_score_summary(db, strategy_id)


# ============================================
# 战略日历
# ============================================

@router.post("/calendar/events", response_model=StrategyCalendarEventResponse, status_code=status.HTTP_201_CREATED)
def create_calendar_event(
    data: StrategyCalendarEventCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建日历事件
    """
    event = strategy_service.create_calendar_event(db, data)
    return StrategyCalendarEventResponse(
        id=event.id,
        strategy_id=event.strategy_id,
        event_type=event.event_type,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        start_time=event.start_time,
        end_time=event.end_time,
        is_recurring=event.is_recurring,
        recurrence_pattern=event.recurrence_pattern,
        status=event.status,
        owner_user_id=event.owner_user_id,
        related_csf_id=event.related_csf_id,
        related_kpi_id=event.related_kpi_id,
        is_active=event.is_active,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.get("/calendar/events", response_model=PageResponse[StrategyCalendarEventResponse])
def list_calendar_events(
    strategy_id: int = Query(..., description="战略 ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
):
    """
    获取日历事件列表
    """
    items, total = strategy_service.list_calendar_events(
        db, strategy_id, start_date, end_date, event_type, skip, limit
    )

    responses = [
        StrategyCalendarEventResponse(
            id=e.id,
            strategy_id=e.strategy_id,
            event_type=e.event_type,
            title=e.title,
            description=e.description,
            event_date=e.event_date,
            start_time=e.start_time,
            end_time=e.end_time,
            is_recurring=e.is_recurring,
            recurrence_pattern=e.recurrence_pattern,
            status=e.status,
            owner_user_id=e.owner_user_id,
            related_csf_id=e.related_csf_id,
            related_kpi_id=e.related_kpi_id,
            is_active=e.is_active,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in items
    ]

    return PageResponse(
        items=responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/calendar/month/{strategy_id}", response_model=CalendarMonthResponse)
def get_calendar_month(
    strategy_id: int,
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    db: Session = Depends(deps.get_db),
):
    """
    获取月度日历
    """
    return strategy_service.get_calendar_month(db, strategy_id, year, month)


@router.get("/calendar/year/{strategy_id}", response_model=CalendarYearResponse)
def get_calendar_year(
    strategy_id: int,
    year: int = Query(..., description="年份"),
    db: Session = Depends(deps.get_db),
):
    """
    获取年度日历概览
    """
    return strategy_service.get_calendar_year(db, strategy_id, year)


@router.put("/calendar/events/{event_id}", response_model=StrategyCalendarEventResponse)
def update_calendar_event(
    event_id: int,
    data: StrategyCalendarEventUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新日历事件
    """
    event = strategy_service.update_calendar_event(db, event_id, data)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )

    return StrategyCalendarEventResponse(
        id=event.id,
        strategy_id=event.strategy_id,
        event_type=event.event_type,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        start_time=event.start_time,
        end_time=event.end_time,
        is_recurring=event.is_recurring,
        recurrence_pattern=event.recurrence_pattern,
        status=event.status,
        owner_user_id=event.owner_user_id,
        related_csf_id=event.related_csf_id,
        related_kpi_id=event.related_kpi_id,
        is_active=event.is_active,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.delete("/calendar/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_event(
    event_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除日历事件（软删除）
    """
    success = strategy_service.delete_calendar_event(db, event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    return None


# ============================================
# 例行管理
# ============================================

@router.get("/routine/{strategy_id}", response_model=RoutineManagementCycleResponse)
def get_routine_management_cycle(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取例行管理周期配置
    """
    return strategy_service.get_routine_management_cycle(db, strategy_id)


@router.post("/routine/{strategy_id}/generate-events", response_model=Dict[str, Any])
def generate_routine_events(
    strategy_id: int,
    year: int = Query(..., description="年份"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    生成年度例行管理事件
    """
    events = strategy_service.generate_routine_events(db, strategy_id, year)
    return {
        "message": f"成功生成 {len(events)} 个例行管理事件",
        "count": len(events),
        "year": year,
    }

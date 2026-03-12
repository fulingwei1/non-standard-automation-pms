# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - 战略审视与日历
"""

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
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
from app.services.strategy.review.strategy_reviews import _review_to_response
from app.services.strategy.review.calendar_events import _event_to_response

router = APIRouter()


# ============================================
# 战略审视
# ============================================


@router.post("/reviews", response_model=StrategyReviewResponse, status_code=status.HTTP_201_CREATED)
def create_strategy_review(
    data: StrategyReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    strategy = strategy_service.get_strategy(db, data.strategy_id)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="关联的战略不存在")

    review = strategy_service.create_strategy_review(db, data, current_user.id)
    return _review_to_response(review)


@router.get("/reviews", response_model=PageResponse[StrategyReviewResponse])
def list_strategy_reviews(
    strategy_id: int = Query(..., description="战略 ID"),
    review_type: Optional[str] = Query(None, description="审视类型筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
):
    items, total = strategy_service.list_strategy_reviews(
        db, strategy_id, review_type, pagination.offset, pagination.limit
    )

    responses = [_review_to_response(r) for r in items]

    return PageResponse(
        items=responses,
        total=total,
        skip=pagination.offset,
        limit=pagination.limit,
    )


@router.get("/reviews/latest/{strategy_id}", response_model=StrategyReviewResponse)
def get_latest_review(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    review = strategy_service.get_latest_review(db, strategy_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="没有审视记录")
    return review


@router.get("/reviews/{review_id}", response_model=StrategyReviewResponse)
def get_strategy_review(
    review_id: int,
    db: Session = Depends(deps.get_db),
):
    review = strategy_service.get_strategy_review(db, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审视记录不存在")
    return _review_to_response(review)


@router.put("/reviews/{review_id}", response_model=StrategyReviewResponse)
def update_strategy_review(
    review_id: int,
    data: StrategyReviewUpdate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    review = strategy_service.update_strategy_review(db, review_id, data)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审视记录不存在")
    return _review_to_response(review)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy_review(
    review_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    success = strategy_service.delete_strategy_review(db, review_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审视记录不存在")
    return None


# ============================================
# 健康度
# ============================================


@router.get("/health/{strategy_id}", response_model=HealthScoreResponse)
def get_health_score(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    return strategy_service.get_health_score_summary(db, strategy_id)


# ============================================
# 战略日历
# ============================================


@router.post(
    "/calendar/events",
    response_model=StrategyCalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_calendar_event(
    data: StrategyCalendarEventCreate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    event = strategy_service.create_calendar_event(db, data)
    return _event_to_response(event)


@router.get("/calendar/events", response_model=PageResponse[StrategyCalendarEventResponse])
def list_calendar_events(
    strategy_id: int = Query(..., description="战略 ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
):
    items, total = strategy_service.list_calendar_events(
        db, strategy_id, start_date, end_date, event_type, pagination.offset, pagination.limit
    )

    responses = [_event_to_response(e) for e in items]

    return PageResponse(
        items=responses,
        total=total,
        skip=pagination.offset,
        limit=pagination.limit,
    )


@router.get("/calendar/events/{event_id}", response_model=StrategyCalendarEventResponse)
def get_calendar_event(
    event_id: int,
    db: Session = Depends(deps.get_db),
):
    event = strategy_service.get_calendar_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="事件不存在")
    return _event_to_response(event)


@router.get("/calendar/month/{strategy_id}", response_model=CalendarMonthResponse)
def get_calendar_month(
    strategy_id: int,
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    db: Session = Depends(deps.get_db),
):
    return strategy_service.get_calendar_month(db, strategy_id, year, month)


@router.get("/calendar/year/{strategy_id}", response_model=CalendarYearResponse)
def get_calendar_year(
    strategy_id: int,
    year: int = Query(..., description="年份"),
    db: Session = Depends(deps.get_db),
):
    return strategy_service.get_calendar_year(db, strategy_id, year)


@router.put("/calendar/events/{event_id}", response_model=StrategyCalendarEventResponse)
def update_calendar_event(
    event_id: int,
    data: StrategyCalendarEventUpdate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    event = strategy_service.update_calendar_event(db, event_id, data)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="事件不存在")
    return _event_to_response(event)


@router.delete("/calendar/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_event(
    event_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    success = strategy_service.delete_calendar_event(db, event_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="事件不存在")
    return None


# ============================================
# 例行管理
# ============================================


@router.get("/routine/{strategy_id}", response_model=RoutineManagementCycleResponse)
def get_routine_management_cycle(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    return strategy_service.get_routine_management_cycle(db, strategy_id)


@router.post("/routine/{strategy_id}/generate-events", response_model=Dict[str, Any])
def generate_routine_events(
    strategy_id: int,
    year: int = Query(..., description="年份"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    events = strategy_service.generate_routine_events(db, strategy_id, year)
    return {
        "message": f"成功生成 {len(events)} 个例行管理事件",
        "count": len(events),
        "year": year,
    }

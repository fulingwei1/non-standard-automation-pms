# -*- coding: utf-8 -*-
"""
战略日历管理

提供战略日历事件的 CRUD 操作和日历视图
"""

import json
from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.strategy import StrategyCalendarEvent
from app.schemas.strategy import (
    CalendarMonthResponse,
    CalendarYearResponse,
    StrategyCalendarEventCreate,
    StrategyCalendarEventResponse,
    StrategyCalendarEventUpdate,
)

# ============================================
# 战略日历管理
# ============================================


def _safe_json_loads(val):
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


def _event_to_response(e: StrategyCalendarEvent) -> StrategyCalendarEventResponse:
    """将 Model 转为 Response"""
    participants = _safe_json_loads(e.participants)
    return StrategyCalendarEventResponse(
        id=e.id,
        strategy_id=e.strategy_id,
        event_type=e.event_type,
        name=e.name,
        description=e.description,
        year=e.year,
        month=e.month,
        quarter=e.quarter,
        scheduled_date=e.scheduled_date,
        actual_date=e.actual_date,
        deadline=e.deadline,
        is_recurring=e.is_recurring or False,
        recurrence_rule=e.recurrence_rule,
        owner_user_id=e.owner_user_id,
        participants=participants if isinstance(participants, list) else None,
        status=e.status or "PLANNED",
        review_id=e.review_id,
        reminder_days=e.reminder_days or 7,
        reminder_sent=bool(e.reminder_sent),
        is_active=e.is_active,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


def create_calendar_event(db: Session, data: StrategyCalendarEventCreate) -> StrategyCalendarEvent:
    event = StrategyCalendarEvent(
        strategy_id=data.strategy_id,
        event_type=data.event_type,
        name=data.name,
        description=data.description,
        year=data.year,
        month=data.month,
        quarter=data.quarter,
        scheduled_date=data.scheduled_date,
        deadline=data.deadline,
        is_recurring=data.is_recurring,
        recurrence_rule=data.recurrence_rule,
        owner_user_id=data.owner_user_id,
        participants=json.dumps(data.participants) if data.participants else None,
        reminder_days=data.reminder_days,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_calendar_event(db: Session, event_id: int) -> Optional[StrategyCalendarEvent]:
    return (
        db.query(StrategyCalendarEvent)
        .filter(StrategyCalendarEvent.id == event_id, StrategyCalendarEvent.is_active)
        .first()
    )


def list_calendar_events(
    db: Session,
    strategy_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[StrategyCalendarEvent], int]:
    query = db.query(StrategyCalendarEvent).filter(
        StrategyCalendarEvent.strategy_id == strategy_id, StrategyCalendarEvent.is_active
    )

    if start_date:
        query = query.filter(StrategyCalendarEvent.scheduled_date >= start_date)
    if end_date:
        query = query.filter(StrategyCalendarEvent.scheduled_date <= end_date)
    if event_type:
        query = query.filter(StrategyCalendarEvent.event_type == event_type)

    total = query.count()
    items = apply_pagination(query.order_by(StrategyCalendarEvent.scheduled_date), skip, limit).all()

    return items, total


def update_calendar_event(
    db: Session, event_id: int, data: StrategyCalendarEventUpdate
) -> Optional[StrategyCalendarEvent]:
    event = get_calendar_event(db, event_id)
    if not event:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # JSON 字段
    if "participants" in update_data and update_data["participants"] is not None:
        update_data["participants"] = json.dumps(update_data["participants"])

    for key, value in update_data.items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event


def delete_calendar_event(db: Session, event_id: int) -> bool:
    event = get_calendar_event(db, event_id)
    if not event:
        return False

    event.is_active = False
    db.commit()
    return True


def get_calendar_month(db: Session, strategy_id: int, year: int, month: int) -> CalendarMonthResponse:
    if month == 12:
        start_date_val = date(year, 12, 1)
        end_date_val = date(year + 1, 1, 1)
    else:
        start_date_val = date(year, month, 1)
        end_date_val = date(year, month + 1, 1)

    events, _ = list_calendar_events(db, strategy_id, start_date_val, end_date_val, limit=1000)
    event_responses = [_event_to_response(e) for e in events]

    return CalendarMonthResponse(
        year=year,
        month=month,
        events=event_responses,
    )


def get_calendar_year(db: Session, strategy_id: int, year: int) -> CalendarYearResponse:
    start_date_val = date(year, 1, 1)
    end_date_val = date(year, 12, 31)

    events, total = list_calendar_events(db, strategy_id, start_date_val, end_date_val, limit=10000)

    # 按月分组
    months_data = defaultdict(list)
    event_summary: Dict[str, int] = {}
    for e in events:
        if e.scheduled_date:
            months_data[e.scheduled_date.month].append(_event_to_response(e))
        event_type = e.event_type or "OTHER"
        event_summary[event_type] = event_summary.get(event_type, 0) + 1

    months = []
    for m in range(1, 13):
        months.append(CalendarMonthResponse(
            year=year,
            month=m,
            events=months_data.get(m, []),
        ))

    return CalendarYearResponse(
        year=year,
        months=months,
        event_summary=event_summary,
    )

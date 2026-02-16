# -*- coding: utf-8 -*-
"""
战略日历管理

提供战略日历事件的 CRUD 操作和日历视图
"""

"""
战略管理服务 - 战略审视与例行管理
"""

from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.strategy import StrategyCalendarEvent
from app.common.date_range import get_month_range_by_ym
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

def create_calendar_event(
    db: Session,
    data: StrategyCalendarEventCreate
) -> StrategyCalendarEvent:
    """
    创建日历事件

    Args:
        db: 数据库会话
        data: 创建数据

    Returns:
        StrategyCalendarEvent: 创建的日历事件
    """
    event = StrategyCalendarEvent(
        strategy_id=data.strategy_id,
        event_type=data.event_type,
        title=data.title,
        description=data.description,
        event_date=data.event_date,
        start_time=data.start_time,
        end_time=data.end_time,
        is_recurring=data.is_recurring,
        recurrence_pattern=data.recurrence_pattern,
        owner_user_id=data.owner_user_id,
        related_csf_id=data.related_csf_id,
        related_kpi_id=data.related_kpi_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_calendar_event(db: Session, event_id: int) -> Optional[StrategyCalendarEvent]:
    """
    获取日历事件

    Args:
        db: 数据库会话
        event_id: 事件 ID

    Returns:
        Optional[StrategyCalendarEvent]: 日历事件
    """
    return db.query(StrategyCalendarEvent).filter(
        StrategyCalendarEvent.id == event_id,
        StrategyCalendarEvent.is_active
    ).first()


def list_calendar_events(
    db: Session,
    strategy_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[StrategyCalendarEvent], int]:
    """
    获取日历事件列表

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        start_date: 开始日期
        end_date: 结束日期
        event_type: 事件类型
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (事件列表, 总数)
    """
    query = db.query(StrategyCalendarEvent).filter(
        StrategyCalendarEvent.strategy_id == strategy_id,
        StrategyCalendarEvent.is_active
    )

    if start_date:
        query = query.filter(StrategyCalendarEvent.event_date >= start_date)
    if end_date:
        query = query.filter(StrategyCalendarEvent.event_date <= end_date)
    if event_type:
        query = query.filter(StrategyCalendarEvent.event_type == event_type)

    total = query.count()
    items = apply_pagination(query.order_by(StrategyCalendarEvent.event_date), skip, limit).all()

    return items, total


def update_calendar_event(
    db: Session,
    event_id: int,
    data: StrategyCalendarEventUpdate
) -> Optional[StrategyCalendarEvent]:
    """
    更新日历事件

    Args:
        db: 数据库会话
        event_id: 事件 ID
        data: 更新数据

    Returns:
        Optional[StrategyCalendarEvent]: 更新后的事件
    """
    event = get_calendar_event(db, event_id)
    if not event:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event


def delete_calendar_event(db: Session, event_id: int) -> bool:
    """
    删除日历事件（软删除）

    Args:
        db: 数据库会话
        event_id: 事件 ID

    Returns:
        bool: 是否删除成功
    """
    event = get_calendar_event(db, event_id)
    if not event:
        return False

    event.is_active = False
    db.commit()
    return True


def get_calendar_month(
    db: Session,
    strategy_id: int,
    year: int,
    month: int
) -> CalendarMonthResponse:
    """
    获取月度日历

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        year: 年份
        month: 月份

    Returns:
        CalendarMonthResponse: 月度日历数据
    """
    start_date, end_date = get_month_range_by_ym(year, month)

    events, _ = list_calendar_events(
        db, strategy_id, start_date, end_date, limit=1000
    )

    # 按日期分组
    events_by_date: Dict[str, List[StrategyCalendarEventResponse]] = {}
    for e in events:
        date_key = e.event_date.isoformat()
        if date_key not in events_by_date:
            events_by_date[date_key] = []
        events_by_date[date_key].append(StrategyCalendarEventResponse(
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
        ))

    return CalendarMonthResponse(
        year=year,
        month=month,
        events_by_date=events_by_date,
        total_events=len(events),
    )


def get_calendar_year(
    db: Session,
    strategy_id: int,
    year: int
) -> CalendarYearResponse:
    """
    获取年度日历概览

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        year: 年份

    Returns:
        CalendarYearResponse: 年度日历概览
    """
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    events, total = list_calendar_events(
        db, strategy_id, start_date, end_date, limit=10000
    )

    # 按月份统计
    monthly_counts: Dict[int, int] = {i: 0 for i in range(1, 13)}
    for e in events:
        monthly_counts[e.event_date.month] += 1

    # 按类型统计
    type_counts: Dict[str, int] = {}
    for e in events:
        event_type = e.event_type or "OTHER"
        type_counts[event_type] = type_counts.get(event_type, 0) + 1

    return CalendarYearResponse(
        year=year,
        monthly_counts=monthly_counts,
        type_counts=type_counts,
        total_events=total,
    )



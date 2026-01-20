# -*- coding: utf-8 -*-
"""
战略管理服务 - 战略审视与例行管理
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.strategy import StrategyCalendarEvent, StrategyReview
from app.schemas.strategy import (
    CalendarMonthResponse,
    CalendarYearResponse,
    DimensionHealthDetail,
    HealthScoreResponse,
    RoutineManagementCycleItem,
    RoutineManagementCycleResponse,
    StrategyCalendarEventCreate,
    StrategyCalendarEventResponse,
    StrategyCalendarEventUpdate,
    StrategyReviewCreate,
    StrategyReviewResponse,
    StrategyReviewUpdate,
)


# ============================================
# 战略审视管理
# ============================================

def create_strategy_review(
    db: Session,
    data: StrategyReviewCreate,
    created_by: int
) -> StrategyReview:
    """
    创建战略审视记录

    Args:
        db: 数据库会话
        data: 创建数据
        created_by: 创建人 ID

    Returns:
        StrategyReview: 创建的审视记录
    """
    # 自动计算健康度评分
    from .health_calculator import (
        calculate_dimension_health,
        calculate_strategy_health,
    )

    overall_health = calculate_strategy_health(db, data.strategy_id)

    financial_health = calculate_dimension_health(db, data.strategy_id, "FINANCIAL")
    customer_health = calculate_dimension_health(db, data.strategy_id, "CUSTOMER")
    internal_health = calculate_dimension_health(db, data.strategy_id, "INTERNAL")
    learning_health = calculate_dimension_health(db, data.strategy_id, "LEARNING")

    review = StrategyReview(
        strategy_id=data.strategy_id,
        review_date=data.review_date or date.today(),
        review_period=data.review_period,
        review_type=data.review_type,
        health_score=overall_health,
        financial_score=financial_health.get("score"),
        customer_score=customer_health.get("score"),
        internal_score=internal_health.get("score"),
        learning_score=learning_health.get("score"),
        summary=data.summary,
        achievements=data.achievements,
        issues=data.issues,
        action_items=data.action_items,
        next_steps=data.next_steps,
        created_by=created_by,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_strategy_review(db: Session, review_id: int) -> Optional[StrategyReview]:
    """
    获取战略审视记录

    Args:
        db: 数据库会话
        review_id: 审视记录 ID

    Returns:
        Optional[StrategyReview]: 审视记录
    """
    return db.query(StrategyReview).filter(
        StrategyReview.id == review_id,
        StrategyReview.is_active == True
    ).first()


def list_strategy_reviews(
    db: Session,
    strategy_id: int,
    review_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> tuple[List[StrategyReview], int]:
    """
    获取战略审视记录列表

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        review_type: 审视类型筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (审视记录列表, 总数)
    """
    query = db.query(StrategyReview).filter(
        StrategyReview.strategy_id == strategy_id,
        StrategyReview.is_active == True
    )

    if review_type:
        query = query.filter(StrategyReview.review_type == review_type)

    total = query.count()
    items = query.order_by(desc(StrategyReview.review_date)).offset(skip).limit(limit).all()

    return items, total


def update_strategy_review(
    db: Session,
    review_id: int,
    data: StrategyReviewUpdate
) -> Optional[StrategyReview]:
    """
    更新战略审视记录

    Args:
        db: 数据库会话
        review_id: 审视记录 ID
        data: 更新数据

    Returns:
        Optional[StrategyReview]: 更新后的审视记录
    """
    review = get_strategy_review(db, review_id)
    if not review:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)
    return review


def delete_strategy_review(db: Session, review_id: int) -> bool:
    """
    删除战略审视记录（软删除）

    Args:
        db: 数据库会话
        review_id: 审视记录 ID

    Returns:
        bool: 是否删除成功
    """
    review = get_strategy_review(db, review_id)
    if not review:
        return False

    review.is_active = False
    db.commit()
    return True


def get_latest_review(db: Session, strategy_id: int) -> Optional[StrategyReviewResponse]:
    """
    获取最新的战略审视记录

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        Optional[StrategyReviewResponse]: 最新审视记录
    """
    review = db.query(StrategyReview).filter(
        StrategyReview.strategy_id == strategy_id,
        StrategyReview.is_active == True
    ).order_by(desc(StrategyReview.review_date)).first()

    if not review:
        return None

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


# ============================================
# 健康度汇总
# ============================================

def get_health_score_summary(db: Session, strategy_id: int) -> HealthScoreResponse:
    """
    获取健康度汇总

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        HealthScoreResponse: 健康度汇总
    """
    from .health_calculator import (
        calculate_strategy_health,
        get_dimension_health_details,
        get_health_level,
        get_health_trend,
    )

    overall_score = calculate_strategy_health(db, strategy_id)
    overall_level = get_health_level(overall_score) if overall_score else None

    # 获取各维度详情
    dimension_details = get_dimension_health_details(db, strategy_id)
    dimensions = [
        DimensionHealthDetail(
            dimension=d["dimension"],
            dimension_name=d["dimension_name"],
            score=d["score"],
            health_level=d["health_level"],
            csf_count=d["csf_count"],
            kpi_count=d["kpi_count"],
            kpi_completion_rate=d["kpi_completion_rate"],
            kpi_on_track=d.get("kpi_on_track", 0),
            kpi_at_risk=d.get("kpi_at_risk", 0),
            kpi_off_track=d.get("kpi_off_track", 0),
        )
        for d in dimension_details
    ]

    # 获取趋势数据
    trend_data = get_health_trend(db, strategy_id)

    return HealthScoreResponse(
        strategy_id=strategy_id,
        overall_score=overall_score,
        overall_level=overall_level,
        dimensions=dimensions,
        trend=trend_data,
        calculated_at=datetime.now(),
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
        StrategyCalendarEvent.is_active == True
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
        StrategyCalendarEvent.is_active == True
    )

    if start_date:
        query = query.filter(StrategyCalendarEvent.event_date >= start_date)
    if end_date:
        query = query.filter(StrategyCalendarEvent.event_date <= end_date)
    if event_type:
        query = query.filter(StrategyCalendarEvent.event_type == event_type)

    total = query.count()
    items = query.order_by(StrategyCalendarEvent.event_date).offset(skip).limit(limit).all()

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
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

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


# ============================================
# 例行管理周期
# ============================================

def get_routine_management_cycle(
    db: Session,
    strategy_id: int
) -> RoutineManagementCycleResponse:
    """
    获取例行管理周期配置

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        RoutineManagementCycleResponse: 例行管理周期
    """
    # 华为 BEM 标准例行管理周期
    cycles = [
        RoutineManagementCycleItem(
            cycle_type="DAILY",
            cycle_name="日例会",
            frequency="DAILY",
            description="每日站会，快速同步进展和问题",
            typical_duration=15,
            participants=["项目经理", "团队成员"],
        ),
        RoutineManagementCycleItem(
            cycle_type="WEEKLY",
            cycle_name="周例会",
            frequency="WEEKLY",
            description="每周回顾 KPI 进展，协调资源",
            typical_duration=60,
            participants=["部门负责人", "KPI 责任人"],
        ),
        RoutineManagementCycleItem(
            cycle_type="MONTHLY",
            cycle_name="月度经营分析会",
            frequency="MONTHLY",
            description="月度经营数据分析，识别风险和机会",
            typical_duration=120,
            participants=["高管", "部门负责人"],
        ),
        RoutineManagementCycleItem(
            cycle_type="QUARTERLY",
            cycle_name="季度战略审视会",
            frequency="QUARTERLY",
            description="季度战略执行回顾，调整策略",
            typical_duration=240,
            participants=["CEO", "高管团队", "部门负责人"],
        ),
        RoutineManagementCycleItem(
            cycle_type="YEARLY",
            cycle_name="年度战略规划会",
            frequency="YEARLY",
            description="年度战略制定与分解",
            typical_duration=480,
            participants=["董事会", "CEO", "高管团队"],
        ),
    ]

    return RoutineManagementCycleResponse(
        strategy_id=strategy_id,
        cycles=cycles,
    )


def generate_routine_events(
    db: Session,
    strategy_id: int,
    year: int
) -> List[StrategyCalendarEvent]:
    """
    生成年度例行管理事件

    Args:
        db: 数据库会话
        strategy_id: 战略 ID
        year: 年份

    Returns:
        List[StrategyCalendarEvent]: 生成的事件列表
    """
    events = []

    # 生成月度经营分析会（每月最后一个工作日）
    for month in range(1, 13):
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        # 调整到工作日
        while last_day.weekday() >= 5:  # 周六或周日
            last_day -= timedelta(days=1)

        event = StrategyCalendarEvent(
            strategy_id=strategy_id,
            event_type="MONTHLY_REVIEW",
            title=f"{year}年{month}月经营分析会",
            description="月度经营数据分析，识别风险和机会",
            event_date=last_day,
            is_recurring=True,
            recurrence_pattern="MONTHLY",
        )
        db.add(event)
        events.append(event)

    # 生成季度战略审视会
    for quarter in range(1, 5):
        # 每季度最后一个月的第三周
        month = quarter * 3
        review_date = date(year, month, 21)
        while review_date.weekday() >= 5:
            review_date -= timedelta(days=1)

        event = StrategyCalendarEvent(
            strategy_id=strategy_id,
            event_type="QUARTERLY_REVIEW",
            title=f"{year}年Q{quarter}战略审视会",
            description="季度战略执行回顾，调整策略",
            event_date=review_date,
            is_recurring=True,
            recurrence_pattern="QUARTERLY",
        )
        db.add(event)
        events.append(event)

    # 生成年度战略规划会（12月第一周）
    annual_date = date(year, 12, 7)
    while annual_date.weekday() >= 5:
        annual_date -= timedelta(days=1)

    annual_event = StrategyCalendarEvent(
        strategy_id=strategy_id,
        event_type="YEARLY_PLANNING",
        title=f"{year + 1}年度战略规划会",
        description="年度战略制定与分解",
        event_date=annual_date,
        is_recurring=True,
        recurrence_pattern="YEARLY",
    )
    db.add(annual_event)
    events.append(annual_event)

    db.commit()
    return events

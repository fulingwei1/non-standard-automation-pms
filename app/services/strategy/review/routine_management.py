# -*- coding: utf-8 -*-
"""
例行管理周期

提供例行管理周期配置和事件生成
"""

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

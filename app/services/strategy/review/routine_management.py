# -*- coding: utf-8 -*-
"""
例行管理周期

提供例行管理周期配置和事件生成
"""

"""
战略管理服务 - 战略审视与例行管理
"""

from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.common.date_range import get_month_range_by_ym
from app.models.strategy import StrategyCalendarEvent
from app.schemas.strategy import (
    RoutineManagementCycleItem,
    RoutineManagementCycleResponse,
)

# ============================================
# 例行管理周期
# ============================================


def get_routine_management_cycle(db: Session, strategy_id: int) -> RoutineManagementCycleResponse:
    """
    获取例行管理周期配置

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        RoutineManagementCycleResponse: 例行管理周期
    """
    # 华为 BEM 标准例行管理周期
    monthly_events = [
        RoutineManagementCycleItem(
            event_type="DAILY",
            event_type_name="日例会",
            frequency="DAILY",
            typical_timing="每日",
            participants=["项目经理", "团队成员"],
            key_activities=["同步进展", "识别阻塞"],
        ),
        RoutineManagementCycleItem(
            event_type="WEEKLY",
            event_type_name="周例会",
            frequency="WEEKLY",
            typical_timing="每周",
            participants=["部门负责人", "KPI 责任人"],
            key_activities=["回顾 KPI 进展", "协调资源"],
        ),
        RoutineManagementCycleItem(
            event_type="MONTHLY_REVIEW",
            event_type_name="月度经营分析会",
            frequency="MONTHLY",
            typical_timing="每月第一周",
            participants=["高管", "部门负责人"],
            key_activities=["经营数据分析", "识别风险和机会"],
        ),
    ]
    quarterly_events = [
        RoutineManagementCycleItem(
            event_type="QUARTERLY_REVIEW",
            event_type_name="季度战略审视会",
            frequency="QUARTERLY",
            typical_timing="每季度末",
            participants=["CEO", "高管团队", "部门负责人"],
            key_activities=["战略执行回顾", "策略调整"],
        ),
    ]
    annual_events = [
        RoutineManagementCycleItem(
            event_type="ANNUAL_PLANNING",
            event_type_name="年度战略规划会",
            frequency="YEARLY",
            typical_timing="每年第四季度",
            participants=["董事会", "CEO", "高管团队"],
            key_activities=["年度战略制定", "战略目标分解"],
        ),
    ]

    return RoutineManagementCycleResponse(
        strategy_id=strategy_id,
        year=date.today().year,
        annual_events=annual_events,
        quarterly_events=quarterly_events,
        monthly_events=monthly_events,
    )


def generate_routine_events(
    db: Session, strategy_id: int, year: int
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
        _, last_day = get_month_range_by_ym(year, month)

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

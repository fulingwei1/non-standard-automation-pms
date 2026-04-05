# -*- coding: utf-8 -*-
"""
智能跟进提醒 API

提供业务员跟进提醒接口。
"""

import logging
from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.follow_up_reminder_service import (
    FollowUpReminder,
    FollowUpReminderService,
    ReminderPriority,
    ReminderType,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _serialize_reminder(reminder: FollowUpReminder) -> dict:
    return {
        "type": reminder.type.value,
        "priority": reminder.priority.value,
        "entity_type": reminder.entity_type,
        "entity_id": reminder.entity_id,
        "entity_code": reminder.entity_code,
        "entity_name": reminder.entity_name,
        "customer_name": reminder.customer_name,
        "message": reminder.message,
        "suggestion": reminder.suggestion,
        "days_overdue": reminder.days_overdue,
        "last_follow_up_at": reminder.last_follow_up_at.isoformat()
        if reminder.last_follow_up_at
        else None,
        "next_action_at": reminder.next_action_at.isoformat() if reminder.next_action_at else None,
        "est_amount": reminder.est_amount,
    }


@router.get("/reminders", response_model=ResponseModel)
def get_follow_up_reminders(
    db: Session = Depends(deps.get_db),
    types: Optional[List[str]] = Query(
        None,
        description="提醒类型过滤: overdue_action, no_follow_up, quote_expiring, high_value_idle",
    ),
    priority: Optional[str] = Query(
        None,
        description="优先级过滤: urgent, high, medium, low",
    ),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取当前用户的智能跟进提醒

    系统自动分析用户负责的线索、商机、报价，生成跟进提醒：
    - overdue_action: 计划行动已过期
    - no_follow_up: 长时间未跟进
    - quote_expiring: 报价即将过期
    - high_value_idle: 高价值客户闲置

    返回按优先级排序的提醒列表，每条提醒包含具体的跟进建议。
    """
    type_filters = None
    if types:
        type_filters = []
        for reminder_type in types:
            try:
                type_filters.append(ReminderType(reminder_type))
            except ValueError:
                pass

    service = FollowUpReminderService(db)
    reminders = service.get_reminders_for_user(
        user_id=current_user.id,
        include_types=type_filters,
        limit=limit,
    )

    if priority:
        try:
            priority_filter = ReminderPriority(priority)
            reminders = [reminder for reminder in reminders if reminder.priority == priority_filter]
        except ValueError:
            pass

    items = [_serialize_reminder(reminder) for reminder in reminders]

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": items,
            "total": len(items),
        },
    )


@router.get("/reminders/action-board", response_model=ResponseModel)
def get_follow_up_action_board(
    db: Session = Depends(deps.get_db),
    window_days: int = Query(3, ge=0, le=30, description="临近提醒窗口（天）"),
    limit: int = Query(50, ge=1, le=200, description="每个分组返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取自动跟进行动看板（超期 + 临近）"""
    service = FollowUpReminderService(db)
    digest = service.get_due_action_digest(
        user_id=current_user.id,
        window_days=window_days,
        limit=limit,
    )

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "generated_at": digest["generated_at"],
            "window_days": digest["window_days"],
            "overdue_count": digest["overdue_count"],
            "upcoming_count": digest["upcoming_count"],
            "high_priority_count": digest["high_priority_count"],
            "total": digest["total"],
            "overdue": [_serialize_reminder(reminder) for reminder in digest["overdue"]],
            "upcoming": [_serialize_reminder(reminder) for reminder in digest["upcoming"]],
        },
    )


@router.get("/reports/weekly", response_model=ResponseModel)
def get_weekly_follow_up_report(
    db: Session = Depends(deps.get_db),
    week_start: Optional[date] = Query(None, description="周起始日期，默认本周一"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取跟进周报汇总（跟进次数、超期数、转化率）"""
    service = FollowUpReminderService(db)
    report = service.get_weekly_follow_up_report(
        user_id=current_user.id,
        week_start=week_start,
    )

    return ResponseModel(
        code=200,
        message="获取成功",
        data=report,
    )


@router.get("/reminders/summary", response_model=ResponseModel)
def get_reminders_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取跟进提醒摘要

    返回各类型和优先级的统计数据，以及紧急待处理项。
    适合在首页或仪表盘展示。
    """
    service = FollowUpReminderService(db)
    summary = service.get_summary(current_user.id)

    return ResponseModel(
        code=200,
        message="获取成功",
        data=summary,
    )


@router.get("/reminders/urgent", response_model=ResponseModel)
def get_urgent_reminders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取紧急跟进提醒（今日必须处理）

    仅返回优先级为 urgent 的提醒，适合早晨查看当日任务。
    """
    service = FollowUpReminderService(db)
    reminders = service.get_reminders_for_user(
        user_id=current_user.id,
        limit=20,
    )

    urgent_reminders = [reminder for reminder in reminders if reminder.priority == ReminderPriority.URGENT]
    items = [_serialize_reminder(reminder) for reminder in urgent_reminders]

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": items,
            "count": len(items),
            "tip": "这些是今天必须处理的紧急事项" if items else "今日暂无紧急事项 👍",
        },
    )

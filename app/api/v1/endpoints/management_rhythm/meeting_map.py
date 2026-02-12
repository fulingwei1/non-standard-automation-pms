# -*- coding: utf-8 -*-
"""
会议地图 - 自动生成
从 management_rhythm.py 拆分
"""

# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from datetime import date, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import (
    ActionItemStatus,
)
from app.models.management_rhythm import (
    MeetingActionItem,
    StrategicMeeting,
)
from app.models.user import User
from app.schemas.management_rhythm import (
    MeetingCalendarResponse,
    MeetingMapItem,
    MeetingMapResponse,
    MeetingStatisticsResponse,
)

from .permission_utils import (
    check_rhythm_level_permission,
    filter_meetings_by_permission,
)

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/management-rhythm/meeting-map",
    tags=["meeting_map"]
)

# 共 3 个路由

# ==================== 会议地图 ====================

@router.get("/meeting-map", response_model=MeetingMapResponse)
def read_meeting_map(
    rhythm_level: Optional[str] = Query(None, description="会议层级筛选"),
    cycle_type: Optional[str] = Query(None, description="周期类型筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议地图（按周期和层级组织）
    """
    query = db.query(StrategicMeeting)

    # 权限过滤
    query = filter_meetings_by_permission(db, query, current_user)

    # 如果指定了层级，检查权限
    if rhythm_level and not check_rhythm_level_permission(current_user, rhythm_level):
        raise HTTPException(status_code=403, detail="您没有权限访问该层级的会议")

    if rhythm_level:
        query = query.filter(StrategicMeeting.rhythm_level == rhythm_level)

    if cycle_type:
        query = query.filter(StrategicMeeting.cycle_type == cycle_type)

    if start_date:
        query = query.filter(StrategicMeeting.meeting_date >= start_date)

    if end_date:
        query = query.filter(StrategicMeeting.meeting_date <= end_date)

    meetings = query.order_by(StrategicMeeting.meeting_date).all()

    items = []
    by_level = {}
    by_cycle = {}

    for meeting in meetings:
        # 统计行动项
        action_items_count = db.query(MeetingActionItem).filter(MeetingActionItem.meeting_id == meeting.id).count()
        completed_count = db.query(MeetingActionItem).filter(
            and_(
                MeetingActionItem.meeting_id == meeting.id,
                MeetingActionItem.status == ActionItemStatus.COMPLETED.value
            )
        ).count()

        item = MeetingMapItem(
            id=meeting.id,
            rhythm_level=meeting.rhythm_level,
            cycle_type=meeting.cycle_type,
            meeting_name=meeting.meeting_name,
            meeting_date=meeting.meeting_date,
            start_time=meeting.start_time,
            status=meeting.status,
            organizer_name=meeting.organizer_name,
            action_items_count=action_items_count,
            completed_action_items_count=completed_count,
        )

        items.append(item)

        # 按层级分组
        if meeting.rhythm_level not in by_level:
            by_level[meeting.rhythm_level] = []
        by_level[meeting.rhythm_level].append(item)

        # 按周期分组
        if meeting.cycle_type not in by_cycle:
            by_cycle[meeting.cycle_type] = []
        by_cycle[meeting.cycle_type].append(item)

    return MeetingMapResponse(
        items=items,
        by_level=by_level,
        by_cycle=by_cycle,
    )


@router.get("/meeting-map/calendar", response_model=List[MeetingCalendarResponse])
def read_meeting_calendar(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    rhythm_level: Optional[str] = Query(None, description="会议层级筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议日历视图
    """
    query = db.query(StrategicMeeting).filter(
        and_(
            StrategicMeeting.meeting_date >= start_date,
            StrategicMeeting.meeting_date <= end_date
        )
    )

    if rhythm_level:
        query = query.filter(StrategicMeeting.rhythm_level == rhythm_level)

    meetings = query.order_by(StrategicMeeting.meeting_date).all()

    # 按日期分组
    calendar_map = {}
    for meeting in meetings:
        meeting_date = meeting.meeting_date

        if meeting_date not in calendar_map:
            calendar_map[meeting_date] = []

        # 统计行动项
        action_items_count = db.query(MeetingActionItem).filter(MeetingActionItem.meeting_id == meeting.id).count()
        completed_count = db.query(MeetingActionItem).filter(
            and_(
                MeetingActionItem.meeting_id == meeting.id,
                MeetingActionItem.status == ActionItemStatus.COMPLETED.value
            )
        ).count()

        calendar_map[meeting_date].append(MeetingMapItem(
            id=meeting.id,
            rhythm_level=meeting.rhythm_level,
            cycle_type=meeting.cycle_type,
            meeting_name=meeting.meeting_name,
            meeting_date=meeting.meeting_date,
            start_time=meeting.start_time,
            status=meeting.status,
            organizer_name=meeting.organizer_name,
            action_items_count=action_items_count,
            completed_action_items_count=completed_count,
        ))

    # 转换为列表
    result = []
    current_date = start_date
    while current_date <= end_date:
        if current_date in calendar_map:
            result.append(MeetingCalendarResponse(
                date=current_date,
                meetings=calendar_map[current_date],
            ))
        current_date += timedelta(days=1)

    return result


@router.get("/meeting-map/statistics", response_model=MeetingStatisticsResponse)
def read_meeting_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    rhythm_level: Optional[str] = Query(None, description="会议层级筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议统计（参与率、完成率等）
    """
    query = db.query(StrategicMeeting)

    if rhythm_level:
        query = query.filter(StrategicMeeting.rhythm_level == rhythm_level)

    if start_date:
        query = query.filter(StrategicMeeting.meeting_date >= start_date)

    if end_date:
        query = query.filter(StrategicMeeting.meeting_date <= end_date)

    meetings = query.all()

    total_meetings = len(meetings)
    completed_meetings = len([m for m in meetings if m.status == "COMPLETED"])
    scheduled_meetings = len([m for m in meetings if m.status == "SCHEDULED"])
    cancelled_meetings = len([m for m in meetings if m.status == "CANCELLED"])

    # 统计行动项
    meeting_ids = [m.id for m in meetings]
    if meeting_ids:
        total_action_items = db.query(MeetingActionItem).filter(
            MeetingActionItem.meeting_id.in_(meeting_ids)
        ).count()

        completed_action_items = db.query(MeetingActionItem).filter(
            and_(
                MeetingActionItem.meeting_id.in_(meeting_ids),
                MeetingActionItem.status == ActionItemStatus.COMPLETED.value
            )
        ).count()

        overdue_action_items = db.query(MeetingActionItem).filter(
            and_(
                MeetingActionItem.meeting_id.in_(meeting_ids),
                MeetingActionItem.status == ActionItemStatus.OVERDUE.value
            )
        ).count()
    else:
        total_action_items = 0
        completed_action_items = 0
        overdue_action_items = 0

    completion_rate = (completed_action_items / total_action_items * 100) if total_action_items > 0 else 0.0

    # 按层级统计
    by_level = {}
    for meeting in meetings:
        level = meeting.rhythm_level
        by_level[level] = by_level.get(level, 0) + 1

    # 按周期统计
    by_cycle = {}
    for meeting in meetings:
        cycle = meeting.cycle_type
        by_cycle[cycle] = by_cycle.get(cycle, 0) + 1

    return MeetingStatisticsResponse(
        total_meetings=total_meetings,
        completed_meetings=completed_meetings,
        scheduled_meetings=scheduled_meetings,
        cancelled_meetings=cancelled_meetings,
        total_action_items=total_action_items,
        completed_action_items=completed_action_items,
        overdue_action_items=overdue_action_items,
        completion_rate=completion_rate,
        by_level=by_level,
        by_cycle=by_cycle,
    )



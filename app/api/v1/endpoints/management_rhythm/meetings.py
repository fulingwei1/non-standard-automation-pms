# -*- coding: utf-8 -*-
"""
战略会议 - 自动生成
从 management_rhythm.py 拆分
"""

# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.models.enums import (
    ActionItemStatus,
)
from app.models.management_rhythm import (
    MeetingActionItem,
    StrategicMeeting,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.management_rhythm import (
    StrategicMeetingCreate,
    StrategicMeetingMinutesRequest,
    StrategicMeetingResponse,
    StrategicMeetingUpdate,
)

from .permission_utils import (
    check_rhythm_level_permission,
    filter_meetings_by_permission,
)

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/management-rhythm/meetings",
    tags=["meetings"]
)

# 共 5 个路由

# ==================== 战略会议 ====================

@router.get("/strategic-meetings", response_model=PaginatedResponse)
def read_strategic_meetings(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    rhythm_level: Optional[str] = Query(None, description="会议层级筛选"),
    cycle_type: Optional[str] = Query(None, description="周期类型筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    meeting_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（会议名称）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    战略会议列表
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

    if project_id:
        query = query.filter(StrategicMeeting.project_id == project_id)

    if meeting_status:
        query = query.filter(StrategicMeeting.status == meeting_status)

    query = apply_keyword_filter(query, StrategicMeeting, keyword, ["meeting_name"])

    total = query.count()

    # 统计行动项数量
    meetings = query.order_by(desc(StrategicMeeting.meeting_date), desc(StrategicMeeting.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for meeting in meetings:
        # 统计行动项
        action_items_count = db.query(MeetingActionItem).filter(MeetingActionItem.meeting_id == meeting.id).count()
        completed_count = db.query(MeetingActionItem).filter(
            and_(
                MeetingActionItem.meeting_id == meeting.id,
                MeetingActionItem.status == ActionItemStatus.COMPLETED.value
            )
        ).count()

        items.append(StrategicMeetingResponse(
            id=meeting.id,
            project_id=meeting.project_id,
            rhythm_config_id=meeting.rhythm_config_id,
            rhythm_level=meeting.rhythm_level,
            cycle_type=meeting.cycle_type,
            meeting_name=meeting.meeting_name,
            meeting_type=meeting.meeting_type,
            meeting_date=meeting.meeting_date,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            location=meeting.location,
            organizer_id=meeting.organizer_id,
            organizer_name=meeting.organizer_name,
            attendees=meeting.attendees if meeting.attendees else [],
            agenda=meeting.agenda,
            minutes=meeting.minutes,
            decisions=meeting.decisions,
            strategic_context=meeting.strategic_context if meeting.strategic_context else {},
            strategic_structure=meeting.strategic_structure if meeting.strategic_structure else {},
            key_decisions=meeting.key_decisions if meeting.key_decisions else [],
            resource_allocation=meeting.resource_allocation if meeting.resource_allocation else {},
            metrics_snapshot=meeting.metrics_snapshot if meeting.metrics_snapshot else {},
            attachments=meeting.attachments if meeting.attachments else [],
            status=meeting.status,
            created_by=meeting.created_by,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
            action_items_count=action_items_count,
            completed_action_items_count=completed_count,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/strategic-meetings", response_model=StrategicMeetingResponse, status_code=status.HTTP_201_CREATED)
def create_strategic_meeting(
    meeting_data: StrategicMeetingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建战略会议
    """
    meeting = StrategicMeeting(
        project_id=meeting_data.project_id,
        rhythm_config_id=meeting_data.rhythm_config_id,
        rhythm_level=meeting_data.rhythm_level,
        cycle_type=meeting_data.cycle_type,
        meeting_name=meeting_data.meeting_name,
        meeting_type=meeting_data.meeting_type,
        meeting_date=meeting_data.meeting_date,
        start_time=meeting_data.start_time,
        end_time=meeting_data.end_time,
        location=meeting_data.location,
        organizer_id=meeting_data.organizer_id or current_user.id,
        organizer_name=meeting_data.organizer_name,
        attendees=meeting_data.attendees,
        agenda=meeting_data.agenda,
        strategic_context=meeting_data.strategic_context,
        strategic_structure=meeting_data.strategic_structure,
        key_decisions=meeting_data.key_decisions,
        resource_allocation=meeting_data.resource_allocation,
        created_by=current_user.id,
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return StrategicMeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        rhythm_config_id=meeting.rhythm_config_id,
        rhythm_level=meeting.rhythm_level,
        cycle_type=meeting.cycle_type,
        meeting_name=meeting.meeting_name,
        meeting_type=meeting.meeting_type,
        meeting_date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        location=meeting.location,
        organizer_id=meeting.organizer_id,
        organizer_name=meeting.organizer_name,
        attendees=meeting.attendees if meeting.attendees else [],
        agenda=meeting.agenda,
        minutes=meeting.minutes,
        decisions=meeting.decisions,
        strategic_context=meeting.strategic_context if meeting.strategic_context else {},
        strategic_structure=meeting.strategic_structure if meeting.strategic_structure else {},
        key_decisions=meeting.key_decisions if meeting.key_decisions else [],
        resource_allocation=meeting.resource_allocation if meeting.resource_allocation else {},
        metrics_snapshot=meeting.metrics_snapshot if meeting.metrics_snapshot else {},
        attachments=meeting.attachments if meeting.attachments else [],
        status=meeting.status,
        created_by=meeting.created_by,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        action_items_count=0,
        completed_action_items_count=0,
    )


@router.get("/strategic-meetings/{meeting_id}", response_model=StrategicMeetingResponse)
def read_strategic_meeting(
    meeting_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取战略会议详情
    """
    meeting = db.query(StrategicMeeting).filter(StrategicMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    # 权限检查
    if not check_rhythm_level_permission(current_user, meeting.rhythm_level):
        raise HTTPException(status_code=403, detail="您没有权限访问该会议")

    # 统计行动项
    action_items_count = db.query(MeetingActionItem).filter(MeetingActionItem.meeting_id == meeting.id).count()
    completed_count = db.query(MeetingActionItem).filter(
        and_(
            MeetingActionItem.meeting_id == meeting.id,
            MeetingActionItem.status == ActionItemStatus.COMPLETED.value
        )
    ).count()

    return StrategicMeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        rhythm_config_id=meeting.rhythm_config_id,
        rhythm_level=meeting.rhythm_level,
        cycle_type=meeting.cycle_type,
        meeting_name=meeting.meeting_name,
        meeting_type=meeting.meeting_type,
        meeting_date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        location=meeting.location,
        organizer_id=meeting.organizer_id,
        organizer_name=meeting.organizer_name,
        attendees=meeting.attendees if meeting.attendees else [],
        agenda=meeting.agenda,
        minutes=meeting.minutes,
        decisions=meeting.decisions,
        strategic_context=meeting.strategic_context if meeting.strategic_context else {},
        strategic_structure=meeting.strategic_structure if meeting.strategic_structure else {},
        key_decisions=meeting.key_decisions if meeting.key_decisions else [],
        resource_allocation=meeting.resource_allocation if meeting.resource_allocation else {},
        metrics_snapshot=meeting.metrics_snapshot if meeting.metrics_snapshot else {},
        attachments=meeting.attachments if meeting.attachments else [],
        status=meeting.status,
        created_by=meeting.created_by,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        action_items_count=action_items_count,
        completed_action_items_count=completed_count,
    )


@router.put("/strategic-meetings/{meeting_id}", response_model=StrategicMeetingResponse)
def update_strategic_meeting(
    meeting_id: int,
    meeting_data: StrategicMeetingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新战略会议
    """
    meeting = db.query(StrategicMeeting).filter(StrategicMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    update_data = meeting_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)

    db.commit()
    db.refresh(meeting)

    # 统计行动项
    action_items_count = db.query(MeetingActionItem).filter(MeetingActionItem.meeting_id == meeting.id).count()
    completed_count = db.query(MeetingActionItem).filter(
        and_(
            MeetingActionItem.meeting_id == meeting.id,
            MeetingActionItem.status == ActionItemStatus.COMPLETED.value
        )
    ).count()

    return StrategicMeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        rhythm_config_id=meeting.rhythm_config_id,
        rhythm_level=meeting.rhythm_level,
        cycle_type=meeting.cycle_type,
        meeting_name=meeting.meeting_name,
        meeting_type=meeting.meeting_type,
        meeting_date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        location=meeting.location,
        organizer_id=meeting.organizer_id,
        organizer_name=meeting.organizer_name,
        attendees=meeting.attendees if meeting.attendees else [],
        agenda=meeting.agenda,
        minutes=meeting.minutes,
        decisions=meeting.decisions,
        strategic_context=meeting.strategic_context if meeting.strategic_context else {},
        strategic_structure=meeting.strategic_structure if meeting.strategic_structure else {},
        key_decisions=meeting.key_decisions if meeting.key_decisions else [],
        resource_allocation=meeting.resource_allocation if meeting.resource_allocation else {},
        metrics_snapshot=meeting.metrics_snapshot if meeting.metrics_snapshot else {},
        attachments=meeting.attachments if meeting.attachments else [],
        status=meeting.status,
        created_by=meeting.created_by,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        action_items_count=action_items_count,
        completed_action_items_count=completed_count,
    )


@router.put("/strategic-meetings/{meeting_id}/minutes", response_model=StrategicMeetingResponse)
def update_meeting_minutes(
    meeting_id: int,
    minutes_data: StrategicMeetingMinutesRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新会议纪要
    """
    meeting = db.query(StrategicMeeting).filter(StrategicMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    meeting.minutes = minutes_data.minutes
    if minutes_data.decisions:
        meeting.decisions = minutes_data.decisions
    if minutes_data.strategic_structure:
        meeting.strategic_structure = minutes_data.strategic_structure
    if minutes_data.key_decisions:
        meeting.key_decisions = minutes_data.key_decisions
    if minutes_data.metrics_snapshot:
        meeting.metrics_snapshot = minutes_data.metrics_snapshot

    db.commit()
    db.refresh(meeting)

    # 统计行动项
    action_items_count = db.query(MeetingActionItem).filter(MeetingActionItem.meeting_id == meeting.id).count()
    completed_count = db.query(MeetingActionItem).filter(
        and_(
            MeetingActionItem.meeting_id == meeting.id,
            MeetingActionItem.status == ActionItemStatus.COMPLETED.value
        )
    ).count()

    return StrategicMeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        rhythm_config_id=meeting.rhythm_config_id,
        rhythm_level=meeting.rhythm_level,
        cycle_type=meeting.cycle_type,
        meeting_name=meeting.meeting_name,
        meeting_type=meeting.meeting_type,
        meeting_date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        location=meeting.location,
        organizer_id=meeting.organizer_id,
        organizer_name=meeting.organizer_name,
        attendees=meeting.attendees if meeting.attendees else [],
        agenda=meeting.agenda,
        minutes=meeting.minutes,
        decisions=meeting.decisions,
        strategic_context=meeting.strategic_context if meeting.strategic_context else {},
        strategic_structure=meeting.strategic_structure if meeting.strategic_structure else {},
        key_decisions=meeting.key_decisions if meeting.key_decisions else [],
        resource_allocation=meeting.resource_allocation if meeting.resource_allocation else {},
        metrics_snapshot=meeting.metrics_snapshot if meeting.metrics_snapshot else {},
        attachments=meeting.attachments if meeting.attachments else [],
        status=meeting.status,
        created_by=meeting.created_by,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        action_items_count=action_items_count,
        completed_action_items_count=completed_count,
    )



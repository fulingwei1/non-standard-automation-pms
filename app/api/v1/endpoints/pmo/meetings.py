# -*- coding: utf-8 -*-
"""
会议管理 - 自动生成
从 pmo.py 拆分
"""

# -*- coding: utf-8 -*-
"""
PMO 项目管理部 API endpoints
包含：立项管理、项目阶段门管理、风险管理、项目结项管理、PMO驾驶舱
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.pmo import (
    PmoMeeting,
    PmoProjectClosure,
    PmoProjectInitiation,
    PmoProjectPhase,
    PmoProjectRisk,
    PmoResourceAllocation,
)
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.pmo import (
    ClosureCreate,
    ClosureLessonsRequest,
    ClosureResponse,
    ClosureReviewRequest,
    DashboardResponse,
    DashboardSummary,
    InitiationApproveRequest,
    InitiationCreate,
    InitiationRejectRequest,
    InitiationResponse,
    InitiationUpdate,
    MeetingCreate,
    MeetingMinutesRequest,
    MeetingResponse,
    MeetingUpdate,
    PhaseAdvanceRequest,
    PhaseEntryCheckRequest,
    PhaseExitCheckRequest,
    PhaseResponse,
    PhaseReviewRequest,
    ResourceOverviewResponse,
    RiskAssessRequest,
    RiskCloseRequest,
    RiskCreate,
    RiskResponse,
    RiskResponseRequest,
    RiskStatusUpdateRequest,
    RiskWallResponse,
    WeeklyReportResponse,
)

# Included without extra prefix; decorators already include `/pmo/...` paths.
router = APIRouter(tags=["pmo-meetings"])


def generate_initiation_no(db: Session) -> str:
    """生成立项申请编号：INIT-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_init = (
        db.query(PmoProjectInitiation)
        .filter(PmoProjectInitiation.application_no.like(f"INIT-{today}-%"))
        .order_by(desc(PmoProjectInitiation.application_no))
        .first()
    )
    if max_init:
        seq = int(max_init.application_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"INIT-{today}-{seq:03d}"


def generate_risk_no(db: Session) -> str:
    """生成风险编号：RISK-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_risk = (
        db.query(PmoProjectRisk)
        .filter(PmoProjectRisk.risk_no.like(f"RISK-{today}-%"))
        .order_by(desc(PmoProjectRisk.risk_no))
        .first()
    )
    if max_risk:
        seq = int(max_risk.risk_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RISK-{today}-{seq:03d}"

# 共 6 个路由

# ==================== 会议管理 ====================

@router.get("/pmo/meetings", response_model=PaginatedResponse)
def read_meetings(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    meeting_type: Optional[str] = Query(None, description="会议类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（会议名称）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    会议列表
    """
    query = db.query(PmoMeeting)

    if project_id:
        query = query.filter(PmoMeeting.project_id == project_id)

    if meeting_type:
        query = query.filter(PmoMeeting.meeting_type == meeting_type)

    if status:
        query = query.filter(PmoMeeting.status == status)

    if keyword:
        query = query.filter(PmoMeeting.meeting_name.like(f"%{keyword}%"))

    total = query.count()
    offset = (page - 1) * page_size
    meetings = query.order_by(desc(PmoMeeting.meeting_date), desc(PmoMeeting.created_at)).offset(offset).limit(page_size).all()

    items = []
    for meeting in meetings:
        items.append(MeetingResponse(
            id=meeting.id,
            project_id=meeting.project_id,
            meeting_type=meeting.meeting_type,
            meeting_name=meeting.meeting_name,
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
            action_items=meeting.action_items if meeting.action_items else [],
            attachments=meeting.attachments if meeting.attachments else [],
            status=meeting.status,
            created_by=meeting.created_by,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/pmo/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(
    *,
    db: Session = Depends(deps.get_db),
    meeting_in: MeetingCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建会议
    """
    organizer_name = None
    if meeting_in.organizer_id:
        organizer = db.query(User).filter(User.id == meeting_in.organizer_id).first()
        organizer_name = organizer.real_name or organizer.username if organizer else None
    elif not meeting_in.organizer_id:
        # 如果没有指定组织者，使用当前用户
        organizer_name = current_user.real_name or current_user.username

    meeting = PmoMeeting(
        project_id=meeting_in.project_id,
        meeting_type=meeting_in.meeting_type,
        meeting_name=meeting_in.meeting_name,
        meeting_date=meeting_in.meeting_date,
        start_time=meeting_in.start_time,
        end_time=meeting_in.end_time,
        location=meeting_in.location,
        organizer_id=meeting_in.organizer_id or current_user.id,
        organizer_name=organizer_name,
        attendees=meeting_in.attendees or [],
        agenda=meeting_in.agenda,
        status='SCHEDULED',
        created_by=current_user.id
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return MeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        meeting_type=meeting.meeting_type,
        meeting_name=meeting.meeting_name,
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
        action_items=meeting.action_items if meeting.action_items else [],
        attachments=meeting.attachments if meeting.attachments else [],
        status=meeting.status,
        created_by=meeting.created_by,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


@router.get("/pmo/meetings/{meeting_id}", response_model=MeetingResponse)
def read_meeting(
    *,
    db: Session = Depends(deps.get_db),
    meeting_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    会议详情
    """
    meeting = db.query(PmoMeeting).filter(PmoMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    return MeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        meeting_type=meeting.meeting_type,
        meeting_name=meeting.meeting_name,
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
        action_items=meeting.action_items if meeting.action_items else [],
        attachments=meeting.attachments if meeting.attachments else [],
        status=meeting.status,
        created_by=meeting.created_by,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


@router.put("/pmo/meetings/{meeting_id}", response_model=MeetingResponse)
def update_meeting(
    *,
    db: Session = Depends(deps.get_db),
    meeting_id: int,
    meeting_in: MeetingUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新会议
    """
    meeting = db.query(PmoMeeting).filter(PmoMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    update_data = meeting_in.model_dump(exclude_unset=True)

    # 如果更新了组织者，更新组织者名称
    if 'organizer_id' in update_data and update_data['organizer_id']:
        organizer = db.query(User).filter(User.id == update_data['organizer_id']).first()
        if organizer:
            update_data['organizer_name'] = organizer.real_name or organizer.username

    for field, value in update_data.items():
        setattr(meeting, field, value)

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return read_meeting(db=db, meeting_id=meeting_id, current_user=current_user)


@router.put("/pmo/meetings/{meeting_id}/minutes", response_model=MeetingResponse)
def update_meeting_minutes(
    *,
    db: Session = Depends(deps.get_db),
    meeting_id: int,
    minutes_request: MeetingMinutesRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    记录会议纪要
    """
    meeting = db.query(PmoMeeting).filter(PmoMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    meeting.minutes = minutes_request.minutes
    meeting.decisions = minutes_request.decisions
    meeting.action_items = minutes_request.action_items or []
    meeting.status = 'COMPLETED'

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return read_meeting(db=db, meeting_id=meeting_id, current_user=current_user)


@router.get("/pmo/meetings/{meeting_id}/actions", response_model=List[Dict[str, Any]])
def get_meeting_actions(
    *,
    db: Session = Depends(deps.get_db),
    meeting_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    会议待办跟踪
    """
    meeting = db.query(PmoMeeting).filter(PmoMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    return meeting.action_items if meeting.action_items else []

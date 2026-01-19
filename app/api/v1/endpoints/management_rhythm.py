# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.management_rhythm import (
    ManagementRhythmConfig,
    StrategicMeeting,
    MeetingActionItem,
    RhythmDashboardSnapshot,
    MeetingReport,
    MeetingReportConfig,
    ReportMetricDefinition
)
from app.models.enums import (
    MeetingRhythmLevel,
    MeetingCycleType,
    ActionItemStatus,
    RhythmHealthStatus
)
from app.schemas.management_rhythm import (
    RhythmConfigCreate, RhythmConfigUpdate, RhythmConfigResponse,
    StrategicMeetingCreate, StrategicMeetingUpdate, StrategicMeetingMinutesRequest,
    StrategicMeetingResponse,
    ActionItemCreate, ActionItemUpdate, ActionItemResponse,
    RhythmDashboardResponse, RhythmDashboardSummary,
    MeetingMapItem, MeetingMapResponse, MeetingCalendarResponse, MeetingStatisticsResponse,
    StrategicStructureTemplate,
    MeetingReportGenerateRequest, MeetingReportResponse,
    MeetingReportConfigCreate, MeetingReportConfigUpdate, MeetingReportConfigResponse,
    ReportMetricDefinitionCreate, ReportMetricDefinitionUpdate, ReportMetricDefinitionResponse,
    AvailableMetricsResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


# ==================== 管理节律配置 ====================

@router.get("/management-rhythm/configs", response_model=PaginatedResponse)
def read_rhythm_configs(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    rhythm_level: Optional[str] = Query(None, description="节律层级筛选"),
    cycle_type: Optional[str] = Query(None, description="周期类型筛选"),
    is_active: Optional[str] = Query(None, description="是否启用筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（配置名称）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取节律配置列表
    """
    query = db.query(ManagementRhythmConfig)
    
    if rhythm_level:
        query = query.filter(ManagementRhythmConfig.rhythm_level == rhythm_level)
    
    if cycle_type:
        query = query.filter(ManagementRhythmConfig.cycle_type == cycle_type)
    
    if is_active:
        query = query.filter(ManagementRhythmConfig.is_active == is_active)
    
    if keyword:
        query = query.filter(ManagementRhythmConfig.config_name.like(f"%{keyword}%"))
    
    total = query.count()
    offset = (page - 1) * page_size
    configs = query.order_by(desc(ManagementRhythmConfig.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for config in configs:
        items.append(RhythmConfigResponse(
            id=config.id,
            rhythm_level=config.rhythm_level,
            cycle_type=config.cycle_type,
            config_name=config.config_name,
            description=config.description,
            meeting_template=config.meeting_template if config.meeting_template else {},
            key_metrics=config.key_metrics if config.key_metrics else [],
            output_artifacts=config.output_artifacts if config.output_artifacts else [],
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/management-rhythm/configs", response_model=RhythmConfigResponse, status_code=status.HTTP_201_CREATED)
def create_rhythm_config(
    config_data: RhythmConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建节律配置
    """
    config = ManagementRhythmConfig(
        rhythm_level=config_data.rhythm_level,
        cycle_type=config_data.cycle_type,
        config_name=config_data.config_name,
        description=config_data.description,
        meeting_template=config_data.meeting_template,
        key_metrics=config_data.key_metrics,
        output_artifacts=config_data.output_artifacts,
        is_active=config_data.is_active or "ACTIVE",
        created_by=current_user.id,
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return RhythmConfigResponse(
        id=config.id,
        rhythm_level=config.rhythm_level,
        cycle_type=config.cycle_type,
        config_name=config.config_name,
        description=config.description,
        meeting_template=config.meeting_template if config.meeting_template else {},
        key_metrics=config.key_metrics if config.key_metrics else [],
        output_artifacts=config.output_artifacts if config.output_artifacts else [],
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/management-rhythm/configs/{config_id}", response_model=RhythmConfigResponse)
def read_rhythm_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取节律配置详情
    """
    config = db.query(ManagementRhythmConfig).filter(ManagementRhythmConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="节律配置不存在")
    
    return RhythmConfigResponse(
        id=config.id,
        rhythm_level=config.rhythm_level,
        cycle_type=config.cycle_type,
        config_name=config.config_name,
        description=config.description,
        meeting_template=config.meeting_template if config.meeting_template else {},
        key_metrics=config.key_metrics if config.key_metrics else [],
        output_artifacts=config.output_artifacts if config.output_artifacts else [],
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.put("/management-rhythm/configs/{config_id}", response_model=RhythmConfigResponse)
def update_rhythm_config(
    config_id: int,
    config_data: RhythmConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新节律配置
    """
    config = db.query(ManagementRhythmConfig).filter(ManagementRhythmConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="节律配置不存在")
    
    update_data = config_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    return RhythmConfigResponse(
        id=config.id,
        rhythm_level=config.rhythm_level,
        cycle_type=config.cycle_type,
        config_name=config.config_name,
        description=config.description,
        meeting_template=config.meeting_template if config.meeting_template else {},
        key_metrics=config.key_metrics if config.key_metrics else [],
        output_artifacts=config.output_artifacts if config.output_artifacts else [],
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/management-rhythm/strategic-structure-template", response_model=StrategicStructureTemplate)
def get_strategic_structure_template(
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取五层战略结构模板
    """
    return StrategicStructureTemplate(
        vision={
            "mission": "我们希望通过____，让____变得更好",
            "vision": "最终成为一家怎样的公司",
            "why_exist": "存在的意义",
            "three_years_later": "三年后希望被怎么记住",
            "long_term_value": "为谁创造长期价值",
            "standard_expression": "我们希望通过（核心使命或创新方式），让（核心客户群体或社会群体）在（关键领域）获得（理想的未来状态），并最终成为一家怎样的公司（愿景）"
        },
        opportunity={
            "market_trend": "未来三年的行业关键趋势",
            "customer_demand": "客户需求本质",
            "competitive_gap": "竞争空位",
            "our_advantage": "我们的优势",
            "four_in_one": {
                "industry_growth": "行业是否有增长",
                "competitive_gap": "竞争是否有空隙",
                "customer_demand": "客户是否有需求",
                "our_advantage": "我们是否有优势"
            },
            "why_we_win": "凭什么能赢的逻辑",
            "standard_expression": "我们认为未来（时间周期）内，（关键趋势或结构性变化）将成为行业增长的决定力量，我们将通过（关键能力或资源杠杆），抓住（结构性机会），满足（什么本质需求），瞄准（什么竞争空位），从而建立（长期竞争势能）"
        },
        positioning={
            "market_segment": "聚焦的赛道/细分市场",
            "differentiation": "差异化方式",
            "target_customers": "核心客户群体",
            "value_proposition": "独特价值主张",
            "competitive_barrier": "竞争壁垒",
            "standard_expression": "我们选择聚焦（核心赛道/细分市场），以（核心打法/差异化路径）形成竞争壁垒，为（核心客户群体）提供（独特价值主张）"
        },
        goals={
            "strategic_hypothesis": "战略假设",
            "key_metrics": [],
            "annual_goals": "年度目标",
            "quarterly_goals": "季度目标",
            "monthly_goals": "月度目标",
            "standard_expression": "围绕上述战略机会，我们设定以下关键验证目标：通过（关键指标/OKR/KPI）衡量（假设是否成立），确保（战略成果）在（时间周期）内得到验证"
        },
        path={
            "value_chain": "价值流路径(客户需求→产品方案→交付体验→复购机制)",
            "customer_need_essence": "客户需求本质是什么",
            "product_solution": "我们在客户需求本质上应该提供什么产品",
            "service_experience": "我们在客户需求本质上应该创造什么体验",
            "repurchase_mechanism": "我们在客户需求本质上如何让客户持续复购",
            "execution_order": "执行次序",
            "rhythm": "节奏(周执行/月验证/季校准/年复盘)",
            "resources": "兵力投入",
            "campaigns": "战役系统",
            "standard_expression": "我们将通过（核心路径结构），实现战略目标，并以（经营节奏、次序、兵力、战役机制）保障战略持续运行与动态优化"
        }
    )


# ==================== 战略会议 ====================

@router.get("/strategic-meetings", response_model=PaginatedResponse)
def read_strategic_meetings(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    rhythm_level: Optional[str] = Query(None, description="会议层级筛选"),
    cycle_type: Optional[str] = Query(None, description="周期类型筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
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
    
    if status:
        query = query.filter(StrategicMeeting.status == status)
    
    if keyword:
        query = query.filter(StrategicMeeting.meeting_name.like(f"%{keyword}%"))
    
    total = query.count()
    offset = (page - 1) * page_size
    
    # 统计行动项数量
    meetings = query.order_by(desc(StrategicMeeting.meeting_date), desc(StrategicMeeting.created_at)).offset(offset).limit(page_size).all()
    
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
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
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


# ==================== 会议行动项 ====================

@router.get("/strategic-meetings/{meeting_id}/action-items", response_model=List[ActionItemResponse])
def read_meeting_action_items(
    meeting_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议行动项列表
    """
    query = db.query(MeetingActionItem).filter(MeetingActionItem.meeting_id == meeting_id)
    
    if status:
        query = query.filter(MeetingActionItem.status == status)
    
    action_items = query.order_by(MeetingActionItem.due_date, MeetingActionItem.created_at).all()
    
    return [
        ActionItemResponse(
            id=item.id,
            meeting_id=item.meeting_id,
            action_description=item.action_description,
            owner_id=item.owner_id,
            owner_name=item.owner_name,
            due_date=item.due_date,
            completed_date=item.completed_date,
            status=item.status,
            completion_notes=item.completion_notes,
            priority=item.priority,
            created_by=item.created_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in action_items
    ]


@router.post("/strategic-meetings/{meeting_id}/action-items", response_model=ActionItemResponse, status_code=status.HTTP_201_CREATED)
def create_action_item(
    meeting_id: int,
    item_data: ActionItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建会议行动项
    """
    # 验证会议存在
    meeting = db.query(StrategicMeeting).filter(StrategicMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    action_item = MeetingActionItem(
        meeting_id=meeting_id,
        action_description=item_data.action_description,
        owner_id=item_data.owner_id,
        owner_name=item_data.owner_name,
        due_date=item_data.due_date,
        priority=item_data.priority or "NORMAL",
        created_by=current_user.id,
    )
    
    db.add(action_item)
    db.commit()
    db.refresh(action_item)
    
    return ActionItemResponse(
        id=action_item.id,
        meeting_id=action_item.meeting_id,
        action_description=action_item.action_description,
        owner_id=action_item.owner_id,
        owner_name=action_item.owner_name,
        due_date=action_item.due_date,
        completed_date=action_item.completed_date,
        status=action_item.status,
        completion_notes=action_item.completion_notes,
        priority=action_item.priority,
        created_by=action_item.created_by,
        created_at=action_item.created_at,
        updated_at=action_item.updated_at,
    )


@router.put("/strategic-meetings/{meeting_id}/action-items/{item_id}", response_model=ActionItemResponse)
def update_action_item(
    meeting_id: int,
    item_id: int,
    item_data: ActionItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新会议行动项
    """
    action_item = db.query(MeetingActionItem).filter(
        and_(
            MeetingActionItem.id == item_id,
            MeetingActionItem.meeting_id == meeting_id
        )
    ).first()
    
    if not action_item:
        raise HTTPException(status_code=404, detail="行动项不存在")
    
    update_data = item_data.dict(exclude_unset=True)
    
    # 如果状态更新为已完成，自动设置完成日期
    if update_data.get("status") == ActionItemStatus.COMPLETED.value and not action_item.completed_date:
        update_data["completed_date"] = date.today()
    
    # 如果状态更新为已完成，但完成日期被清除，则恢复为待处理
    if update_data.get("status") != ActionItemStatus.COMPLETED.value and action_item.completed_date:
        if "completed_date" not in update_data:
            update_data["completed_date"] = None
    
    for field, value in update_data.items():
        setattr(action_item, field, value)
    
    # 检查是否逾期
    if action_item.status != ActionItemStatus.COMPLETED.value and action_item.due_date < date.today():
        action_item.status = ActionItemStatus.OVERDUE.value
    
    db.commit()
    db.refresh(action_item)
    
    return ActionItemResponse(
        id=action_item.id,
        meeting_id=action_item.meeting_id,
        action_description=action_item.action_description,
        owner_id=action_item.owner_id,
        owner_name=action_item.owner_name,
        due_date=action_item.due_date,
        completed_date=action_item.completed_date,
        status=action_item.status,
        completion_notes=action_item.completion_notes,
        priority=action_item.priority,
        created_by=action_item.created_by,
        created_at=action_item.created_at,
        updated_at=action_item.updated_at,
    )


# ==================== 节律仪表盘 ====================

@router.get("/management-rhythm/dashboard", response_model=RhythmDashboardSummary)
def read_rhythm_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取节律仪表盘数据
    """
    # 获取各层级的最新快照
    levels = [MeetingRhythmLevel.STRATEGIC.value, MeetingRhythmLevel.OPERATIONAL.value,
               MeetingRhythmLevel.OPERATION.value, MeetingRhythmLevel.TASK.value]
    
    result = {}
    
    for level in levels:
        # 获取最新快照
        snapshot = db.query(RhythmDashboardSnapshot).filter(
            RhythmDashboardSnapshot.rhythm_level == level
        ).order_by(desc(RhythmDashboardSnapshot.snapshot_date)).first()
        
        if snapshot:
            result[level.lower()] = RhythmDashboardResponse(
                rhythm_level=snapshot.rhythm_level,
                cycle_type=snapshot.cycle_type,
                current_cycle=snapshot.current_cycle,
                key_metrics_snapshot=snapshot.key_metrics_snapshot if snapshot.key_metrics_snapshot else {},
                health_status=snapshot.health_status,
                last_meeting_date=snapshot.last_meeting_date,
                next_meeting_date=snapshot.next_meeting_date,
                meetings_count=snapshot.meetings_count,
                completed_meetings_count=snapshot.completed_meetings_count,
                total_action_items=snapshot.total_action_items,
                completed_action_items=snapshot.completed_action_items,
                overdue_action_items=snapshot.overdue_action_items,
                completion_rate=snapshot.completion_rate,
                snapshot_date=snapshot.snapshot_date,
            )
        else:
            # 如果没有快照，实时计算
            dashboard_data = _calculate_dashboard_data(db, level)
            result[level.lower()] = dashboard_data
    
    return RhythmDashboardSummary(
        strategic=result.get("strategic"),
        operational=result.get("operational"),
        operation=result.get("operation"),
        task=result.get("task"),
    )


def _calculate_dashboard_data(db: Session, rhythm_level: str) -> RhythmDashboardResponse:
    """计算仪表盘数据"""
    # 获取当前周期的会议
    today = date.today()
    
    # 根据层级确定周期类型
    cycle_type_map = {
        MeetingRhythmLevel.STRATEGIC.value: MeetingCycleType.QUARTERLY.value,
        MeetingRhythmLevel.OPERATIONAL.value: MeetingCycleType.MONTHLY.value,
        MeetingRhythmLevel.OPERATION.value: MeetingCycleType.WEEKLY.value,
        MeetingRhythmLevel.TASK.value: MeetingCycleType.DAILY.value,
    }
    
    cycle_type = cycle_type_map.get(rhythm_level, MeetingCycleType.MONTHLY.value)
    
    # 计算当前周期
    if cycle_type == MeetingCycleType.QUARTERLY.value:
        quarter = (today.month - 1) // 3 + 1
        current_cycle = f"{today.year}-Q{quarter}"
    elif cycle_type == MeetingCycleType.MONTHLY.value:
        current_cycle = f"{today.year}-{today.month:02d}"
    elif cycle_type == MeetingCycleType.WEEKLY.value:
        week_num = today.isocalendar()[1]
        current_cycle = f"{today.year}-W{week_num:02d}"
    else:
        current_cycle = today.isoformat()
    
    # 查询会议
    meetings = db.query(StrategicMeeting).filter(
        StrategicMeeting.rhythm_level == rhythm_level
    ).all()
    
    meetings_count = len(meetings)
    completed_meetings = [m for m in meetings if m.status == "COMPLETED"]
    completed_meetings_count = len(completed_meetings)
    
    # 查询行动项
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
    
    # 计算完成率
    completion_rate = f"{(completed_action_items / total_action_items * 100):.1f}%" if total_action_items > 0 else "0%"
    
    # 计算健康状态
    if total_action_items > 0:
        completion_ratio = completed_action_items / total_action_items
        if completion_ratio >= 0.9:
            health_status = RhythmHealthStatus.GREEN.value
        elif completion_ratio >= 0.7:
            health_status = RhythmHealthStatus.YELLOW.value
        else:
            health_status = RhythmHealthStatus.RED.value
    else:
        health_status = RhythmHealthStatus.GREEN.value
    
    # 获取最近和下次会议
    last_meeting = db.query(StrategicMeeting).filter(
        and_(
            StrategicMeeting.rhythm_level == rhythm_level,
            StrategicMeeting.status == "COMPLETED"
        )
    ).order_by(desc(StrategicMeeting.meeting_date)).first()
    
    next_meeting = db.query(StrategicMeeting).filter(
        and_(
            StrategicMeeting.rhythm_level == rhythm_level,
            StrategicMeeting.status.in_(["SCHEDULED", "ONGOING"]),
            StrategicMeeting.meeting_date >= today
        )
    ).order_by(StrategicMeeting.meeting_date).first()
    
    return RhythmDashboardResponse(
        rhythm_level=rhythm_level,
        cycle_type=cycle_type,
        current_cycle=current_cycle,
        key_metrics_snapshot={},
        health_status=health_status,
        last_meeting_date=last_meeting.meeting_date if last_meeting else None,
        next_meeting_date=next_meeting.meeting_date if next_meeting else None,
        meetings_count=meetings_count,
        completed_meetings_count=completed_meetings_count,
        total_action_items=total_action_items,
        completed_action_items=completed_action_items,
        overdue_action_items=overdue_action_items,
        completion_rate=completion_rate,
        snapshot_date=today,
    )


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


# ==================== 数据集成 ====================

@router.get("/rhythm-integration/financial-metrics")
def get_financial_metrics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取财务指标（用于经营分析会）
    """
    from app.models.project import Project, ProjectCost
    from app.models.budget import ProjectBudget
    from sqlalchemy import func

    # 构建日期过滤条件
    cost_date_filter = []
    if start_date:
        cost_date_filter.append(ProjectCost.cost_date >= start_date)
    if end_date:
        cost_date_filter.append(ProjectCost.cost_date <= end_date)

    # 1. 查询总成本（从ProjectCost表）
    cost_query = db.query(func.sum(ProjectCost.amount))
    if cost_date_filter:
        cost_query = cost_query.filter(*cost_date_filter)
    total_cost = cost_query.scalar() or 0

    # 2. 查询总收入（从Project表的contract_amount，只计算进行中和已完成的项目）
    revenue_query = db.query(func.sum(Project.contract_amount)).filter(
        Project.health.in_(['H1', 'H2', 'H3', 'H4'])  # 进行中和已完结的项目
    )
    total_revenue = revenue_query.scalar() or 0

    # 3. 查询总预算（从ProjectBudget表，只计算已审批的预算）
    budget_query = db.query(func.sum(ProjectBudget.total_amount)).filter(
        ProjectBudget.status == 'APPROVED',
        ProjectBudget.is_active == True
    )
    total_budget = budget_query.scalar() or 0

    # 4. 计算利润和利润率
    total_revenue = float(total_revenue)
    total_cost = float(total_cost)
    profit = total_revenue - total_cost

    gross_margin_rate = 0.0
    if total_revenue > 0:
        gross_margin_rate = round((profit / total_revenue) * 100, 2)

    # 5. 计算预算执行率
    budget_execution_rate = 0.0
    if total_budget and float(total_budget) > 0:
        budget_execution_rate = round((total_cost / float(total_budget)) * 100, 2)

    metrics = {
        "revenue": total_revenue,
        "cost": total_cost,
        "profit": profit,
        "budget": float(total_budget) if total_budget else 0.0,
        "budget_execution_rate": budget_execution_rate,
        "gross_margin_rate": gross_margin_rate,
        "net_profit_rate": gross_margin_rate,  # 简化处理，净利率=毛利率
        "cash_flow": profit,  # 简化处理，现金流=利润
    }

    return metrics


@router.get("/rhythm-integration/project-metrics")
def get_project_metrics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目指标（用于运营例会）
    """
    from app.models.project import Project
    
    # 获取项目统计数据
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.health.in_(['H1', 'H2', 'H3'])).count()
    at_risk_projects = db.query(Project).filter(Project.health.in_(['H2', 'H3'])).count()
    
    metrics = {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "at_risk_projects": at_risk_projects,
        "project_health_distribution": {},
    }
    
    # 统计健康度分布
    health_counts = db.query(Project.health, func.count(Project.id)).group_by(Project.health).all()
    for health, count in health_counts:
        metrics["project_health_distribution"][health] = count
    
    return metrics


@router.get("/rhythm-integration/task-metrics")
def get_task_metrics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务指标（用于日清会）
    """
    from app.models.task_center import TaskUnified as Task
    
    # 获取任务统计数据
    query = db.query(Task)
    
    if start_date:
        query = query.filter(Task.created_at >= start_date)
    if end_date:
        query = query.filter(Task.created_at <= end_date)
    
    total_tasks = query.count()
    completed_tasks = query.filter(Task.status == 'COMPLETED').count()
    overdue_tasks = query.filter(
        and_(
            Task.due_date < date.today(),
            Task.status != 'COMPLETED'
        )
    ).count()
    
    metrics = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0,
    }
    
    return metrics


# ==================== 权限控制辅助函数 ====================

def check_rhythm_level_permission(user: User, rhythm_level: str) -> bool:
    """
    检查用户是否有权限访问指定层级的会议
    
    权限规则：
    - 战略层：仅高管可见
    - 经营层：部门负责人及以上
    - 运营层：项目组及相关人员
    - 任务层：执行层人员
    """
    # 获取用户角色
    user_roles = [role.name for role in user.roles] if hasattr(user, 'roles') else []
    
    # 高管角色（可根据实际角色名称调整）
    executive_roles = ['CEO', '总经理', '副总经理', '总监']
    
    # 部门负责人角色
    manager_roles = ['部门经理', '部门负责人', '项目经理']
    
    if rhythm_level == MeetingRhythmLevel.STRATEGIC.value:
        # 战略层：仅高管可见
        return any(role in executive_roles for role in user_roles) or user.is_superuser
    elif rhythm_level == MeetingRhythmLevel.OPERATIONAL.value:
        # 经营层：部门负责人及以上
        return any(role in executive_roles + manager_roles for role in user_roles) or user.is_superuser
    elif rhythm_level == MeetingRhythmLevel.OPERATION.value:
        # 运营层：项目组及相关人员（所有登录用户）
        return True
    elif rhythm_level == MeetingRhythmLevel.TASK.value:
        # 任务层：执行层人员（所有登录用户）
        return True
    else:
        return False


def filter_meetings_by_permission(db: Session, query, user: User):
    """
    根据用户权限过滤会议列表
    """
    # 如果用户是超级管理员，返回所有会议
    if user.is_superuser:
        return query
    
    # 获取用户角色
    user_roles = [role.name for role in user.roles] if hasattr(user, 'roles') else []
    executive_roles = ['CEO', '总经理', '副总经理', '总监']
    manager_roles = ['部门经理', '部门负责人', '项目经理']
    
    # 构建权限条件
    allowed_levels = []
    
    # 所有用户都可以看到运营层和任务层
    allowed_levels.extend([MeetingRhythmLevel.OPERATION.value, MeetingRhythmLevel.TASK.value])
    
    # 部门负责人及以上可以看到经营层
    if any(role in executive_roles + manager_roles for role in user_roles):
        allowed_levels.append(MeetingRhythmLevel.OPERATIONAL.value)
    
    # 高管可以看到战略层
    if any(role in executive_roles for role in user_roles):
        allowed_levels.append(MeetingRhythmLevel.STRATEGIC.value)
    
    # 过滤会议
    return query.filter(StrategicMeeting.rhythm_level.in_(allowed_levels))


# ==================== 报告配置管理 ====================

@router.get("/meeting-reports/configs", response_model=PaginatedResponse)
def read_report_configs(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    report_type: Optional[str] = Query(None, description="报告类型筛选"),
    is_default: Optional[bool] = Query(None, description="是否默认配置"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报告配置列表
    """
    query = db.query(MeetingReportConfig)
    
    if report_type:
        query = query.filter(MeetingReportConfig.report_type == report_type)
    
    if is_default is not None:
        query = query.filter(MeetingReportConfig.is_default == is_default)
    
    total = query.count()
    offset = (page - 1) * page_size
    configs = query.order_by(desc(MeetingReportConfig.is_default), desc(MeetingReportConfig.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for config in configs:
        items.append(MeetingReportConfigResponse(
            id=config.id,
            config_name=config.config_name,
            report_type=config.report_type,
            description=config.description,
            enabled_metrics=config.enabled_metrics,
            comparison_config=config.comparison_config,
            display_config=config.display_config,
            is_default=config.is_default,
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/meeting-reports/configs", response_model=MeetingReportConfigResponse, status_code=status.HTTP_201_CREATED)
def create_report_config(
    config_data: MeetingReportConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建报告配置
    """
    # 如果设置为默认配置，先取消其他默认配置
    if config_data.is_default:
        db.query(MeetingReportConfig).filter(
            and_(
                MeetingReportConfig.report_type == config_data.report_type,
                MeetingReportConfig.is_default == True
            )
        ).update({"is_default": False})
    
    config = MeetingReportConfig(
        config_name=config_data.config_name,
        report_type=config_data.report_type,
        description=config_data.description,
        enabled_metrics=[item.dict() for item in config_data.enabled_metrics] if config_data.enabled_metrics else [],
        comparison_config=config_data.comparison_config.dict() if config_data.comparison_config else None,
        display_config=config_data.display_config.dict() if config_data.display_config else None,
        is_default=config_data.is_default,
        is_active=True,
        created_by=current_user.id,
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return MeetingReportConfigResponse(
        id=config.id,
        config_name=config.config_name,
        report_type=config.report_type,
        description=config.description,
        enabled_metrics=config.enabled_metrics,
        comparison_config=config.comparison_config,
        display_config=config.display_config,
        is_default=config.is_default,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/meeting-reports/configs/{config_id}", response_model=MeetingReportConfigResponse)
def read_report_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报告配置详情
    """
    config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return MeetingReportConfigResponse(
        id=config.id,
        config_name=config.config_name,
        report_type=config.report_type,
        description=config.description,
        enabled_metrics=config.enabled_metrics,
        comparison_config=config.comparison_config,
        display_config=config.display_config,
        is_default=config.is_default,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.put("/meeting-reports/configs/{config_id}", response_model=MeetingReportConfigResponse)
def update_report_config(
    config_id: int,
    config_data: MeetingReportConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新报告配置
    """
    config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 如果设置为默认配置，先取消其他默认配置
    if config_data.is_default is True:
        db.query(MeetingReportConfig).filter(
            and_(
                MeetingReportConfig.report_type == config.report_type,
                MeetingReportConfig.is_default == True,
                MeetingReportConfig.id != config_id
            )
        ).update({"is_default": False})
    
    update_data = config_data.dict(exclude_unset=True)
    
    # 处理嵌套对象
    if config_data.enabled_metrics is not None:
        update_data["enabled_metrics"] = [item.dict() for item in config_data.enabled_metrics]
    if config_data.comparison_config is not None:
        update_data["comparison_config"] = config_data.comparison_config.dict()
    if config_data.display_config is not None:
        update_data["display_config"] = config_data.display_config.dict()
    
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    return MeetingReportConfigResponse(
        id=config.id,
        config_name=config.config_name,
        report_type=config.report_type,
        description=config.description,
        enabled_metrics=config.enabled_metrics,
        comparison_config=config.comparison_config,
        display_config=config.display_config,
        is_default=config.is_default,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/meeting-reports/configs/default/{report_type}", response_model=MeetingReportConfigResponse)
def get_default_report_config(
    report_type: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取默认报告配置
    """
    config = db.query(MeetingReportConfig).filter(
        and_(
            MeetingReportConfig.report_type == report_type,
            MeetingReportConfig.is_default == True,
            MeetingReportConfig.is_active == True
        )
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="未找到默认配置")
    
    return MeetingReportConfigResponse(
        id=config.id,
        config_name=config.config_name,
        report_type=config.report_type,
        description=config.description,
        enabled_metrics=config.enabled_metrics,
        comparison_config=config.comparison_config,
        display_config=config.display_config,
        is_default=config.is_default,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


# ==================== 指标定义管理 ====================

@router.get("/meeting-reports/metrics/available", response_model=AvailableMetricsResponse)
def get_available_metrics(
    db: Session = Depends(deps.get_db),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_active: Optional[bool] = Query(True, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取可用指标列表
    """
    query = db.query(ReportMetricDefinition)
    
    if category:
        query = query.filter(ReportMetricDefinition.category == category)
    
    if is_active is not None:
        query = query.filter(ReportMetricDefinition.is_active == is_active)
    
    metrics = query.order_by(ReportMetricDefinition.category, ReportMetricDefinition.metric_name).all()
    
    # 获取所有分类
    categories = db.query(ReportMetricDefinition.category).distinct().all()
    category_list = sorted([cat[0] for cat in categories])
    
    items = []
    for metric in metrics:
        items.append(ReportMetricDefinitionResponse(
            id=metric.id,
            metric_code=metric.metric_code,
            metric_name=metric.metric_name,
            category=metric.category,
            description=metric.description,
            data_source=metric.data_source,
            data_field=metric.data_field,
            filter_conditions=metric.filter_conditions,
            calculation_type=metric.calculation_type,
            calculation_formula=metric.calculation_formula,
            support_mom=metric.support_mom,
            support_yoy=metric.support_yoy,
            unit=metric.unit,
            format_type=metric.format_type,
            decimal_places=metric.decimal_places,
            is_active=metric.is_active,
            is_system=metric.is_system,
            created_by=metric.created_by,
            created_at=metric.created_at,
            updated_at=metric.updated_at,
        ))
    
    return AvailableMetricsResponse(
        metrics=items,
        categories=category_list,
        total_count=len(items)
    )


@router.post("/meeting-reports/metrics", response_model=ReportMetricDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_metric_definition(
    metric_data: ReportMetricDefinitionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建指标定义
    """
    # 检查指标编码是否已存在
    existing = db.query(ReportMetricDefinition).filter(
        ReportMetricDefinition.metric_code == metric_data.metric_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="指标编码已存在")
    
    metric = ReportMetricDefinition(
        metric_code=metric_data.metric_code,
        metric_name=metric_data.metric_name,
        category=metric_data.category,
        description=metric_data.description,
        data_source=metric_data.data_source,
        data_field=metric_data.data_field,
        filter_conditions=metric_data.filter_conditions,
        calculation_type=metric_data.calculation_type,
        calculation_formula=metric_data.calculation_formula,
        support_mom=metric_data.support_mom,
        support_yoy=metric_data.support_yoy,
        unit=metric_data.unit,
        format_type=metric_data.format_type,
        decimal_places=metric_data.decimal_places,
        is_active=True,
        is_system=False,
        created_by=current_user.id,
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    
    return ReportMetricDefinitionResponse(
        id=metric.id,
        metric_code=metric.metric_code,
        metric_name=metric.metric_name,
        category=metric.category,
        description=metric.description,
        data_source=metric.data_source,
        data_field=metric.data_field,
        filter_conditions=metric.filter_conditions,
        calculation_type=metric.calculation_type,
        calculation_formula=metric.calculation_formula,
        support_mom=metric.support_mom,
        support_yoy=metric.support_yoy,
        unit=metric.unit,
        format_type=metric.format_type,
        decimal_places=metric.decimal_places,
        is_active=metric.is_active,
        is_system=metric.is_system,
        created_by=metric.created_by,
        created_at=metric.created_at,
        updated_at=metric.updated_at,
    )


@router.put("/meeting-reports/metrics/{metric_id}", response_model=ReportMetricDefinitionResponse)
def update_metric_definition(
    metric_id: int,
    metric_data: ReportMetricDefinitionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新指标定义
    """
    metric = db.query(ReportMetricDefinition).filter(ReportMetricDefinition.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="指标定义不存在")
    
    # 系统预置指标不能修改某些字段
    if metric.is_system:
        if metric_data.data_source or metric_data.calculation_type or metric_data.calculation_formula:
            raise HTTPException(status_code=403, detail="系统预置指标不能修改数据源和计算方式")
    
    update_data = metric_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(metric, field, value)
    
    db.commit()
    db.refresh(metric)
    
    return ReportMetricDefinitionResponse(
        id=metric.id,
        metric_code=metric.metric_code,
        metric_name=metric.metric_name,
        category=metric.category,
        description=metric.description,
        data_source=metric.data_source,
        data_field=metric.data_field,
        filter_conditions=metric.filter_conditions,
        calculation_type=metric.calculation_type,
        calculation_formula=metric.calculation_formula,
        support_mom=metric.support_mom,
        support_yoy=metric.support_yoy,
        unit=metric.unit,
        format_type=metric.format_type,
        decimal_places=metric.decimal_places,
        is_active=metric.is_active,
        is_system=metric.is_system,
        created_by=metric.created_by,
        created_at=metric.created_at,
        updated_at=metric.updated_at,
    )


# ==================== 会议报告 ====================

@router.post("/meeting-reports/generate", response_model=MeetingReportResponse, status_code=status.HTTP_201_CREATED)
def generate_meeting_report(
    report_request: MeetingReportGenerateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成会议报告（年度或月度）
    
    - **年度报告**：生成指定年份的年度会议报告
    - **月度报告**：生成指定年月的月度会议报告，包含与上月对比数据
    
    如果report_request中包含config_id，将使用该配置生成报告（包含业务指标）。
    如果没有config_id，将尝试使用默认配置。
    """
    from app.services.meeting_report_service import MeetingReportService
    
    # 获取配置ID（优先使用请求中的，否则使用默认配置）
    config_id = report_request.config_id
    
    if not config_id:
        # 尝试获取默认配置
        default_config = db.query(MeetingReportConfig).filter(
            and_(
                MeetingReportConfig.report_type == report_request.report_type,
                MeetingReportConfig.is_default == True,
                MeetingReportConfig.is_active == True
            )
        ).first()
        if default_config:
            config_id = default_config.id
    
    if report_request.report_type == "ANNUAL":
        if report_request.period_month:
            raise HTTPException(status_code=400, detail="年度报告不需要指定月份")
        
        report = MeetingReportService.generate_annual_report(
            db=db,
            year=report_request.period_year,
            rhythm_level=report_request.rhythm_level,
            generated_by=current_user.id,
            config_id=config_id
        )
    elif report_request.report_type == "MONTHLY":
        if not report_request.period_month:
            raise HTTPException(status_code=400, detail="月度报告必须指定月份")
        
        if not (1 <= report_request.period_month <= 12):
            raise HTTPException(status_code=400, detail="月份必须在1-12之间")
        
        report = MeetingReportService.generate_monthly_report(
            db=db,
            year=report_request.period_year,
            month=report_request.period_month,
            rhythm_level=report_request.rhythm_level,
            generated_by=current_user.id,
            config_id=config_id
        )
    else:
        raise HTTPException(status_code=400, detail="报告类型必须是ANNUAL或MONTHLY")
    
    return MeetingReportResponse(
        id=report.id,
        report_no=report.report_no,
        report_type=report.report_type,
        report_title=report.report_title,
        period_year=report.period_year,
        period_month=report.period_month,
        period_start=report.period_start,
        period_end=report.period_end,
        rhythm_level=report.rhythm_level,
        report_data=report.report_data,
        comparison_data=report.comparison_data,
        file_path=report.file_path,
        file_size=report.file_size,
        status=report.status,
        generated_by=report.generated_by,
        generated_at=report.generated_at,
        published_at=report.published_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/meeting-reports", response_model=PaginatedResponse)
def read_meeting_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    report_type: Optional[str] = Query(None, description="报告类型筛选:ANNUAL/MONTHLY"),
    period_year: Optional[int] = Query(None, description="年份筛选"),
    rhythm_level: Optional[str] = Query(None, description="节律层级筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议报告列表
    """
    query = db.query(MeetingReport)
    
    if report_type:
        query = query.filter(MeetingReport.report_type == report_type)
    
    if period_year:
        query = query.filter(MeetingReport.period_year == period_year)
    
    if rhythm_level:
        query = query.filter(MeetingReport.rhythm_level == rhythm_level)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(MeetingReport.period_start), desc(MeetingReport.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        items.append(MeetingReportResponse(
            id=report.id,
            report_no=report.report_no,
            report_type=report.report_type,
            report_title=report.report_title,
            period_year=report.period_year,
            period_month=report.period_month,
            period_start=report.period_start,
            period_end=report.period_end,
            rhythm_level=report.rhythm_level,
            report_data=report.report_data,
            comparison_data=report.comparison_data,
            file_path=report.file_path,
            file_size=report.file_size,
            status=report.status,
            generated_by=report.generated_by,
            generated_at=report.generated_at,
            published_at=report.published_at,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/meeting-reports/{report_id}", response_model=MeetingReportResponse)
def read_meeting_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议报告详情
    """
    report = db.query(MeetingReport).filter(MeetingReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return MeetingReportResponse(
        id=report.id,
        report_no=report.report_no,
        report_type=report.report_type,
        report_title=report.report_title,
        period_year=report.period_year,
        period_month=report.period_month,
        period_start=report.period_start,
        period_end=report.period_end,
        rhythm_level=report.rhythm_level,
        report_data=report.report_data,
        comparison_data=report.comparison_data,
        file_path=report.file_path,
        file_size=report.file_size,
        status=report.status,
        generated_by=report.generated_by,
        generated_at=report.generated_at,
        published_at=report.published_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/meeting-reports/{report_id}/export-docx")
def export_meeting_report_docx(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    导出会议报告为Word文档
    """
    from fastapi.responses import StreamingResponse
    from app.services.meeting_report_docx_service import MeetingReportDocxService
    import os
    from app.core.config import settings
    
    report = db.query(MeetingReport).filter(MeetingReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    try:
        docx_service = MeetingReportDocxService()
        
        if report.report_type == "ANNUAL":
            # 生成年度报告Word文档
            buffer = docx_service.generate_annual_report_docx(
                report_data=report.report_data or {},
                report_title=report.report_title,
                period_year=report.period_year,
                rhythm_level=report.rhythm_level if report.rhythm_level != "ALL" else None
            )
        else:
            # 生成月度报告Word文档
            buffer = docx_service.generate_monthly_report_docx(
                report_data=report.report_data or {},
                comparison_data=report.comparison_data or {},
                report_title=report.report_title,
                period_year=report.period_year,
                period_month=report.period_month or 1,
                rhythm_level=report.rhythm_level if report.rhythm_level != "ALL" else None
            )
        
        # 保存文件
        report_dir = os.path.join(settings.UPLOAD_DIR, "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        file_rel_path = f"reports/{report.report_no}.docx"
        file_full_path = os.path.join(settings.UPLOAD_DIR, file_rel_path)
        
        with open(file_full_path, "wb") as f:
            f.write(buffer.read())
        
        file_size = os.path.getsize(file_full_path)
        
        # 更新报告记录
        report.file_path = file_rel_path
        report.file_size = file_size
        db.commit()
        
        # 返回文件
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={report.report_no}.docx"
            }
        )
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail="Word文档生成功能不可用，请安装python-docx库")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成Word文档失败: {str(e)}")

# -*- coding: utf-8 -*-
"""
节律仪表盘 - 自动生成
从 management_rhythm.py 拆分
"""

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



from fastapi import APIRouter

router = APIRouter(
    prefix="/management-rhythm/dashboard",
    tags=["dashboard"]
)

# 共 1 个路由

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




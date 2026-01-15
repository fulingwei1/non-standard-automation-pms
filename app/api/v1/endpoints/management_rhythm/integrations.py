# -*- coding: utf-8 -*-
"""
数据集成 - 自动生成
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
    prefix="/management-rhythm/integrations",
    tags=["integrations"]
)

# 共 3 个路由

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
    from app.models.cost import ProjectCost
    from app.models.budget import Budget
    from sqlalchemy import func
    
    # 获取收入、成本、利润等财务数据
    # 这里需要根据实际的数据模型进行调整
    metrics = {
        "revenue": 0.0,
        "cost": 0.0,
        "profit": 0.0,
        "cash_flow": 0.0,
        "gross_margin_rate": 0.0,
        "net_profit_rate": 0.0,
    }
    
    # TODO: 集成实际的财务数据查询逻辑
    # 示例：从ProjectCost表查询成本数据
    # 示例：从Budget表查询预算数据
    
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




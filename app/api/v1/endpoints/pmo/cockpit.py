# -*- coding: utf-8 -*-
"""
PMO 驾驶舱 - 自动生成
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

router = APIRouter(tags=["pmo-cockpit"])


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


# 共 4 个路由

# ==================== PMO 驾驶舱 ====================

@router.get("/pmo/dashboard", response_model=DashboardResponse)
def get_pmo_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    PMO 驾驶舱数据
    """
    # 统计项目
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    active_projects = db.query(func.count(Project.id)).filter(Project.is_active == True).scalar() or 0
    completed_projects = db.query(func.count(Project.id)).filter(Project.stage == 'S9').scalar() or 0

    # 统计延期项目（简化：计划结束日期已过但未完成）
    from datetime import date
    today = date.today()
    delayed_projects = db.query(func.count(Project.id)).filter(
        Project.planned_end_date != None,
        Project.planned_end_date < today,
        Project.stage != 'S9',
        Project.is_active == True
    ).scalar() or 0

    # 统计预算和成本
    budget_result = db.query(func.sum(Project.budget_amount)).scalar() or 0
    cost_result = db.query(func.sum(Project.actual_cost)).scalar() or 0

    # 统计风险
    total_risks = db.query(func.count(PmoProjectRisk.id)).filter(PmoProjectRisk.status != 'CLOSED').scalar() or 0
    high_risks = db.query(func.count(PmoProjectRisk.id)).filter(
        PmoProjectRisk.risk_level == 'HIGH',
        PmoProjectRisk.status != 'CLOSED'
    ).scalar() or 0
    critical_risks = db.query(func.count(PmoProjectRisk.id)).filter(
        PmoProjectRisk.risk_level == 'CRITICAL',
        PmoProjectRisk.status != 'CLOSED'
    ).scalar() or 0

    # 按状态统计项目
    projects_by_status = {}
    status_counts = db.query(Project.status, func.count(Project.id)).group_by(Project.status).all()
    for status, count in status_counts:
        projects_by_status[status] = count

    # 按阶段统计项目
    projects_by_stage = {}
    stage_counts = db.query(Project.stage, func.count(Project.id)).group_by(Project.stage).all()
    for stage, count in stage_counts:
        projects_by_stage[stage] = count

    # 最近的风险
    recent_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.status != 'CLOSED'
    ).order_by(desc(PmoProjectRisk.created_at)).limit(10).all()

    risk_list = []
    for risk in recent_risks:
        risk_list.append(RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            risk_no=risk.risk_no,
            risk_category=risk.risk_category,
            risk_name=risk.risk_name,
            description=risk.description,
            probability=risk.probability,
            impact=risk.impact,
            risk_level=risk.risk_level,
            response_strategy=risk.response_strategy,
            response_plan=risk.response_plan,
            owner_id=risk.owner_id,
            owner_name=risk.owner_name,
            status=risk.status,
            follow_up_date=risk.follow_up_date,
            last_update=risk.last_update,
            trigger_condition=risk.trigger_condition,
            is_triggered=risk.is_triggered,
            triggered_date=risk.triggered_date,
            closed_date=risk.closed_date,
            closed_reason=risk.closed_reason,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        ))

    return DashboardResponse(
        summary=DashboardSummary(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            delayed_projects=delayed_projects,
            total_budget=float(budget_result),
            total_cost=float(cost_result),
            total_risks=total_risks,
            high_risks=high_risks,
            critical_risks=critical_risks
        ),
        projects_by_status=projects_by_status,
        projects_by_stage=projects_by_stage,
        recent_risks=risk_list
    )


@router.get("/pmo/risk-wall", response_model=RiskWallResponse)
def get_risk_wall(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    风险预警墙
    """
    # 统计风险
    total_risks = db.query(PmoProjectRisk).filter(PmoProjectRisk.status != 'CLOSED').count()

    # 严重风险
    critical_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.risk_level == 'CRITICAL',
        PmoProjectRisk.status != 'CLOSED'
    ).order_by(desc(PmoProjectRisk.created_at)).all()

    # 高风险
    high_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.risk_level == 'HIGH',
        PmoProjectRisk.status != 'CLOSED'
    ).order_by(desc(PmoProjectRisk.created_at)).limit(20).all()

    # 按类别统计
    by_category = {}
    category_counts = db.query(
        PmoProjectRisk.risk_category,
        func.count(PmoProjectRisk.id)
    ).filter(
        PmoProjectRisk.status != 'CLOSED'
    ).group_by(PmoProjectRisk.risk_category).all()

    for category, count in category_counts:
        by_category[category] = count

    # 按项目统计
    by_project = []
    project_risks = db.query(
        PmoProjectRisk.project_id,
        func.count(PmoProjectRisk.id).label('risk_count')
    ).filter(
        PmoProjectRisk.status != 'CLOSED'
    ).group_by(PmoProjectRisk.project_id).order_by(desc('risk_count')).limit(10).all()

    for project_id, risk_count in project_risks:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            by_project.append({
                'project_id': project_id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'risk_count': risk_count
            })

    critical_list = []
    for risk in critical_risks:
        critical_list.append(RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            risk_no=risk.risk_no,
            risk_category=risk.risk_category,
            risk_name=risk.risk_name,
            description=risk.description,
            probability=risk.probability,
            impact=risk.impact,
            risk_level=risk.risk_level,
            response_strategy=risk.response_strategy,
            response_plan=risk.response_plan,
            owner_id=risk.owner_id,
            owner_name=risk.owner_name,
            status=risk.status,
            follow_up_date=risk.follow_up_date,
            last_update=risk.last_update,
            trigger_condition=risk.trigger_condition,
            is_triggered=risk.is_triggered,
            triggered_date=risk.triggered_date,
            closed_date=risk.closed_date,
            closed_reason=risk.closed_reason,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        ))

    high_list = []
    for risk in high_risks:
        high_list.append(RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            risk_no=risk.risk_no,
            risk_category=risk.risk_category,
            risk_name=risk.risk_name,
            description=risk.description,
            probability=risk.probability,
            impact=risk.impact,
            risk_level=risk.risk_level,
            response_strategy=risk.response_strategy,
            response_plan=risk.response_plan,
            owner_id=risk.owner_id,
            owner_name=risk.owner_name,
            status=risk.status,
            follow_up_date=risk.follow_up_date,
            last_update=risk.last_update,
            trigger_condition=risk.trigger_condition,
            is_triggered=risk.is_triggered,
            triggered_date=risk.triggered_date,
            closed_date=risk.closed_date,
            closed_reason=risk.closed_reason,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        ))

    return RiskWallResponse(
        total_risks=total_risks,
        critical_risks=critical_list,
        high_risks=high_list,
        by_category=by_category,
        by_project=by_project
    )


@router.get("/pmo/weekly-report", response_model=WeeklyReportResponse)
def get_weekly_report(
    db: Session = Depends(deps.get_db),
    week_start: Optional[date] = Query(None, description="周开始日期（默认：当前周）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目状态周报
    """
    from datetime import timedelta

    # 默认使用当前周
    today = date.today()
    if not week_start:
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)

    week_end = week_start + timedelta(days=6)

    # 统计新项目（本周创建）
    new_projects = db.query(Project).filter(
        Project.created_at >= datetime.combine(week_start, datetime.min.time()),
        Project.created_at <= datetime.combine(week_end, datetime.max.time())
    ).count()

    # 统计完成项目（本周完成）
    completed_projects = db.query(Project).filter(
        Project.actual_end_date >= week_start,
        Project.actual_end_date <= week_end,
        Project.stage == 'S9'
    ).count()

    # 统计延期项目
    delayed_projects = db.query(Project).filter(
        Project.planned_end_date < today,
        Project.stage != 'S9',
        Project.is_active == True
    ).count()

    # 统计新风险
    new_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.created_at >= datetime.combine(week_start, datetime.min.time()),
        PmoProjectRisk.created_at <= datetime.combine(week_end, datetime.max.time())
    ).count()

    # 统计解决风险
    resolved_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.closed_date >= week_start,
        PmoProjectRisk.closed_date <= week_end,
        PmoProjectRisk.status == 'CLOSED'
    ).count()

    # 项目更新列表（简化：返回本周有更新的项目）
    project_updates = []
    updated_projects = db.query(Project).filter(
        Project.updated_at >= datetime.combine(week_start, datetime.min.time()),
        Project.updated_at <= datetime.combine(week_end, datetime.max.time())
    ).order_by(desc(Project.updated_at)).limit(10).all()

    for proj in updated_projects:
        project_updates.append({
            'project_id': proj.id,
            'project_code': proj.project_code,
            'project_name': proj.project_name,
            'stage': proj.stage,
            'status': proj.status,
            'progress': float(proj.progress_pct) if proj.progress_pct else 0.0,
            'updated_at': proj.updated_at
        })

    return WeeklyReportResponse(
        report_date=today,
        week_start=week_start,
        week_end=week_end,
        new_projects=new_projects,
        completed_projects=completed_projects,
        delayed_projects=delayed_projects,
        new_risks=new_risks,
        resolved_risks=resolved_risks,
        project_updates=project_updates
    )


@router.get("/pmo/resource-overview", response_model=ResourceOverviewResponse)
def get_resource_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    资源负荷总览
    """
    # 统计资源分配
    total_resources = db.query(User).filter(User.is_active == True).count()

    # 统计已分配资源
    allocated_resource_ids = db.query(PmoResourceAllocation.resource_id).filter(
        PmoResourceAllocation.status.in_(['PLANNED', 'ACTIVE'])
    ).distinct().all()
    allocated_resources = len([r[0] for r in allocated_resource_ids])

    available_resources = total_resources - allocated_resources

    # 统计超负荷资源（使用workload模块的计算逻辑）
    # 计算每个资源的分配工时，超过标准工作负荷的视为超负荷
    overloaded_resources = 0
    standard_workload = 160  # 假设每月标准工时为160小时

    from collections import defaultdict
    resource_workload = defaultdict(float)

    # 统计每个资源的分配工时
    allocations = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.status.in_(['PLANNED', 'ACTIVE'])
    ).all()

    for alloc in allocations:
        # 计算该分配的预估工时（使用分配比例）
        if alloc.allocation_percent:
            # 假设每个项目的标准工时为160小时
            estimated_hours = (alloc.allocation_percent / 100) * standard_workload
            resource_workload[alloc.resource_id] += estimated_hours

    # 统计超负荷资源数量
    for resource_id, total_hours in resource_workload.items():
        if total_hours > standard_workload:
            overloaded_resources += 1

    # 按部门统计
    from app.models.organization import Department
    by_department = []
    departments = db.query(Department).all()

    for dept in departments:
        dept_users = db.query(User).filter(
            User.department == dept.name,
            User.is_active == True
        ).count()

        dept_allocated = db.query(PmoResourceAllocation.resource_id).join(
            User, PmoResourceAllocation.resource_id == User.id
        ).filter(
            User.department == dept.name,
            PmoResourceAllocation.status.in_(['PLANNED', 'ACTIVE'])
        ).distinct().count()

        by_department.append({
            'department_id': dept.id,
            'department_name': dept.name,
            'total_resources': dept_users,
            'allocated_resources': dept_allocated,
            'available_resources': dept_users - dept_allocated
        })

    return ResourceOverviewResponse(
        total_resources=total_resources,
        allocated_resources=allocated_resources,
        available_resources=available_resources,
        overloaded_resources=overloaded_resources,
        by_department=by_department
    )




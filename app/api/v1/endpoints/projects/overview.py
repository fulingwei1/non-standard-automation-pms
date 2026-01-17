# -*- coding: utf-8 -*-
"""
项目概览和仪表盘端点

包含：项目概览、仪表盘、在产项目汇总、项目时间线等
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, Project, ProjectMilestone, ProjectStatusLog
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/overview", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_projects_overview(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目概览数据
    """
    query = db.query(Project).filter(Project.is_active == True)

    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    projects = query.all()

    total_count = len(projects)
    total_contract = sum(float(p.contract_amount or 0) for p in projects)

    # 按阶段统计
    stage_counts = {}
    for p in projects:
        stage = p.stage or 'S1'
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    # 按健康度统计
    health_counts = {}
    for p in projects:
        health = p.health or 'H1'
        health_counts[health] = health_counts.get(health, 0) + 1

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_count": total_count,
            "total_contract_amount": total_contract,
            "by_stage": stage_counts,
            "by_health": health_counts,
            "in_production": len([p for p in projects if p.stage in ['S5', 'S6']]),
            "pending_delivery": len([p for p in projects if p.stage in ['S7', 'S8']]),
            "completed": len([p for p in projects if p.stage == 'S9']),
        }
    )


@router.get("/dashboard", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目仪表盘数据
    """
    query = db.query(Project).filter(Project.is_active == True, Project.is_archived == False)

    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    projects = query.all()

    # 健康状态分布
    health_distribution = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}
    for p in projects:
        health = p.health or 'H1'
        if health in health_distribution:
            health_distribution[health] += 1

    # 阶段分布
    stage_distribution = {}
    for p in projects:
        stage = p.stage or 'S1'
        stage_distribution[stage] = stage_distribution.get(stage, 0) + 1

    # 需要关注的项目（健康度H2/H3）
    attention_needed = [
        {
            "id": p.id,
            "project_code": p.project_code,
            "project_name": p.project_name,
            "health": p.health,
            "stage": p.stage,
            "pm_name": p.pm_name,
        }
        for p in projects if p.health in ['H2', 'H3']
    ][:10]

    # 即将到期的里程碑
    today = date.today()
    upcoming_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id.in_([p.id for p in projects]),
        ProjectMilestone.planned_date >= today,
        ProjectMilestone.planned_date <= today + timedelta(days=7),
        ProjectMilestone.actual_date.is_(None)
    ).order_by(ProjectMilestone.planned_date).limit(10).all()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_projects": len(projects),
            "total_contract_amount": sum(float(p.contract_amount or 0) for p in projects),
            "health_distribution": health_distribution,
            "stage_distribution": stage_distribution,
            "attention_needed": attention_needed,
            "upcoming_milestones": [
                {
                    "id": m.id,
                    "milestone_name": m.milestone_name,
                    "project_id": m.project_id,
                    "planned_date": m.planned_date.isoformat() if m.planned_date else None,
                }
                for m in upcoming_milestones
            ],
        }
    )


@router.get("/in-production-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_in_production_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    在产项目进度汇总
    """
    query = db.query(Project).filter(
        Project.is_active == True,
        Project.stage.in_(['S5', 'S6'])
    )

    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    projects = query.all()

    summary = []
    for project in projects:
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()

        summary.append({
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "pm_name": project.pm_name,
            "stage": project.stage,
            "progress_pct": project.progress_pct,
            "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
            "machine_count": len(machines),
            "machines": [
                {
                    "id": m.id,
                    "machine_code": m.machine_code,
                    "status": m.status,
                    "progress_pct": m.progress_pct,
                }
                for m in machines
            ]
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_count": len(summary),
            "projects": summary
        }
    )


@router.get("/{project_id}/timeline", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_timeline(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目时间线
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    events = []

    # 添加里程碑事件
    milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).order_by(ProjectMilestone.planned_date).all()

    for m in milestones:
        events.append({
            "type": "milestone",
            "title": m.milestone_name,
            "date": (m.actual_date or m.planned_date).isoformat() if (m.actual_date or m.planned_date) else None,
            "planned_date": m.planned_date.isoformat() if m.planned_date else None,
            "actual_date": m.actual_date.isoformat() if m.actual_date else None,
            "status": "completed" if m.actual_date else "pending",
        })

    # 添加状态变更事件
    status_logs = db.query(ProjectStatusLog).filter(
        ProjectStatusLog.project_id == project_id
    ).order_by(desc(ProjectStatusLog.changed_at)).limit(20).all()

    for log in status_logs:
        events.append({
            "type": "status_change",
            "title": f"{log.change_type}: {log.old_stage or log.old_status} → {log.new_stage or log.new_status}",
            "date": log.changed_at.isoformat() if log.changed_at else None,
            "change_reason": log.change_reason,
        })

    # 按日期排序
    events.sort(key=lambda x: x.get("date") or "", reverse=True)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_name": project.project_name,
            "events": events[:50]
        }
    )

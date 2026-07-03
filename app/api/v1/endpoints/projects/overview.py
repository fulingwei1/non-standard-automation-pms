# -*- coding: utf-8 -*-
"""
项目总览 API

提供项目与各模块关联数据的总览视图
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.data_scope import DataScopeService
from app.services.project_timeline_service import (
    add_project_created_event,
    collect_cost_events,
    collect_document_events,
    collect_milestone_events,
    collect_status_change_events,
    collect_task_events,
)
from app.services.project_relation_service import get_project_relation_service

router = APIRouter()


def _project_scope_query(db: Session, current_user: User):
    query = db.query(Project).filter(Project.is_active)
    return DataScopeService.filter_projects_by_scope(db, query, current_user)


def _count_by(projects, attr_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for project in projects:
        key = getattr(project, attr_name, None) or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _serialize_timeline_event(event) -> dict[str, Any]:
    if hasattr(event, "model_dump"):
        return event.model_dump()
    return event.dict()


@router.get("/overview", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_projects_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """项目概览数据"""
    projects = _project_scope_query(db, current_user).all()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_count": len(projects),
            "active_count": sum(1 for p in projects if not p.is_archived),
            "archived_count": sum(1 for p in projects if p.is_archived),
            "by_stage": _count_by(projects, "stage"),
            "by_health": _count_by(projects, "health"),
            "by_status": _count_by(projects, "status"),
            "total_contract_amount": sum(float(p.contract_amount or 0) for p in projects),
            "total_budget_amount": sum(float(p.budget_amount or 0) for p in projects),
            "total_actual_cost": sum(float(p.actual_cost or 0) for p in projects),
        },
    )


@router.get("/dashboard", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """项目仪表盘数据"""
    projects = _project_scope_query(db, current_user).all()
    health_distribution = _count_by(projects, "health")
    stage_distribution = _count_by(projects, "stage")

    recent_projects = sorted(
        projects,
        key=lambda project: project.created_at,
        reverse=True,
    )[:10]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "summary": {
                "total_projects": len(projects),
                "in_production_count": sum(1 for p in projects if p.stage in {"S5", "S6"}),
                "risk_count": sum(1 for p in projects if p.health in {"H3", "H4"}),
                "overdue_count": sum(1 for p in projects if p.is_overdue),
            },
            "health_distribution": health_distribution,
            "stage_distribution": stage_distribution,
            "recent_projects": [
                {
                    "id": project.id,
                    "project_code": project.project_code,
                    "project_name": project.project_name,
                    "customer_name": project.customer_name,
                    "stage": project.stage,
                    "status": project.status,
                    "health": project.health,
                    "progress_pct": float(project.progress_pct or 0),
                }
                for project in recent_projects
            ],
        },
    )


@router.get("/in-production-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_in_production_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """在产项目进度汇总"""
    projects = (
        _project_scope_query(db, current_user)
        .filter(Project.stage.in_(("S5", "S6")))
        .order_by(Project.created_at.desc())
        .all()
    )

    items = [
        {
            "id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "stage": project.stage,
            "status": project.status,
            "health": project.health,
            "progress_pct": float(project.progress_pct or 0),
            "planned_end_date": (
                project.planned_end_date.isoformat() if project.planned_end_date else None
            ),
        }
        for project in projects
    ]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "summary": {
                "total_count": len(projects),
                "by_stage": _count_by(projects, "stage"),
                "by_health": _count_by(projects, "health"),
            },
            "items": items,
        },
    )


@router.get("/{project_id}/timeline", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_timeline(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """项目时间线"""
    project = _project_scope_query(db, current_user).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    events = [
        add_project_created_event(project),
        *collect_status_change_events(db, project_id),
        *collect_milestone_events(db, project_id),
        *collect_task_events(db, project_id),
        *collect_cost_events(db, project_id),
        *collect_document_events(db, project_id),
    ]
    events.sort(key=lambda event: event.event_time, reverse=True)
    serialized_events = [_serialize_timeline_event(event) for event in events]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "events": serialized_events,
            "timeline": serialized_events,
            "total_events": len(serialized_events),
        },
    )


@router.get("/{project_id}/overview", summary="项目总览")
def get_project_overview(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目总览（包含生产/采购/交付/售后各模块数据）
    """
    service = get_project_relation_service(db)
    overview = service.get_project_overview(project_id)
    
    if not overview:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return overview


@router.get("/{project_id}/production-status", summary="项目生产状态")
def get_project_production_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目生产状态"""
    service = get_project_relation_service(db)
    return service.get_production_status(project_id)


@router.get("/{project_id}/procurement-status", summary="项目采购状态")
def get_project_procurement_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目采购状态"""
    service = get_project_relation_service(db)
    return service.get_procurement_status(project_id)


@router.get("/{project_id}/delivery-status", summary="项目交付状态")
def get_project_delivery_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目交付状态"""
    service = get_project_relation_service(db)
    return service.get_delivery_status(project_id)


@router.get("/{project_id}/after-sales-status", summary="项目售后状态")
def get_project_after_sales_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目售后状态"""
    service = get_project_relation_service(db)
    return service.get_after_sales_status(project_id)

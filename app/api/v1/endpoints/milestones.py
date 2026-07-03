# -*- coding: utf-8 -*-
"""全局里程碑兼容路由。"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.project import Project, ProjectMilestone
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


def _serialize_milestone(milestone: ProjectMilestone) -> dict:
    project = milestone.project
    return {
        "id": milestone.id,
        "project_id": milestone.project_id,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "machine_id": milestone.machine_id,
        "milestone_code": milestone.milestone_code,
        "milestone_name": milestone.milestone_name,
        "milestone_type": milestone.milestone_type,
        "planned_date": milestone.planned_date.isoformat() if milestone.planned_date else None,
        "actual_date": milestone.actual_date.isoformat() if milestone.actual_date else None,
        "status": milestone.status,
        "stage_code": milestone.stage_code,
        "owner_id": milestone.owner_id,
        "remark": milestone.remark,
        "created_at": milestone.created_at.isoformat() if milestone.created_at else None,
        "updated_at": milestone.updated_at.isoformat() if milestone.updated_at else None,
    }


@router.get("/", response_model=PaginatedResponse[dict])
def list_milestones(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态"),
    milestone_type: Optional[str] = Query(None, description="里程碑类型"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    query = db.query(ProjectMilestone)

    if project_id:
        query = query.filter(ProjectMilestone.project_id == project_id)
    if status_filter and status_filter != "all":
        query = query.filter(ProjectMilestone.status == status_filter)
    if milestone_type:
        query = query.filter(ProjectMilestone.milestone_type == milestone_type)

    total = query.count()
    rows = apply_pagination(
        query.order_by(desc(ProjectMilestone.planned_date), desc(ProjectMilestone.id)),
        pagination.offset,
        pagination.limit,
    ).all()

    return PaginatedResponse(
        items=[_serialize_milestone(row) for row in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.get("/projects/{project_id}/milestones", response_model=PaginatedResponse[dict])
def list_project_milestones_compat(
    project_id: int,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return list_milestones(
        db=db,
        pagination=pagination,
        project_id=project_id,
        status_filter=None,
        milestone_type=None,
        current_user=current_user,
    )


@router.get("/{milestone_id}", response_model=dict)
def get_milestone(
    milestone_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    return _serialize_milestone(milestone)


def _parse_date(value: Any) -> Optional[date]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_milestone(
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    project_id = data.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id不能为空")

    project = db.query(Project).filter(Project.id == int(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    milestone = ProjectMilestone(
        project_id=int(project_id),
        machine_id=data.get("machine_id"),
        milestone_code=data.get("milestone_code") or f"MS-{uuid4().hex[:8].upper()}",
        milestone_name=data.get("milestone_name") or data.get("name"),
        milestone_type=data.get("milestone_type") or "CUSTOM",
        planned_date=_parse_date(data.get("planned_date")),
        stage_code=data.get("stage_code"),
        deliverables=data.get("deliverables"),
        owner_id=data.get("owner_id"),
        remark=data.get("remark") or data.get("description"),
        status=data.get("status") or "PENDING",
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return _serialize_milestone(milestone)


@router.put("/{milestone_id}", response_model=dict)
def update_milestone(
    milestone_id: int,
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    for field in [
        "milestone_name",
        "milestone_type",
        "status",
        "stage_code",
        "deliverables",
        "owner_id",
        "remark",
    ]:
        if field in data:
            setattr(milestone, field, data[field])
    if "planned_date" in data:
        milestone.planned_date = _parse_date(data.get("planned_date"))
    if "actual_date" in data:
        milestone.actual_date = _parse_date(data.get("actual_date"))

    db.commit()
    db.refresh(milestone)
    return _serialize_milestone(milestone)


@router.put("/{milestone_id}/complete", response_model=dict)
def complete_milestone(
    milestone_id: int,
    data: dict = Body(default={}),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    milestone.status = "COMPLETED"
    milestone.actual_date = _parse_date(data.get("actual_date")) or date.today()
    if data.get("completion_note"):
        milestone.remark = data["completion_note"]

    db.commit()
    db.refresh(milestone)
    return _serialize_milestone(milestone)


@router.delete("/{milestone_id}", response_model=ResponseModel)
def delete_milestone(
    milestone_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    db.delete(milestone)
    db.commit()
    return ResponseModel(code=200, message="删除成功")

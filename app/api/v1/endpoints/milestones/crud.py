# -*- coding: utf-8 -*-
"""
里程碑CRUD操作
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectMilestone
from app.models.user import User
from app.schemas.project import MilestoneCreate, MilestoneResponse, MilestoneUpdate

router = APIRouter()


@router.get("/", response_model=List[MilestoneResponse], deprecated=True)
def read_milestones(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="里程碑状态筛选"),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 GET /projects/{project_id}/milestones/

    Retrieve milestones.
    """
    from app.utils.permission_helpers import (
        check_project_access_or_raise,
        filter_by_project_access,
    )

    query = db.query(ProjectMilestone)

    # 如果指定了project_id，检查访问权限并过滤
    if project_id:
        check_project_access_or_raise(db, current_user, project_id)
        query = query.filter(ProjectMilestone.project_id == project_id)
    else:
        # 根据用户权限过滤项目
        query = filter_by_project_access(
            db, query, current_user, ProjectMilestone.project_id
        )

    if status:
        query = query.filter(ProjectMilestone.status == status)

    milestones = (
        query.order_by(desc(ProjectMilestone.planned_date))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return milestones


@router.get("/projects/{project_id}/milestones", response_model=List[MilestoneResponse], deprecated=True)
def get_project_milestones(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    status: Optional[str] = Query(None, description="里程碑状态筛选"),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 GET /projects/{project_id}/milestones/

    获取项目的里程碑列表
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id)
    if status:
        query = query.filter(ProjectMilestone.status == status)

    milestones = query.order_by(ProjectMilestone.planned_date).all()
    return milestones


@router.post("/", response_model=MilestoneResponse, deprecated=True)
def create_milestone(
    *,
    db: Session = Depends(deps.get_db),
    milestone_in: MilestoneCreate,
    current_user: User = Depends(security.require_permission("milestone:create")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 POST /projects/{project_id}/milestones/

    Create new milestone.
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, milestone_in.project_id, "您没有权限在该项目中创建里程碑")

    milestone = ProjectMilestone(**milestone_in.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.get("/{milestone_id}", response_model=MilestoneResponse, deprecated=True)
def read_milestone(
    *,
    db: Session = Depends(deps.get_db),
    milestone_id: int,
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 GET /projects/{project_id}/milestones/{milestone_id}

    Get milestone by ID.
    """
    milestone = (
        db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return milestone


@router.put("/{milestone_id}", response_model=MilestoneResponse, deprecated=True)
def update_milestone(
    *,
    db: Session = Depends(deps.get_db),
    milestone_id: int,
    milestone_in: MilestoneUpdate,
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 PUT /projects/{project_id}/milestones/{milestone_id}

    Update a milestone.
    """
    milestone = (
        db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    update_data = milestone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)

    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone

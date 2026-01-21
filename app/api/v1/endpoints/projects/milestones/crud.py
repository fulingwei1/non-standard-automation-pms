# -*- coding: utf-8 -*-
"""
项目里程碑 CRUD 操作

适配自 app/api/v1/endpoints/milestones/crud.py
变更: 路由从 /milestones/ 改为 /projects/{project_id}/milestones/
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectMilestone
from app.models.user import User
from app.schemas.project import MilestoneCreate, MilestoneResponse, MilestoneUpdate
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=List[MilestoneResponse])
def read_project_milestones(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="里程碑状态筛选"),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目的里程碑列表"""
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
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


@router.post("/", response_model=MilestoneResponse)
def create_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_in: MilestoneCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:create")),
) -> Any:
    """为项目创建里程碑"""
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中创建里程碑")

    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 创建里程碑，强制使用路径中的 project_id
    milestone_data = milestone_in.model_dump()
    milestone_data["project_id"] = project_id  # 确保使用路径中的项目ID

    milestone = ProjectMilestone(**milestone_data)
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.get("/{milestone_id}", response_model=MilestoneResponse)
def read_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目里程碑详情"""
    check_project_access_or_raise(db, current_user, project_id)

    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id,
        ProjectMilestone.project_id == project_id,
    ).first()

    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    return milestone


@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    milestone_in: MilestoneUpdate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
) -> Any:
    """更新项目里程碑"""
    check_project_access_or_raise(db, current_user, project_id)

    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id,
        ProjectMilestone.project_id == project_id,
    ).first()

    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    update_data = milestone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)

    db.commit()
    db.refresh(milestone)
    return milestone

from typing import Any, List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import ProjectStage, ProjectStatus, Project
from app.schemas.project import (
    ProjectStageCreate,
    ProjectStageResponse,
    ProjectStageUpdate,
    ProjectStatusCreate,
    ProjectStatusResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()


# ==================== 阶段管理 ====================


@router.get("/", response_model=List[ProjectStageResponse])
def read_stages(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("stage:read")),
) -> Any:
    """
    获取项目阶段列表
    """
    query = db.query(ProjectStage)
    if project_id:
        query = query.filter(ProjectStage.project_id == project_id)
    if is_active is not None:
        query = query.filter(ProjectStage.is_active == is_active)

    stages = (
        query.order_by(asc(ProjectStage.stage_order)).offset(skip).limit(limit).all()
    )
    return stages


@router.get("/projects/{project_id}/stages", response_model=List[ProjectStageResponse])
def get_project_stages(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("stage:read")),
) -> Any:
    """
    获取项目的阶段列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    stages = (
        db.query(ProjectStage)
        .filter(ProjectStage.project_id == project_id)
        .order_by(asc(ProjectStage.stage_order))
        .all()
    )
    return stages


@router.post("/", response_model=ProjectStageResponse)
def create_stage(
    *,
    db: Session = Depends(deps.get_db),
    stage_in: ProjectStageCreate,
    current_user: User = Depends(security.require_permission("stage:create")),
) -> Any:
    """
    Create new project stage.
    """
    # Check if this stage code already exists for this project
    existing = (
        db.query(ProjectStage)
        .filter(
            ProjectStage.project_id == stage_in.project_id,
            ProjectStage.stage_code == stage_in.stage_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Stage code already exists for this project"
        )

    stage = ProjectStage(**stage_in.model_dump())
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage


@router.get("/{stage_id}", response_model=ProjectStageResponse)
def read_stage(
    *,
    db: Session = Depends(deps.get_db),
    stage_id: int,
) -> Any:
    """
    Get stage by ID.
    """
    stage = db.query(ProjectStage).get(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    return stage


@router.put("/{stage_id}", response_model=ProjectStageResponse)
def update_stage(
    *,
    db: Session = Depends(deps.get_db),
    stage_id: int,
    stage_in: ProjectStageCreate,
    current_user: User = Depends(security.require_permission("stage:update")),
) -> Any:
    """
    更新项目阶段
    """
    stage = db.query(ProjectStage).get(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")

    update_data = stage_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(stage, field):
            setattr(stage, field, value)

    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage


@router.put("/project-stages/{stage_id}", response_model=ProjectStageResponse)
def update_project_stage_progress(
    *,
    db: Session = Depends(deps.get_db),
    stage_id: int,
    progress_pct: Optional[int] = Query(None, ge=0, le=100, description="进度百分比（0-100）"),
    status: Optional[str] = Query(None, description="阶段状态"),
    actual_start_date: Optional[str] = Query(None, description="实际开始日期（YYYY-MM-DD）"),
    actual_end_date: Optional[str] = Query(None, description="实际结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.require_permission("stage:read")),
) -> Any:
    """
    更新项目阶段进度
    """
    from datetime import datetime
    
    stage = db.query(ProjectStage).filter(ProjectStage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    if progress_pct is not None:
        stage.progress_pct = progress_pct
    if status:
        stage.status = status
    if actual_start_date:
        try:
            stage.actual_start_date = datetime.strptime(actual_start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    if actual_end_date:
        try:
            stage.actual_end_date = datetime.strptime(actual_end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage


# ==================== 状态管理 ====================


@router.get("/statuses", response_model=List[ProjectStatusResponse])
def read_statuses(
    db: Session = Depends(deps.get_db),
    stage_id: Optional[int] = Query(None, description="阶段ID筛选"),
    current_user: User = Depends(security.require_permission("stage:read")),
) -> Any:
    """
    获取项目状态列表
    """
    query = db.query(ProjectStatus)
    if stage_id:
        query = query.filter(ProjectStatus.stage_id == stage_id)

    statuses = query.order_by(asc(ProjectStatus.status_order)).all()
    return statuses


@router.get("/project-stages/{stage_id}/statuses", response_model=List[ProjectStatusResponse])
def get_stage_statuses(
    *,
    db: Session = Depends(deps.get_db),
    stage_id: int,
    current_user: User = Depends(security.require_permission("stage:read")),
) -> Any:
    """
    获取阶段的状态列表
    """
    stage = db.query(ProjectStage).filter(ProjectStage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    statuses = (
        db.query(ProjectStatus)
        .filter(ProjectStatus.stage_id == stage_id)
        .order_by(asc(ProjectStatus.status_order))
        .all()
    )
    return statuses


@router.put("/project-statuses/{status_id}/complete", response_model=ResponseModel)
def complete_project_status(
    *,
    db: Session = Depends(deps.get_db),
    status_id: int,
    current_user: User = Depends(security.require_permission("stage:read")),
) -> Any:
    """
    完成项目状态（标记状态为已完成）
    注意：这里只是标记，实际的状态管理可能需要更复杂的逻辑
    """
    status = db.query(ProjectStatus).filter(ProjectStatus.id == status_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="状态不存在")
    
    # 这里可以根据实际需求添加完成逻辑
    # 例如：更新状态类型、记录完成时间等
    
    return ResponseModel(
        code=200,
        message="状态已标记为完成",
        data={"status_id": status_id, "status_code": status.status_code}
    )


@router.post("/statuses", response_model=ProjectStatusResponse)
def create_status(
    *,
    db: Session = Depends(deps.get_db),
    status_in: ProjectStatusCreate,
    current_user: User = Depends(security.require_permission("stage:read")),
) -> Any:
    """
    Create new project status.
    """
    existing = (
        db.query(ProjectStatus)
        .filter(
            ProjectStatus.stage_id == status_in.stage_id,
            ProjectStatus.status_code == status_in.status_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Status code already exists for this stage"
        )

    status = ProjectStatus(**status_in.model_dump())
    db.add(status)
    db.commit()
    db.refresh(status)
    return status

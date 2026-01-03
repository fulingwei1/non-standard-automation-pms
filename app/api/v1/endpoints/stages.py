from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.api import deps
from app.models.project import ProjectStage, ProjectStatus
from app.schemas.project import (
    ProjectStageCreate,
    ProjectStageResponse,
    ProjectStatusCreate,
    ProjectStatusResponse,
)

router = APIRouter()


# ==================== 阶段管理 ====================


@router.get("/", response_model=List[ProjectStageResponse])
def read_stages(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: int = Query(None, description="Filter by project ID"),
    is_active: bool = Query(None),
) -> Any:
    """
    Retrieve project stages (usually for a specific project).
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


@router.post("/", response_model=ProjectStageResponse)
def create_stage(
    *,
    db: Session = Depends(deps.get_db),
    stage_in: ProjectStageCreate,
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
) -> Any:
    """
    Update a project stage.
    """
    stage = db.query(ProjectStage).get(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    update_data = stage_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(stage, field):
            setattr(stage, field, value)

    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage


# ==================== 状态管理 ====================


@router.get("/statuses", response_model=List[ProjectStatusResponse])
def read_statuses(
    db: Session = Depends(deps.get_db),
    stage_id: int = Query(None),
) -> Any:
    """
    Retrieve project statuses.
    """
    query = db.query(ProjectStatus)
    if stage_id:
        query = query.filter(ProjectStatus.stage_id == stage_id)

    statuses = query.order_by(asc(ProjectStatus.status_order)).all()
    return statuses


@router.post("/statuses", response_model=ProjectStatusResponse)
def create_status(
    *,
    db: Session = Depends(deps.get_db),
    status_in: ProjectStatusCreate,
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

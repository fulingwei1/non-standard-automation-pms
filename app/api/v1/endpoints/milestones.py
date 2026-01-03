from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models.project import ProjectMilestone, Project
from app.schemas.project import MilestoneCreate, MilestoneUpdate, MilestoneResponse

router = APIRouter()


@router.get("/", response_model=List[MilestoneResponse])
def read_milestones(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: int = Query(None, description="Filter by project ID"),
    status: str = Query(None, description="Filter by milestone status"),
) -> Any:
    """
    Retrieve milestones.
    """
    query = db.query(ProjectMilestone)
    if project_id:
        query = query.filter(ProjectMilestone.project_id == project_id)
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
def create_milestone(
    *,
    db: Session = Depends(deps.get_db),
    milestone_in: MilestoneCreate,
) -> Any:
    """
    Create new milestone.
    """
    project = db.query(Project).filter(Project.id == milestone_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestone = ProjectMilestone(**milestone_in.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.get("/{milestone_id}", response_model=MilestoneResponse)
def read_milestone(
    *,
    db: Session = Depends(deps.get_db),
    milestone_id: int,
) -> Any:
    """
    Get milestone by ID.
    """
    milestone = (
        db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return milestone


@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    *,
    db: Session = Depends(deps.get_db),
    milestone_id: int,
    milestone_in: MilestoneUpdate,
) -> Any:
    """
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


@router.delete("/{milestone_id}", response_model=MilestoneResponse)
def delete_milestone(
    *,
    db: Session = Depends(deps.get_db),
    milestone_id: int,
) -> Any:
    """
    Delete a milestone.
    """
    milestone = (
        db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    db.delete(milestone)
    db.commit()
    return milestone

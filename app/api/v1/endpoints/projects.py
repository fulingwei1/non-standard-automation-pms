from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)

router = APIRouter()


@router.get("/", response_model=List[ProjectListResponse])
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 20,
    stage: str = Query(None, description="Filter by project stage"),
    min_progress: int = Query(
        None, description="Filter by minimum progress percentage"
    ),
) -> Any:
    """
    Retrieve projects with optional filtering.
    """
    query = db.query(Project)

    if stage:
        query = query.filter(Project.stage == stage)
    if min_progress is not None:
        query = query.filter(Project.progress_pct >= min_progress)

    projects = query.order_by(desc(Project.created_at)).offset(skip).limit(limit).all()
    # Manual mapping for response model compatibility if needed, but Pydantic might handle aliases if configured
    # For now, we rely on Pydantic's from_attributes = True (orm_mode) and field matching.
    # However, schema uses project_no, model uses project_code.
    # We might need to adjust the schema or alias the model fields in response.
    # Let's adjust schema in next step if this fails or just map it here.
    return projects


@router.post("/", response_model=ProjectResponse)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
) -> Any:
    """
    Create new project.
    """
    # Check if project number exists
    project = (
        db.query(Project)
        .filter(Project.project_code == project_in.project_code)
        .first()
    )
    if project:
        raise HTTPException(
            status_code=400,
            detail="The project with this project number already exists in the system.",
        )

    project = Project(
        project_code=project_in.project_code,
        project_name=project_in.project_name,
        short_name=project_in.short_name,
        customer_id=project_in.customer_id,
        contract_no=project_in.contract_no,
        project_type=project_in.project_type,
        # business_type=project_in.business_type,
        # machine_count=project_in.machine_count,
        contract_date=project_in.contract_date,
        planned_start_date=project_in.planned_start_date,
        planned_end_date=project_in.planned_end_date,
        # delivery_date attribute missing in model
        contract_amount=project_in.contract_amount,
        budget_amount=project_in.budget_amount,
        pm_id=project_in.pm_id,
        description=project_in.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
) -> Any:
    """
    Get project by ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: ProjectUpdate,
) -> Any:
    """
    Update a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_in.dict(exclude_unset=True)

    # Field mapping
    if "manager_id" in update_data:
        update_data["pm_id"] = update_data.pop("manager_id")
    if "customer_contract_no" in update_data:
        update_data["contract_no"] = update_data.pop("customer_contract_no")
    if "project_short_name" in update_data:
        update_data["short_name"] = update_data.pop("project_short_name")

    # Ignoring fields not in model
    valid_fields = {c.name for c in Project.__table__.columns}

    for field, value in update_data.items():
        if field in valid_fields:
            setattr(project, field, value)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project

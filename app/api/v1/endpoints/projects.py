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
    ProjectDetailResponse,
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

    # Convert schema to dict and remove any fields not in model
    project_data = project_in.model_dump()

    # Remove machine_count if it's strictly for logic
    project_data.pop("machine_count", None)

    project = Project(**project_data)

    # Optionally populate redundant fields from related objects
    if project.customer_id:
        from app.models.project import Customer

        customer = db.query(Customer).get(project.customer_id)
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

    if project.pm_id:
        from app.models.user import User

        pm = db.query(User).get(project.pm_id)
        if pm:
            project.pm_name = pm.real_name or pm.username

    db.add(project)
    db.commit()
    db.refresh(project)

    # Initialize standard stages for the project
    from app.utils.project_utils import init_project_stages

    init_project_stages(db, project.id)

    return project


@router.get("/{project_id}", response_model=ProjectDetailResponse)
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

    # Add dynamically fetched data if redundant fields are empty
    if not project.customer_name and project.customer:
        project.customer_name = project.customer.customer_name
    if not project.pm_name and project.manager:
        project.pm_name = project.manager.real_name or project.manager.username

    # Convert dynamic relationships to lists for Pydantic
    # Pydantic detail response will automatically use these
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

    update_data = project_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(project, field):
            setattr(project, field, value)

    # Update redundant fields if ID changed
    if "customer_id" in update_data:
        from app.models.project import Customer

        customer = db.query(Customer).get(project.customer_id)
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

    if "pm_id" in update_data:
        from app.models.user import User

        pm = db.query(User).get(project.pm_id)
        if pm:
            project.pm_name = pm.real_name or pm.username

    db.add(project)
    db.commit()
    db.refresh(project)
    return project

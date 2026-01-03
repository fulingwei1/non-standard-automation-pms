from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models.project import ProjectCost, Project
from app.schemas.project import ProjectCostCreate, ProjectCostResponse

router = APIRouter()


@router.get("/", response_model=List[ProjectCostResponse])
def read_costs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: int = Query(None, description="Filter by project ID"),
) -> Any:
    """
    Retrieve cost records.
    """
    query = db.query(ProjectCost)
    if project_id:
        query = query.filter(ProjectCost.project_id == project_id)

    costs = query.order_by(desc(ProjectCost.cost_date)).offset(skip).limit(limit).all()
    return costs


@router.post("/", response_model=ProjectCostResponse)
def create_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_in: ProjectCostCreate,
) -> Any:
    """
    Create new cost record.
    """
    project = db.query(Project).filter(Project.id == cost_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cost = ProjectCost(**cost_in.model_dump())

    db.add(cost)
    db.commit()
    db.refresh(cost)
    return cost


@router.delete("/{cost_id}", response_model=ProjectCostResponse)
def delete_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
) -> Any:
    """
    Delete a cost record.
    """
    cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Cost record not found")

    db.delete(cost)
    db.commit()
    return cost

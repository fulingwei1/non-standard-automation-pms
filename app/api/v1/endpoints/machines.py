from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models.project import Machine, Project
from app.schemas.project import (
    MachineCreate,
    MachineUpdate,
    MachineResponse,
)

router = APIRouter()


@router.get("/", response_model=List[MachineResponse])
def read_machines(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: int = Query(None, description="Filter by project ID"),
    stage: str = Query(None, description="Filter by machine stage"),
) -> Any:
    """
    Retrieve machines.
    """
    query = db.query(Machine)
    if project_id:
        query = query.filter(Machine.project_id == project_id)
    if stage:
        query = query.filter(Machine.stage == stage)

    machines = query.order_by(desc(Machine.created_at)).offset(skip).limit(limit).all()
    return machines


@router.post("/", response_model=MachineResponse)
def create_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_in: MachineCreate,
) -> Any:
    """
    Create new machine.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.id == machine_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if machine code exists in project
    existing = (
        db.query(Machine)
        .filter(
            Machine.project_id == machine_in.project_id,
            Machine.machine_code == machine_in.machine_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Machine with this code already exists in this project.",
        )

    machine = Machine(**machine_in.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.get("/{machine_id}", response_model=MachineResponse)
def read_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
) -> Any:
    """
    Get machine by ID.
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    machine_in: MachineUpdate,
) -> Any:
    """
    Update a machine.
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    update_data = machine_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(machine, field):
            setattr(machine, field, value)

    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.delete("/{machine_id}", response_model=MachineResponse)
def delete_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
) -> Any:
    """
    Delete a machine.
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    db.delete(machine)
    db.commit()
    return machine

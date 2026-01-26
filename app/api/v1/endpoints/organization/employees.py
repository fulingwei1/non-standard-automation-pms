# -*- coding: utf-8 -*-
"""
员工管理端点
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.organization import Employee
from app.schemas.organization import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)

router = APIRouter()


@router.get("/employees", response_model=List[EmployeeResponse])
def read_employees(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve employees."""
    employees = db.query(Employee).offset(skip).limit(limit).all()
    return employees


@router.post("/employees", response_model=EmployeeResponse)
def create_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_in: EmployeeCreate,
) -> Any:
    """Create new employee."""
    employee = (
        db.query(Employee)
        .filter(Employee.employee_code == emp_in.employee_code)
        .first()
    )
    if employee:
        raise HTTPException(
            status_code=400,
            detail="Employee with this code already exists.",
        )
    employee = Employee(**emp_in.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/employees/{emp_id}", response_model=EmployeeResponse)
def read_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_id: int,
) -> Any:
    """Get employee by ID."""
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_id: int,
    emp_in: EmployeeUpdate,
) -> Any:
    """Update an employee."""
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = emp_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/{emp_id}/assignments", response_model=List[Any])
def get_employee_assignments(
    *,
    db: Session = Depends(deps.get_db),
    emp_id: int,
) -> Any:
    """Get employee organization assignments."""
    from app.models.organization import EmployeeOrgAssignment

    limit = 100
    query = db.query(EmployeeOrgAssignment).filter(
        EmployeeOrgAssignment.employee_id == emp_id
    )
    assignments = query.limit(limit).all()

    # 补充关联名称
    result = []
    for a in assignments:
        # Pydantic model will handle basic mapping, but we might need extra fields
        # Ideally schema handles from_attributes=True and relation access
        # But let's check schema definition basically
        # The response model EmployeeOrgAssignmentResponse expects:
        # employee_name, org_unit_name, position_name, job_level_name
        # These are not on the model directly, usually computed or properties
        # We can simple attach them here if needed or let Pydantic try if models have them
        # Let's manually populate to be safe as previously done in assignments.py
        a_dict = {
            "id": a.id,
            "employee_id": a.employee_id,
            "org_unit_id": a.org_unit_id,
            "position_id": a.position_id,
            "job_level_id": a.job_level_id,
            "is_primary": a.is_primary,
            "assignment_type": a.assignment_type,
            "start_date": a.start_date,
            "end_date": a.end_date,
            "is_active": a.is_active,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
            "employee_name": a.employee.name if a.employee else None,
            "org_unit_name": a.org_unit.unit_name if a.org_unit else None,
            "position_name": a.position.position_name if a.position else None,
            "job_level_name": a.job_level.level_name if a.job_level else None,
        }
        result.append(a_dict)

    return result

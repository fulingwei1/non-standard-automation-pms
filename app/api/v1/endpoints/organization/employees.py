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

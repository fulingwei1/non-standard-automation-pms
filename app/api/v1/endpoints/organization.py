from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from app.api import deps
from app.models.organization import Department, Employee
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)

router = APIRouter()

# ==================== 部门 ====================


@router.get("/departments", response_model=List[DepartmentResponse])
def read_departments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve departments.
    """
    departments = db.query(Department).offset(skip).limit(limit).all()
    return departments


@router.post("/departments", response_model=DepartmentResponse)
def create_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_in: DepartmentCreate,
) -> Any:
    """
    Create new department.
    """
    department = (
        db.query(Department).filter(Department.dept_code == dept_in.dept_code).first()
    )
    if department:
        raise HTTPException(
            status_code=400,
            detail="Department with this code already exists.",
        )
    department = Department(**dept_in.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.get("/departments/{dept_id}", response_model=DepartmentResponse)
def read_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
) -> Any:
    """
    Get department by ID.
    """
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
def update_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    dept_in: DepartmentUpdate,
) -> Any:
    """
    Update a department.
    """
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    update_data = dept_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)

    db.add(department)
    db.commit()
    db.refresh(department)
    return department


# ==================== 员工 ====================


@router.get("/employees", response_model=List[EmployeeResponse])
def read_employees(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve employees.
    """
    employees = db.query(Employee).offset(skip).limit(limit).all()
    return employees


@router.post("/employees", response_model=EmployeeResponse)
def create_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_in: EmployeeCreate,
) -> Any:
    """
    Create new employee.
    """
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
    """
    Get employee by ID.
    """
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
    """
    Update an employee.
    """
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

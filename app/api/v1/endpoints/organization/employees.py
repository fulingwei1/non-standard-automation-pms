# -*- coding: utf-8 -*-
"""
员工管理端点（重构版）
使用统一响应格式
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.schemas import list_response, success_response
from app.models.organization import Employee
from app.schemas.organization import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)

router = APIRouter()


@router.get("/employees")
def read_employees(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """获取员工列表"""
    employees = db.query(Employee).offset(skip).limit(limit).all()

    # 转换为Pydantic模型
    emp_responses = [EmployeeResponse.model_validate(emp) for emp in employees]

    # 使用统一响应格式
    return list_response(
        items=emp_responses,
        message="获取员工列表成功"
    )


@router.post("/employees")
def create_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_in: EmployeeCreate,
) -> Any:
    """创建新员工"""
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

    # 转换为Pydantic模型
    emp_response = EmployeeResponse.model_validate(employee)

    # 使用统一响应格式
    return success_response(
        data=emp_response,
        message="员工创建成功"
    )


@router.get("/employees/{emp_id}")
def read_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_id: int,
) -> Any:
    """获取员工详情"""
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # 转换为Pydantic模型
    emp_response = EmployeeResponse.model_validate(employee)

    # 使用统一响应格式
    return success_response(
        data=emp_response,
        message="获取员工信息成功"
    )


@router.put("/employees/{emp_id}")
def update_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_id: int,
    emp_in: EmployeeUpdate,
) -> Any:
    """更新员工信息"""
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = emp_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    db.add(employee)
    db.commit()
    db.refresh(employee)

    # 转换为Pydantic模型
    emp_response = EmployeeResponse.model_validate(employee)

    # 使用统一响应格式
    return success_response(
        data=emp_response,
        message="员工更新成功"
    )


@router.get("/{emp_id}/assignments")
def get_employee_assignments(
    *,
    db: Session = Depends(deps.get_db),
    emp_id: int,
) -> Any:
    """获取员工组织分配"""
    from app.models.organization import EmployeeOrgAssignment

    limit = 100
    query = db.query(EmployeeOrgAssignment).filter(
        EmployeeOrgAssignment.employee_id == emp_id
    )
    assignments = query.limit(limit).all()

    # 手动构建响应数据（包含关联名称）
    result = []
    for a in assignments:
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

    # 使用统一响应格式
    return list_response(
        items=result,
        message="获取员工分配成功"
    )

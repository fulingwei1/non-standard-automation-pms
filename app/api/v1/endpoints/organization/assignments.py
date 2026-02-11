# -*- coding: utf-8 -*-
"""
员工组织分配管理端点（重构版）
使用统一响应格式
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas import list_response, success_response
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.models.organization import EmployeeOrgAssignment
from app.models.user import User
from app.schemas.organization import (
    EmployeeOrgAssignmentCreate,
    EmployeeOrgAssignmentUpdate,
)

router = APIRouter()


@router.get("/")
def list_assignments(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    org_unit_id: Optional[int] = Query(None, description="组织单元ID"),
    is_active: Optional[bool] = Query(None, description="是否有效"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取员工组织分配列表"""
    query = db.query(EmployeeOrgAssignment)
    if employee_id:
        query = query.filter(EmployeeOrgAssignment.employee_id == employee_id)
    if org_unit_id:
        query = query.filter(EmployeeOrgAssignment.org_unit_id == org_unit_id)
    if is_active is not None:
        query = query.filter(EmployeeOrgAssignment.is_active.is_(is_active))

    assignments = apply_pagination(query, pagination.offset, pagination.limit).all()

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
        message="获取员工分配列表成功"
    )


@router.post("/")
def create_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assign_in: EmployeeOrgAssignmentCreate,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """创建员工组织分配"""
    # 检查主归属冲突
    if assign_in.is_primary:
        existing_primary = (
            db.query(EmployeeOrgAssignment)
            .filter(
                EmployeeOrgAssignment.employee_id == assign_in.employee_id,
                EmployeeOrgAssignment.is_primary.is_(True),
                EmployeeOrgAssignment.is_active.is_(True),
            )
            .first()
        )
        if existing_primary:
            # 将原主归属设置为非主归属
            existing_primary.is_primary = False
            db.add(existing_primary)

    assign = EmployeeOrgAssignment(**assign_in.model_dump())
    db.add(assign)
    db.commit()
    db.refresh(assign)

    # 手动构建响应数据
    a_dict = {
        "id": assign.id,
        "employee_id": assign.employee_id,
        "org_unit_id": assign.org_unit_id,
        "position_id": assign.position_id,
        "job_level_id": assign.job_level_id,
        "is_primary": assign.is_primary,
        "assignment_type": assign.assignment_type,
        "start_date": assign.start_date,
        "end_date": assign.end_date,
        "is_active": assign.is_active,
        "created_at": assign.created_at,
        "updated_at": assign.updated_at,
        "employee_name": assign.employee.name if assign.employee else None,
        "org_unit_name": assign.org_unit.unit_name if assign.org_unit else None,
        "position_name": assign.position.position_name if assign.position else None,
        "job_level_name": assign.job_level.level_name if assign.job_level else None,
    }

    # 使用统一响应格式
    return success_response(
        data=a_dict,
        message="员工分配创建成功"
    )


@router.put("/{id}")
def update_assignment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    assign_in: EmployeeOrgAssignmentUpdate,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """更新员工组织分配"""
    assign = (
        db.query(EmployeeOrgAssignment).filter(EmployeeOrgAssignment.id == id).first()
    )
    if not assign:
        raise HTTPException(status_code=404, detail="分配记录不存在")

    update_data = assign_in.model_dump(exclude_unset=True)

    # 如果要设置为主要归属，需要处理冲突
    if update_data.get("is_primary") is True:
        db.query(EmployeeOrgAssignment).filter(
            EmployeeOrgAssignment.employee_id == assign.employee_id,
            EmployeeOrgAssignment.id != id,
            EmployeeOrgAssignment.is_primary.is_(True),
        ).update({"is_primary": False})

    for field, value in update_data.items():
        setattr(assign, field, value)

    db.add(assign)
    db.commit()
    db.refresh(assign)

    # 手动构建响应数据
    a_dict = {
        "id": assign.id,
        "employee_id": assign.employee_id,
        "org_unit_id": assign.org_unit_id,
        "position_id": assign.position_id,
        "job_level_id": assign.job_level_id,
        "is_primary": assign.is_primary,
        "assignment_type": assign.assignment_type,
        "start_date": assign.start_date,
        "end_date": assign.end_date,
        "is_active": assign.is_active,
        "created_at": assign.created_at,
        "updated_at": assign.updated_at,
        "employee_name": assign.employee.name if assign.employee else None,
        "org_unit_name": assign.org_unit.unit_name if assign.org_unit else None,
        "position_name": assign.position.position_name if assign.position else None,
        "job_level_name": assign.job_level.level_name if assign.job_level else None,
    }

    # 使用统一响应格式
    return success_response(
        data=a_dict,
        message="员工分配更新成功"
    )


@router.delete("/{id}")
def delete_assignment(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """删除员工组织分配"""
    assign = (
        db.query(EmployeeOrgAssignment).filter(EmployeeOrgAssignment.id == id).first()
    )
    if not assign:
        raise HTTPException(status_code=404, detail="分配记录不存在")

    db.delete(assign)
    db.commit()

    # 使用统一响应格式
    return success_response(
        data={"id": id},
        message="员工分配删除成功"
    )

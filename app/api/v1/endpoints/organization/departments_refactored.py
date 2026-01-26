# -*- coding: utf-8 -*-
"""
部门管理端点（重构版）
使用统一响应格式
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.schemas import list_response, paginated_response, success_response
from app.models.organization import Department, Employee
from app.models.user import User
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)

from .utils import build_department_tree

router = APIRouter()


@router.get("/departments")
def read_departments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取部门列表"""
    query = db.query(Department)
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    departments = query.order_by(Department.sort_order, Department.dept_code).offset(skip).limit(limit).all()
    
    # 使用统一响应格式
    return list_response(
        items=departments,
        message="获取部门列表成功"
    )


@router.get("/departments/tree")
def get_department_tree(
    db: Session = Depends(deps.get_db),
    is_active: Optional[bool] = Query(None, description="是否只显示启用的部门"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取部门树结构"""
    query = db.query(Department)
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    departments = query.order_by(Department.sort_order, Department.dept_code).all()
    tree = build_department_tree(departments)
    
    # 使用统一响应格式
    return list_response(
        items=tree,
        message="获取部门树成功"
    )


@router.get("/departments/statistics")
def get_department_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取部门统计数据（用于总经理仪表板）"""
    departments = db.query(Department).filter(Department.is_active == True).all()

    result = []
    for dept in departments:
        employee_count = db.query(func.count(Employee.id)).filter(
            Employee.department == dept.dept_name,
            Employee.is_active == True
        ).scalar() or 0

        result.append({
            "id": dept.id,
            "name": dept.dept_name,
            "manager": dept.manager.name if dept.manager else "",
            "employee_count": employee_count,
            "projects": 0,
            "revenue": 0,
            "target": 0,
            "achievement": 0,
            "status": "good",
            "issues": 0,
            "on_time_rate": 90,
            "arrival_rate": 85,
            "pass_rate": 95,
        })

    # 使用统一响应格式
    return success_response(
        data={"departments": result},
        message="获取部门统计成功"
    )


@router.post("/departments")
def create_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_in: DepartmentCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建新部门"""
    department = db.query(Department).filter(Department.dept_code == dept_in.dept_code).first()
    if department:
        raise HTTPException(status_code=400, detail="该部门编码已存在")

    query = db.query(Department).filter(Department.dept_name == dept_in.dept_name)
    if dept_in.parent_id:
        query = query.filter(Department.parent_id == dept_in.parent_id)
    else:
        query = query.filter(Department.parent_id.is_(None))

    existing_dept = query.first()
    if existing_dept:
        raise HTTPException(status_code=400, detail=f"该部门名称已存在（{existing_dept.dept_code}）")

    if dept_in.parent_id:
        parent = db.query(Department).filter(Department.id == dept_in.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="父部门不存在")

        if parent.dept_name in dept_in.dept_name and dept_in.dept_name != parent.dept_name:
            raise HTTPException(
                status_code=400,
                detail=f"部门名称不应包含父部门名称。建议使用：{dept_in.dept_name.replace(parent.dept_name + '-', '').replace(parent.dept_name, '')}",
            )
        level = parent.level + 1
    else:
        level = 1

    department = Department(**dept_in.model_dump())
    department.level = level
    db.add(department)
    db.commit()
    db.refresh(department)
    
    # 使用统一响应格式
    return success_response(
        data=department,
        message="部门创建成功"
    )


@router.get("/departments/{dept_id}")
def read_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
) -> Any:
    """Get department by ID."""
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # 使用统一响应格式
    return success_response(
        data=department,
        message="获取部门信息成功"
    )


@router.put("/departments/{dept_id}")
def update_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    dept_in: DepartmentUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新部门信息"""
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")

    update_data = dept_in.model_dump(exclude_unset=True)

    if 'dept_name' in update_data:
        new_name = update_data['dept_name']
        parent_id = update_data.get('parent_id', department.parent_id)

        query = db.query(Department).filter(
            Department.dept_name == new_name,
            Department.id != dept_id
        )
        if parent_id:
            query = query.filter(Department.parent_id == parent_id)
        else:
            query = query.filter(Department.parent_id.is_(None))

        existing_dept = query.first()
        if existing_dept:
            raise HTTPException(status_code=400, detail=f"该部门名称已存在（{existing_dept.dept_code}）")

        if parent_id:
            parent = db.query(Department).filter(Department.id == parent_id).first()
            if parent and parent.dept_name in new_name and new_name != parent.dept_name:
                raise HTTPException(
                    status_code=400,
                    detail=f"部门名称不应包含父部门名称。建议使用：{new_name.replace(parent.dept_name + '-', '').replace(parent.dept_name, '')}",
                )

    if 'parent_id' in update_data and update_data['parent_id'] != department.parent_id:
        if update_data['parent_id']:
            parent = db.query(Department).filter(Department.id == update_data['parent_id']).first()
            if not parent:
                raise HTTPException(status_code=404, detail="父部门不存在")
            if parent.id == dept_id:
                raise HTTPException(status_code=400, detail="不能将部门设置为自己的子部门")
            department.level = parent.level + 1
        else:
            department.level = 1

    for field, value in update_data.items():
        if field != 'parent_id':
            setattr(department, field, value)

    db.add(department)
    db.commit()
    db.refresh(department)
    
    # 使用统一响应格式
    return success_response(
        data=department,
        message="部门更新成功"
    )


@router.get("/departments/{dept_id}/users")
def get_department_users(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    keyword: Optional[str] = Query(None, description="关键词搜索（用户名/姓名/工号）"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取部门人员列表"""
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")

    query = db.query(User).filter(User.department == department.dept_name)

    if keyword:
        query = query.filter(
            or_(
                User.username.contains(keyword),
                User.real_name.contains(keyword),
                User.employee_no.contains(keyword),
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

    for u in users:
        u.roles = [ur.role.role_name for ur in u.roles] if u.roles else []

    pages = (total + page_size - 1) // page_size
    
    # 使用统一响应格式
    return paginated_response(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        message="获取部门人员列表成功"
    )

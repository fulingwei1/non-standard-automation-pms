# -*- coding: utf-8 -*-
"""
组织单元管理端点（重构版）
使用统一响应格式
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas import list_response, success_response
from app.models.organization import OrganizationUnit, Employee
from app.models.user import User
from app.schemas.organization import (
    OrganizationUnitCreate,
    OrganizationUnitResponse,
    OrganizationUnitUpdate,
)

router = APIRouter()


@router.get("/")
def list_org_units(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    unit_type: Optional[str] = Query(None, description="组织类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取组织单元列表"""
    query = db.query(OrganizationUnit)
    if unit_type:
        query = query.filter(OrganizationUnit.unit_type == unit_type)
    if is_active is not None:
        query = query.filter(OrganizationUnit.is_active == is_active)

    units = (
        query.order_by(OrganizationUnit.sort_order, OrganizationUnit.unit_code)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # 转换为Pydantic模型
    unit_responses = [OrganizationUnitResponse.model_validate(unit) for unit in units]

    # 使用统一响应格式
    return list_response(
        items=unit_responses,
        message="获取组织单元列表成功"
    )


@router.get("/tree")
def get_org_tree(
    db: Session = Depends(deps.get_db),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取组织架构树"""
    query = db.query(OrganizationUnit)
    if is_active is not None:
        query = query.filter(OrganizationUnit.is_active == is_active)

    units = query.order_by(
        OrganizationUnit.sort_order, OrganizationUnit.unit_code
    ).all()

    # 构建树形结构
    unit_dict = {
        u.id: {
            "id": u.id,
            "unit_code": u.unit_code,
            "unit_name": u.unit_name,
            "unit_type": u.unit_type,
            "parent_id": u.parent_id,
            "manager_id": u.manager_id,
            "manager_name": u.manager.name if u.manager else None,
            "level": u.level,
            "sort_order": u.sort_order,
            "is_active": u.is_active,
            "children": [],
        }
        for u in units
    }

    tree = []
    for u_id, u_data in unit_dict.items():
        parent_id = u_data["parent_id"]
        if parent_id and parent_id in unit_dict:
            unit_dict[parent_id]["children"].append(u_data)
        else:
            tree.append(u_data)

    # 使用统一响应格式
    return list_response(
        items=tree,
        message="获取组织架构树成功"
    )


@router.post("/")
def create_org_unit(
    *,
    db: Session = Depends(deps.get_db),
    unit_in: OrganizationUnitCreate,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """创建组织单元"""
    unit = (
        db.query(OrganizationUnit)
        .filter(OrganizationUnit.unit_code == unit_in.unit_code)
        .first()
    )
    if unit:
        raise HTTPException(status_code=400, detail="组织编码已存在")

    # 计算层级和路径
    level = 1
    path = ""
    if unit_in.parent_id:
        parent = (
            db.query(OrganizationUnit)
            .filter(OrganizationUnit.id == unit_in.parent_id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="父组织不存在")
        level = parent.level + 1
        path = f"{parent.path or '/'}{parent.id}/"
    else:
        path = "/"

    unit = OrganizationUnit(**unit_in.model_dump(), level=level, path=path)
    db.add(unit)
    db.commit()
    db.refresh(unit)

    # 转换为Pydantic模型
    unit_response = OrganizationUnitResponse.model_validate(unit)

    # 使用统一响应格式
    return success_response(
        data=unit_response,
        message="组织单元创建成功"
    )


@router.get("/{id}")
def get_org_unit(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取指定组织单元"""
    unit = db.query(OrganizationUnit).filter(OrganizationUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="组织单元不存在")

    # 转换为Pydantic模型
    unit_response = OrganizationUnitResponse.model_validate(unit)

    # 使用统一响应格式
    return success_response(
        data=unit_response,
        message="获取组织单元成功"
    )


@router.put("/{id}")
def update_org_unit(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    unit_in: OrganizationUnitUpdate,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """更新组织单元"""
    unit = db.query(OrganizationUnit).filter(OrganizationUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="组织单元不存在")

    update_data = unit_in.model_dump(exclude_unset=True)

    # 如果修改了父组织，需要重新计算层级和路径
    if "parent_id" in update_data and update_data["parent_id"] != unit.parent_id:
        if update_data["parent_id"]:
            parent = (
                db.query(OrganizationUnit)
                .filter(OrganizationUnit.id == update_data["parent_id"])
                .first()
            )
            if not parent:
                raise HTTPException(status_code=404, detail="父组织不存在")
            unit.level = parent.level + 1
            unit.path = f"{parent.path or '/'}{parent.id}/"
        else:
            unit.level = 1
            unit.path = "/"

    for field, value in update_data.items():
        setattr(unit, field, value)

    db.add(unit)
    db.commit()
    db.refresh(unit)

    # 转换为Pydantic模型
    unit_response = OrganizationUnitResponse.model_validate(unit)

    # 使用统一响应格式
    return success_response(
        data=unit_response,
        message="组织单元更新成功"
    )


@router.delete("/{id}")
def delete_org_unit(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """删除组织单元"""
    unit = db.query(OrganizationUnit).filter(OrganizationUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="组织单元不存在")

    # 检查是否有子组织
    has_children = (
        db.query(OrganizationUnit).filter(OrganizationUnit.parent_id == id).first()
    )
    if has_children:
        raise HTTPException(status_code=400, detail="该组织下有子组织，不能删除")

    db.delete(unit)
    db.commit()

    # 使用统一响应格式
    return success_response(
        data={"id": id},
        message="组织单元删除成功"
    )


@router.get("/{id}/employees")
def get_org_unit_employees(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取组织单元下的员工"""
    unit = db.query(OrganizationUnit).filter(OrganizationUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="组织单元不存在")

    # 查找在该部门下的员工
    from app.schemas.organization import EmployeeResponse
    employees = db.query(Employee).filter(Employee.department == unit.unit_name).all()

    # 转换为Pydantic模型
    emp_responses = [EmployeeResponse.model_validate(emp) for emp in employees]

    # 使用统一响应格式
    return list_response(
        items=emp_responses,
        message="获取组织单元员工成功"
    )

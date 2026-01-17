# -*- coding: utf-8 -*-
"""
角色类型字典管理 API
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models import ProjectMember, ProjectRoleType
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project_role import (
    ProjectRoleTypeCreate,
    ProjectRoleTypeListResponse,
    ProjectRoleTypeResponse,
    ProjectRoleTypeUpdate,
)

router = APIRouter()


@router.get("/types", response_model=ProjectRoleTypeListResponse, summary="获取所有角色类型")
async def get_role_types(
    category: Optional[str] = Query(None, description="角色分类筛选"),
    active_only: bool = Query(True, description="仅显示启用的角色"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:read"))
):
    """获取所有项目角色类型"""
    query = db.query(ProjectRoleType)

    if category:
        query = query.filter(ProjectRoleType.role_category == category)
    if active_only:
        query = query.filter(ProjectRoleType.is_active == True)

    items = query.order_by(ProjectRoleType.sort_order, ProjectRoleType.id).all()

    return ProjectRoleTypeListResponse(
        items=[ProjectRoleTypeResponse.model_validate(item) for item in items],
        total=len(items)
    )


@router.post("/types", response_model=ProjectRoleTypeResponse, summary="创建角色类型")
async def create_role_type(
    data: ProjectRoleTypeCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:create"))
):
    """创建新的项目角色类型（需要管理员权限）"""
    existing = db.query(ProjectRoleType).filter(
        ProjectRoleType.role_code == data.role_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"角色编码 {data.role_code} 已存在")

    role_type = ProjectRoleType(**data.model_dump())
    db.add(role_type)
    db.commit()
    db.refresh(role_type)

    return ProjectRoleTypeResponse.model_validate(role_type)


@router.get("/types/{role_type_id}", response_model=ProjectRoleTypeResponse, summary="获取角色类型详情")
async def get_role_type(
    role_type_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:read"))
):
    """获取单个角色类型详情"""
    role_type = db.query(ProjectRoleType).filter(ProjectRoleType.id == role_type_id).first()
    if not role_type:
        raise HTTPException(status_code=404, detail="角色类型不存在")
    return ProjectRoleTypeResponse.model_validate(role_type)


@router.put("/types/{role_type_id}", response_model=ProjectRoleTypeResponse, summary="更新角色类型")
async def update_role_type(
    role_type_id: int,
    data: ProjectRoleTypeUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:update"))
):
    """更新项目角色类型"""
    role_type = db.query(ProjectRoleType).filter(ProjectRoleType.id == role_type_id).first()
    if not role_type:
        raise HTTPException(status_code=404, detail="角色类型不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role_type, key, value)

    db.commit()
    db.refresh(role_type)

    return ProjectRoleTypeResponse.model_validate(role_type)


@router.delete("/types/{role_type_id}", response_model=MessageResponse, summary="删除角色类型")
async def delete_role_type(
    role_type_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:delete"))
):
    """删除项目角色类型（软删除，设置 is_active=False）"""
    role_type = db.query(ProjectRoleType).filter(ProjectRoleType.id == role_type_id).first()
    if not role_type:
        raise HTTPException(status_code=404, detail="角色类型不存在")

    usage_count = db.query(ProjectMember).filter(
        ProjectMember.role_type_id == role_type_id,
        ProjectMember.is_active == True
    ).count()

    if usage_count > 0:
        role_type.is_active = False
        db.commit()
        return MessageResponse(message=f"角色类型已禁用（有 {usage_count} 个项目正在使用）")
    else:
        db.delete(role_type)
        db.commit()
        return MessageResponse(message="角色类型已删除")

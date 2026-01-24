# -*- coding: utf-8 -*-
"""
项目成员 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.core import security
from app.models.project import ProjectMember, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import (
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse
)
from app.utils.permission_helpers import check_project_access_or_raise


def filter_by_role(query, role: str):
    """自定义角色筛选器"""
    return query.filter(ProjectMember.role_code == role)


def enrich_member_response(member: ProjectMember) -> ProjectMember:
    """填充成员的username和real_name"""
    if member.user:
        member.username = member.user.username
        member.real_name = member.user.real_name
    else:
        member.username = "Unknown"
        member.real_name = "Unknown"
    return member


# 使用项目中心CRUD路由基类创建路由（用于获取基础路由结构）
base_router = create_project_crud_router(
    model=ProjectMember,
    create_schema=ProjectMemberCreate,
    update_schema=ProjectMemberUpdate,
    response_schema=ProjectMemberResponse,
    permission_prefix="project",
    project_id_field="project_id",
    keyword_fields=["remark"],
    default_order_by="created_at",
    default_order_direction="desc",
    custom_filters={
        "role": filter_by_role,
    },
)

# 创建新的router，覆盖所有端点以添加填充用户信息的逻辑
router = APIRouter()


# 覆盖列表端点，添加填充用户信息逻辑
@router.get("/", response_model=PaginatedResponse[ProjectMemberResponse])
def list_project_members(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=100, description="每页数量"),
    keyword: str = Query(None, description="关键词搜索"),
    order_by: str = Query(None, description="排序字段"),
    order_direction: str = Query("desc", description="排序方向 (asc/desc)"),
    role: str = Query(None, description="角色筛选"),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员列表（支持分页、搜索、排序、筛选）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    # 构建查询
    query = db.query(ProjectMember).filter(ProjectMember.project_id == project_id)
    
    # 角色筛选
    if role:
        query = query.filter(ProjectMember.role_code == role)
    
    # 关键词搜索
    if keyword:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                ProjectMember.remark.ilike(f"%{keyword}%"),
            )
        )
    
    # 排序
    order_field = getattr(ProjectMember, order_by or "created_at", None)
    if order_field:
        if order_direction == "asc":
            query = query.order_by(order_field.asc())
        else:
            query = query.order_by(order_field.desc())
    
    # 分页
    total = query.count()
    offset = (page - 1) * page_size
    members = query.offset(offset).limit(page_size).all()
    
    # 填充用户信息
    for member in members:
        enrich_member_response(member)
    
    return PaginatedResponse(
        items=members,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


# 覆盖创建端点，添加重复检查和填充用户信息逻辑
@router.post("/", response_model=ProjectMemberResponse, status_code=201)
def add_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_in: ProjectMemberCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """为项目添加成员（覆盖基类端点，添加重复检查逻辑）"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限在该项目中添加成员"
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否已是项目成员
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_in.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该用户已是项目成员")
    
    # 准备成员数据，强制使用路径中的 project_id
    member_data = member_in.model_dump(exclude_unset=True)
    member_data["project_id"] = project_id
    
    member = ProjectMember(**member_data)
    db.add(member)
    db.commit()
    db.refresh(member)
    
    # 填充用户信息
    return enrich_member_response(member)


# 覆盖详情端点，添加填充用户信息逻辑
@router.get("/{member_id}", response_model=ProjectMemberResponse)
def get_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员详情（覆盖基类端点，填充用户信息）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")
    
    # 填充用户信息
    return enrich_member_response(member)


# 覆盖更新端点，添加填充用户信息逻辑
@router.put("/{member_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    member_in: ProjectMemberUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """更新项目成员信息（覆盖基类端点，填充用户信息）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")
    
    update_data = member_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(member, field):
            setattr(member, field, value)
    
    db.add(member)
    db.commit()
    db.refresh(member)
    
    # 填充用户信息
    return enrich_member_response(member)


# 覆盖删除端点
@router.delete("/{member_id}", status_code=204)
def remove_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
):
    """移除项目成员（覆盖基类端点）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")
    
    db.delete(member)
    db.commit()

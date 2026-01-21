# -*- coding: utf-8 -*-
"""
项目成员 CRUD 操作

适配自 app/api/v1/endpoints/members/crud.py
变更: 路由从 /members/ 改为 /projects/{project_id}/members/
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import (
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberUpdate,
)
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=List[ProjectMemberResponse])
def list_project_members(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    role: Optional[str] = Query(None, description="角色筛选"),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员列表"""
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectMember).filter(ProjectMember.project_id == project_id)

    if role:
        query = query.filter(ProjectMember.role == role)

    members = query.all()

    for m in members:
        m.username = m.user.username if m.user else "Unknown"
        m.real_name = m.user.real_name if m.user else "Unknown"

    return members


@router.post("/", response_model=ProjectMemberResponse, status_code=201)
def add_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_in: ProjectMemberCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """为项目添加成员"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限在该项目中添加成员"
    )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_in.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="该用户已是项目成员")

    member_data = member_in.model_dump()
    member_data["project_id"] = project_id

    member = ProjectMember(**member_data)
    db.add(member)
    db.commit()
    db.refresh(member)

    member.username = user.username
    member.real_name = user.real_name
    return member


@router.get("/{member_id}", response_model=ProjectMemberResponse)
def get_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员详情"""
    check_project_access_or_raise(db, current_user, project_id)

    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.id == member_id, ProjectMember.project_id == project_id)
        .first()
    )

    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    member.username = member.user.username if member.user else "Unknown"
    member.real_name = member.user.real_name if member.user else "Unknown"

    return member


@router.put("/{member_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    member_in: ProjectMemberUpdate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """更新项目成员信息"""
    check_project_access_or_raise(db, current_user, project_id)

    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.id == member_id, ProjectMember.project_id == project_id)
        .first()
    )

    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    update_data = member_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(member, field):
            setattr(member, field, value)

    db.add(member)
    db.commit()
    db.refresh(member)

    member.username = member.user.username if member.user else "Unknown"
    member.real_name = member.user.real_name if member.user else "Unknown"

    return member


@router.delete("/{member_id}", status_code=200)
def remove_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """移除项目成员"""
    check_project_access_or_raise(db, current_user, project_id)

    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.id == member_id, ProjectMember.project_id == project_id)
        .first()
    )

    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    db.delete(member)
    db.commit()

    return ResponseModel(code=200, message="项目成员已移除")

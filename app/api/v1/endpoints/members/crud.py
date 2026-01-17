# -*- coding: utf-8 -*-
"""
项目成员 CRUD 端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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

router = APIRouter()


@router.get("/", response_model=List[ProjectMemberResponse])
def read_members(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Retrieve project members.
    """
    query = db.query(ProjectMember)

    # 如果指定了project_id，检查访问权限
    if project_id:
        from app.utils.permission_helpers import check_project_access_or_raise
        check_project_access_or_raise(db, current_user, project_id)
        query = query.filter(ProjectMember.project_id == project_id)
    else:
        # 如果没有指定project_id，根据用户权限过滤项目
        from app.services.data_scope_service import DataScopeService
        user_project_ids = DataScopeService.get_user_project_ids(db, current_user.id)
        if not current_user.is_superuser:
            data_scope = DataScopeService.get_user_data_scope(db, current_user)
            if data_scope == "OWN":
                user_managed_projects = db.query(Project.id).filter(
                    (Project.created_by == current_user.id) | (Project.pm_id == current_user.id)
                ).all()
                user_project_ids = user_project_ids | {p[0] for p in user_managed_projects}
            elif data_scope == "DEPT":
                from app.models.organization import Department
                if current_user.department:
                    dept = db.query(Department).filter(Department.dept_name == current_user.department).first()
                    if dept:
                        dept_projects = db.query(Project.id).filter(Project.dept_id == dept.id).all()
                        user_project_ids = user_project_ids | {p[0] for p in dept_projects}

        if user_project_ids:
            query = query.filter(ProjectMember.project_id.in_(user_project_ids))
        elif not current_user.is_superuser:
            query = query.filter(ProjectMember.id == -1)

    members = query.offset(skip).limit(limit).all()

    # Map user info
    for m in members:
        m.username = m.user.username if m.user else "Unknown"
        m.real_name = m.user.real_name if m.user else "Unknown"

    return members


@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
def get_project_members(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目的成员列表
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()

    # 补充用户信息
    for m in members:
        m.username = m.user.username if m.user else "Unknown"
        m.real_name = m.user.real_name if m.user else "Unknown"

    return members


@router.post("/", response_model=ProjectMemberResponse)
def add_member(
    *,
    db: Session = Depends(deps.get_db),
    member_in: ProjectMemberCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加项目成员
    """
    # Check project exists
    project = db.query(Project).filter(Project.id == member_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # Check user exists
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # Check if already a member
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == member_in.project_id,
            ProjectMember.user_id == member_in.user_id,
        )
        .first()
    )
    if member:
        raise HTTPException(
            status_code=400,
            detail="该用户已是项目成员",
        )

    member = ProjectMember(**member_in.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)

    member.username = user.username
    member.real_name = user.real_name
    return member


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
def add_project_member(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    member_in: ProjectMemberCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为项目添加成员
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中添加成员")

    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已经是成员
    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_in.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="该用户已是项目成员",
        )

    member_data = member_in.model_dump()
    member_data['project_id'] = project_id

    member = ProjectMember(**member_data)
    db.add(member)
    db.commit()
    db.refresh(member)

    member.username = user.username
    member.real_name = user.real_name
    return member


@router.put("/project-members/{member_id}", response_model=ProjectMemberResponse)
def update_project_member(
    *,
    db: Session = Depends(deps.get_db),
    member_id: int,
    member_in: ProjectMemberUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目成员角色和分配信息
    """
    member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    update_data = member_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(member, field):
            setattr(member, field, value)

    db.add(member)
    db.commit()
    db.refresh(member)

    # 补充用户信息
    member.username = member.user.username if member.user else "Unknown"
    member.real_name = member.user.real_name if member.user else "Unknown"

    return member


@router.delete("/{member_id}", status_code=200)
def remove_member(
    *,
    db: Session = Depends(deps.get_db),
    member_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    移除项目成员
    """
    member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    db.delete(member)
    db.commit()

    return ResponseModel(code=200, message="项目成员已移除")

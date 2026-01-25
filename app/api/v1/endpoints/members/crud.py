# -*- coding: utf-8 -*-
"""
项目成员全局 CRUD 端点

⚠️ 所有端点已废弃，请使用项目中心端点：
    /api/v1/projects/{project_id}/members/
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


def _enrich_member(member: ProjectMember) -> ProjectMember:
    """填充成员的用户信息"""
    member.username = member.user.username if member.user else "Unknown"
    member.real_name = member.user.real_name if member.user else "Unknown"
    return member


@router.get("/", response_model=List[ProjectMemberResponse], deprecated=True)
def read_members(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 GET /projects/{project_id}/members/

    获取项目成员列表
    """
    from app.utils.permission_helpers import (
        check_project_access_or_raise,
        filter_by_project_access,
    )

    query = db.query(ProjectMember)

    if project_id:
        check_project_access_or_raise(db, current_user, project_id)
        query = query.filter(ProjectMember.project_id == project_id)
    else:
        query = filter_by_project_access(
            db, query, current_user, ProjectMember.project_id
        )

    members = query.offset(skip).limit(limit).all()

    for m in members:
        _enrich_member(m)

    return members


@router.post("/", response_model=ProjectMemberResponse, deprecated=True)
def add_member(
    *,
    db: Session = Depends(deps.get_db),
    member_in: ProjectMemberCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 POST /projects/{project_id}/members/

    添加项目成员
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project_id = member_in.project_id
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id 是必需的")

    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限在该项目中添加成员"
    )

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

    member = ProjectMember(**member_in.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)

    return _enrich_member(member)


@router.put("/project-members/{member_id}", response_model=ProjectMemberResponse, deprecated=True)
def update_project_member(
    *,
    db: Session = Depends(deps.get_db),
    member_id: int,
    member_in: ProjectMemberUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 PUT /projects/{project_id}/members/{member_id}

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

    return _enrich_member(member)


@router.delete("/{member_id}", status_code=200, deprecated=True)
def remove_member(
    *,
    db: Session = Depends(deps.get_db),
    member_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 DELETE /projects/{project_id}/members/{member_id}

    移除项目成员
    """
    member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    db.delete(member)
    db.commit()

    return ResponseModel(code=200, message="项目成员已移除")

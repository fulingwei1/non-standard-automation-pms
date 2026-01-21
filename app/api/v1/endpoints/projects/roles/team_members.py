# -*- coding: utf-8 -*-
"""
团队成员管理 API

路由: /projects/{project_id}/roles/leads/{member_id}/team/
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models import ProjectMember
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project_role import (
    TeamMemberCreate,
    TeamMemberListResponse,
    TeamMemberResponse,
    UserBrief,
)

router = APIRouter()


@router.get(
    "/leads/{member_id}/team",
    response_model=TeamMemberListResponse,
    summary="获取团队成员",
)
async def get_team_members(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="负责人成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:read")),
):
    """获取负责人的团队成员列表"""
    lead = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
            ProjectMember.is_lead == True,
        )
        .first()
    )

    if not lead:
        raise HTTPException(status_code=404, detail="负责人不存在")

    members = (
        db.query(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .filter(
            ProjectMember.lead_member_id == member_id, ProjectMember.is_active == True
        )
        .all()
    )

    items = [
        TeamMemberResponse(
            id=m.id,
            project_id=m.project_id,
            user_id=m.user_id,
            user=UserBrief.model_validate(m.user) if m.user else None,
            role_code=m.role_code,
            role_type_id=m.role_type_id,
            is_lead=False,
            lead_member_id=m.lead_member_id,
            allocation_pct=m.allocation_pct,
            start_date=m.start_date,
            end_date=m.end_date,
            machine_id=m.machine_id,
            remark=m.remark,
            is_active=m.is_active,
            created_at=m.created_at,
        )
        for m in members
    ]

    return TeamMemberListResponse(items=items, total=len(items))


@router.post(
    "/leads/{member_id}/team",
    response_model=TeamMemberResponse,
    summary="添加团队成员",
)
async def add_team_member(
    data: TeamMemberCreate,
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="负责人成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:assign")),
):
    """为负责人添加团队成员"""
    lead = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
            ProjectMember.is_lead == True,
        )
        .first()
    )

    if not lead:
        raise HTTPException(status_code=404, detail="负责人不存在")

    if lead.role_type and not lead.role_type.can_have_team:
        raise HTTPException(status_code=400, detail="该角色不支持带团队")

    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == data.user_id,
            ProjectMember.lead_member_id == member_id,
            ProjectMember.is_active == True,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="该用户已是团队成员")

    member = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        role_code=lead.role_code,
        role_type_id=lead.role_type_id,
        is_lead=False,
        lead_member_id=member_id,
        allocation_pct=data.allocation_pct,
        start_date=data.start_date,
        end_date=data.end_date,
        machine_id=data.machine_id,
        remark=data.remark,
        created_by=current_user.id,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return TeamMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        user=UserBrief.model_validate(member.user) if member.user else None,
        role_code=member.role_code,
        role_type_id=member.role_type_id,
        is_lead=False,
        lead_member_id=member.lead_member_id,
        allocation_pct=member.allocation_pct,
        start_date=member.start_date,
        end_date=member.end_date,
        machine_id=member.machine_id,
        remark=member.remark,
        is_active=member.is_active,
        created_at=member.created_at,
    )


@router.delete(
    "/leads/{lead_id}/team/{member_id}",
    response_model=MessageResponse,
    summary="移除团队成员",
)
async def remove_team_member(
    project_id: int = Path(..., description="项目ID"),
    lead_id: int = Path(..., description="负责人成员ID"),
    member_id: int = Path(..., description="团队成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:update")),
):
    """从团队中移除成员"""
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
            ProjectMember.lead_member_id == lead_id,
        )
        .first()
    )

    if not member:
        raise HTTPException(status_code=404, detail="团队成员不存在")

    member.is_active = False
    member.lead_member_id = None
    db.commit()

    return MessageResponse(message="已移除团队成员")

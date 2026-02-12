# -*- coding: utf-8 -*-
"""
项目角色概览 API

路由: /projects/{project_id}/roles/overview
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models import Project, ProjectMember, ProjectRoleConfig, ProjectRoleType
from app.models.user import User
from app.schemas.project_role import (
    ProjectLeadWithTeamResponse,
    ProjectRoleConfigResponse,
    ProjectRoleOverviewResponse,
    ProjectRoleTypeResponse,
    TeamMemberResponse,
    UserBrief,
)

router = APIRouter()


@router.get(
    "/overview",
    response_model=List[ProjectRoleOverviewResponse],
    summary="获取项目角色概览",
)
async def get_project_role_overview(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:read")),
):
    """获取项目角色概览（包含角色类型、配置、负责人信息）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    role_types = (
        db.query(ProjectRoleType)
        .filter(ProjectRoleType.is_active)
        .order_by(ProjectRoleType.sort_order)
        .all()
    )

    configs = {
        c.role_type_id: c
        for c in db.query(ProjectRoleConfig)
        .filter(ProjectRoleConfig.project_id == project_id)
        .all()
    }

    leads = {
        l.role_type_id: l
        for l in db.query(ProjectMember)
        .options(joinedload(ProjectMember.user), joinedload(ProjectMember.team_members))
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_lead,
            ProjectMember.is_active,
        )
        .all()
    }

    result = []
    for rt in role_types:
        config = configs.get(rt.id)
        lead = leads.get(rt.id)

        is_enabled = config.is_enabled if config else rt.is_required
        is_required = config.is_required if config else rt.is_required

        lead_response = None
        if lead:
            team_count = len([m for m in lead.team_members if m.is_active])
            team_members = [
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
                for m in lead.team_members
                if m.is_active
            ]

            lead_response = ProjectLeadWithTeamResponse(
                id=lead.id,
                project_id=lead.project_id,
                user_id=lead.user_id,
                user=UserBrief.model_validate(lead.user) if lead.user else None,
                role_code=lead.role_code,
                role_type_id=lead.role_type_id,
                role_type=ProjectRoleTypeResponse.model_validate(rt),
                is_lead=True,
                allocation_pct=lead.allocation_pct,
                start_date=lead.start_date,
                end_date=lead.end_date,
                machine_id=lead.machine_id,
                remark=lead.remark,
                team_count=team_count,
                is_active=lead.is_active,
                created_at=lead.created_at,
                updated_at=lead.updated_at,
                team_members=team_members,
            )

        result.append(
            ProjectRoleOverviewResponse(
                role_type=ProjectRoleTypeResponse.model_validate(rt),
                config=(
                    ProjectRoleConfigResponse.model_validate(config) if config else None
                ),
                lead=lead_response,
                is_enabled=is_enabled,
                is_required=is_required,
                has_lead=lead is not None,
            )
        )

    return result

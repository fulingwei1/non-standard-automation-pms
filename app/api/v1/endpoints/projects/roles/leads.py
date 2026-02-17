# -*- coding: utf-8 -*-
"""
项目负责人管理 API

路由: /projects/{project_id}/roles/leads/
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models import Project, ProjectMember, ProjectRoleType
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project_role import (
    ProjectLeadCreate,
    ProjectLeadListResponse,
    ProjectLeadResponse,
    ProjectLeadUpdate,
    ProjectRoleTypeResponse,
    UserBrief,
)
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


@router.get("/leads", response_model=ProjectLeadListResponse, summary="获取项目负责人列表")
async def get_project_leads(
    project_id: int = Path(..., description="项目ID"),
    include_team: bool = Query(False, description="是否包含团队成员"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:read")),
):
    """获取项目所有负责人"""
    project = get_or_404(db, Project, project_id, detail="项目不存在")

    query = (
        db.query(ProjectMember)
        .options(joinedload(ProjectMember.user), joinedload(ProjectMember.role_type))
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_lead,
            ProjectMember.is_active,
        )
    )

    leads = query.all()

    items = []
    for lead in leads:
        team_count = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.lead_member_id == lead.id, ProjectMember.is_active
            )
            .count()
        )

        lead_dict = {
            "id": lead.id,
            "project_id": lead.project_id,
            "user_id": lead.user_id,
            "user": UserBrief.model_validate(lead.user) if lead.user else None,
            "role_code": lead.role_code,
            "role_type_id": lead.role_type_id,
            "role_type": (
                ProjectRoleTypeResponse.model_validate(lead.role_type)
                if lead.role_type
                else None
            ),
            "is_lead": True,
            "allocation_pct": lead.allocation_pct,
            "start_date": lead.start_date,
            "end_date": lead.end_date,
            "machine_id": lead.machine_id,
            "remark": lead.remark,
            "team_count": team_count,
            "is_active": lead.is_active,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at,
        }
        items.append(ProjectLeadResponse(**lead_dict))

    return ProjectLeadListResponse(items=items, total=len(items))


@router.post("/leads", response_model=ProjectLeadResponse, summary="指定项目负责人")
async def create_project_lead(
    data: ProjectLeadCreate,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:assign")),
):
    """为项目指定负责人"""
    project = get_or_404(db, Project, project_id, detail="项目不存在")

    role_type = (
        db.query(ProjectRoleType).filter(ProjectRoleType.id == data.role_type_id).first()
    )
    if not role_type:
        raise HTTPException(status_code=404, detail="角色类型不存在")

    user = get_or_404(db, User, data.user_id, detail="用户不存在")

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.role_type_id == data.role_type_id,
            ProjectMember.is_lead,
            ProjectMember.is_active,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"该项目已有 {role_type.role_name}")

    lead = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        role_code=role_type.role_code,
        role_type_id=data.role_type_id,
        is_lead=True,
        allocation_pct=data.allocation_pct,
        start_date=data.start_date,
        end_date=data.end_date,
        machine_id=data.machine_id,
        remark=data.remark,
        created_by=current_user.id,
    )
    save_obj(db, lead)

    db.refresh(lead)
    lead.user
    lead.role_type

    return ProjectLeadResponse(
        id=lead.id,
        project_id=lead.project_id,
        user_id=lead.user_id,
        user=UserBrief.model_validate(lead.user) if lead.user else None,
        role_code=lead.role_code,
        role_type_id=lead.role_type_id,
        role_type=(
            ProjectRoleTypeResponse.model_validate(lead.role_type)
            if lead.role_type
            else None
        ),
        is_lead=True,
        allocation_pct=lead.allocation_pct,
        start_date=lead.start_date,
        end_date=lead.end_date,
        machine_id=lead.machine_id,
        remark=lead.remark,
        team_count=0,
        is_active=lead.is_active,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.put(
    "/leads/{member_id}", response_model=ProjectLeadResponse, summary="更新项目负责人"
)
async def update_project_lead(
    data: ProjectLeadUpdate,
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:update")),
):
    """更新项目负责人信息"""
    lead = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
            ProjectMember.is_lead,
        )
        .first()
    )

    if not lead:
        raise HTTPException(status_code=404, detail="负责人不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lead, key, value)

    db.commit()
    db.refresh(lead)

    team_count = (
        db.query(ProjectMember)
        .filter(ProjectMember.lead_member_id == lead.id, ProjectMember.is_active)
        .count()
    )

    return ProjectLeadResponse(
        id=lead.id,
        project_id=lead.project_id,
        user_id=lead.user_id,
        user=UserBrief.model_validate(lead.user) if lead.user else None,
        role_code=lead.role_code,
        role_type_id=lead.role_type_id,
        role_type=(
            ProjectRoleTypeResponse.model_validate(lead.role_type)
            if lead.role_type
            else None
        ),
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
    )


@router.delete(
    "/leads/{member_id}", response_model=MessageResponse, summary="移除项目负责人"
)
async def remove_project_lead(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:update")),
):
    """移除项目负责人"""
    lead = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
            ProjectMember.is_lead,
        )
        .first()
    )

    if not lead:
        raise HTTPException(status_code=404, detail="负责人不存在")

    team_count = (
        db.query(ProjectMember)
        .filter(ProjectMember.lead_member_id == member_id, ProjectMember.is_active)
        .count()
    )

    if team_count > 0:
        db.query(ProjectMember).filter(
            ProjectMember.lead_member_id == member_id
        ).update({"lead_member_id": None})

    lead.is_active = False
    db.commit()

    return MessageResponse(
        message=f"已移除负责人{', 其团队成员已解除关联' if team_count > 0 else ''}"
    )

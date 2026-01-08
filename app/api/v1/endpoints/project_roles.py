# -*- coding: utf-8 -*-
"""
项目角色类型与负责人管理 API

包含：
1. 角色类型字典管理（系统管理员）
2. 项目角色配置管理（项目管理员）
3. 项目负责人管理（项目经理）
4. 团队成员管理（负责人）
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from app.api import deps
from app.models import (
    ProjectRoleType, ProjectRoleConfig, ProjectMember,
    Project, User
)
from app.schemas.project_role import (
    ProjectRoleTypeCreate, ProjectRoleTypeUpdate, ProjectRoleTypeResponse, ProjectRoleTypeListResponse,
    ProjectRoleConfigCreate, ProjectRoleConfigUpdate, ProjectRoleConfigBatchUpdate,
    ProjectRoleConfigResponse, ProjectRoleConfigListResponse,
    ProjectLeadCreate, ProjectLeadUpdate, ProjectLeadResponse, ProjectLeadListResponse,
    TeamMemberCreate, TeamMemberResponse, TeamMemberListResponse,
    ProjectLeadWithTeamResponse, ProjectRoleOverviewResponse, UserBrief
)
from app.schemas.common import MessageResponse


router = APIRouter()


# ===========================
# 角色类型字典管理 API
# ===========================

@router.get("/types", response_model=ProjectRoleTypeListResponse, summary="获取所有角色类型")
async def get_role_types(
    category: Optional[str] = Query(None, description="角色分类筛选"),
    active_only: bool = Query(True, description="仅显示启用的角色"),
    db: Session = Depends(deps.get_db)
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
    current_user: User = Depends(deps.get_current_user)
):
    """创建新的项目角色类型（需要管理员权限）"""
    # 检查编码是否重复
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
    db: Session = Depends(deps.get_db)
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
    current_user: User = Depends(deps.get_current_user)
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
    current_user: User = Depends(deps.get_current_user)
):
    """删除项目角色类型（软删除，设置 is_active=False）"""
    role_type = db.query(ProjectRoleType).filter(ProjectRoleType.id == role_type_id).first()
    if not role_type:
        raise HTTPException(status_code=404, detail="角色类型不存在")

    # 检查是否有项目在使用该角色
    usage_count = db.query(ProjectMember).filter(
        ProjectMember.role_type_id == role_type_id,
        ProjectMember.is_active == True
    ).count()

    if usage_count > 0:
        # 软删除
        role_type.is_active = False
        db.commit()
        return MessageResponse(message=f"角色类型已禁用（有 {usage_count} 个项目正在使用）")
    else:
        # 硬删除
        db.delete(role_type)
        db.commit()
        return MessageResponse(message="角色类型已删除")


# ===========================
# 项目角色配置 API
# ===========================

@router.get("/projects/{project_id}/role-configs", response_model=ProjectRoleConfigListResponse, summary="获取项目角色配置")
async def get_project_role_configs(
    project_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取项目的角色配置列表"""
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取配置
    configs = db.query(ProjectRoleConfig).options(
        joinedload(ProjectRoleConfig.role_type)
    ).filter(
        ProjectRoleConfig.project_id == project_id
    ).all()

    return ProjectRoleConfigListResponse(
        items=[ProjectRoleConfigResponse.model_validate(c) for c in configs],
        total=len(configs)
    )


@router.post("/projects/{project_id}/role-configs/init", response_model=ProjectRoleConfigListResponse, summary="初始化项目角色配置")
async def init_project_role_configs(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """从系统默认配置初始化项目角色配置"""
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查是否已初始化
    existing = db.query(ProjectRoleConfig).filter(
        ProjectRoleConfig.project_id == project_id
    ).count()
    if existing > 0:
        raise HTTPException(status_code=400, detail="项目已初始化角色配置")

    # 获取所有启用的角色类型
    role_types = db.query(ProjectRoleType).filter(
        ProjectRoleType.is_active == True
    ).all()

    # 创建配置
    configs = []
    for rt in role_types:
        config = ProjectRoleConfig(
            project_id=project_id,
            role_type_id=rt.id,
            is_enabled=rt.is_required,  # 必需角色默认启用
            is_required=rt.is_required,
            created_by=current_user.id
        )
        db.add(config)
        configs.append(config)

    db.commit()

    # 刷新获取关联数据
    for c in configs:
        db.refresh(c)

    return ProjectRoleConfigListResponse(
        items=[ProjectRoleConfigResponse.model_validate(c) for c in configs],
        total=len(configs)
    )


@router.put("/projects/{project_id}/role-configs", response_model=ProjectRoleConfigListResponse, summary="批量更新项目角色配置")
async def update_project_role_configs(
    project_id: int,
    data: ProjectRoleConfigBatchUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """批量更新项目角色配置"""
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    configs = []
    for config_data in data.configs:
        # 查找或创建配置
        config = db.query(ProjectRoleConfig).filter(
            ProjectRoleConfig.project_id == project_id,
            ProjectRoleConfig.role_type_id == config_data.role_type_id
        ).first()

        if config:
            # 更新
            config.is_enabled = config_data.is_enabled
            config.is_required = config_data.is_required
            config.remark = config_data.remark
        else:
            # 创建
            config = ProjectRoleConfig(
                project_id=project_id,
                role_type_id=config_data.role_type_id,
                is_enabled=config_data.is_enabled,
                is_required=config_data.is_required,
                remark=config_data.remark,
                created_by=current_user.id
            )
            db.add(config)

        configs.append(config)

    db.commit()

    # 刷新获取关联数据
    for c in configs:
        db.refresh(c)

    return ProjectRoleConfigListResponse(
        items=[ProjectRoleConfigResponse.model_validate(c) for c in configs],
        total=len(configs)
    )


# ===========================
# 项目负责人管理 API
# ===========================

@router.get("/projects/{project_id}/leads", response_model=ProjectLeadListResponse, summary="获取项目负责人列表")
async def get_project_leads(
    project_id: int,
    include_team: bool = Query(False, description="是否包含团队成员"),
    db: Session = Depends(deps.get_db)
):
    """获取项目所有负责人"""
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取负责人
    query = db.query(ProjectMember).options(
        joinedload(ProjectMember.user),
        joinedload(ProjectMember.role_type)
    ).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.is_lead == True,
        ProjectMember.is_active == True
    )

    leads = query.all()

    items = []
    for lead in leads:
        # 计算团队成员数量
        team_count = db.query(ProjectMember).filter(
            ProjectMember.lead_member_id == lead.id,
            ProjectMember.is_active == True
        ).count()

        lead_dict = {
            "id": lead.id,
            "project_id": lead.project_id,
            "user_id": lead.user_id,
            "user": UserBrief.model_validate(lead.user) if lead.user else None,
            "role_code": lead.role_code,
            "role_type_id": lead.role_type_id,
            "role_type": ProjectRoleTypeResponse.model_validate(lead.role_type) if lead.role_type else None,
            "is_lead": True,
            "allocation_pct": lead.allocation_pct,
            "start_date": lead.start_date,
            "end_date": lead.end_date,
            "machine_id": lead.machine_id,
            "remark": lead.remark,
            "team_count": team_count,
            "is_active": lead.is_active,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at
        }
        items.append(ProjectLeadResponse(**lead_dict))

    return ProjectLeadListResponse(items=items, total=len(items))


@router.post("/projects/{project_id}/leads", response_model=ProjectLeadResponse, summary="指定项目负责人")
async def create_project_lead(
    project_id: int,
    data: ProjectLeadCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """为项目指定负责人"""
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查角色类型是否存在
    role_type = db.query(ProjectRoleType).filter(
        ProjectRoleType.id == data.role_type_id
    ).first()
    if not role_type:
        raise HTTPException(status_code=404, detail="角色类型不存在")

    # 检查用户是否存在
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已有该角色的负责人
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.role_type_id == data.role_type_id,
        ProjectMember.is_lead == True,
        ProjectMember.is_active == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"该项目已有 {role_type.role_name}")

    # 创建负责人记录
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
        created_by=current_user.id
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # 加载关联
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
        role_type=ProjectRoleTypeResponse.model_validate(lead.role_type) if lead.role_type else None,
        is_lead=True,
        allocation_pct=lead.allocation_pct,
        start_date=lead.start_date,
        end_date=lead.end_date,
        machine_id=lead.machine_id,
        remark=lead.remark,
        team_count=0,
        is_active=lead.is_active,
        created_at=lead.created_at,
        updated_at=lead.updated_at
    )


@router.put("/projects/{project_id}/leads/{member_id}", response_model=ProjectLeadResponse, summary="更新项目负责人")
async def update_project_lead(
    project_id: int,
    member_id: int,
    data: ProjectLeadUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新项目负责人信息"""
    lead = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
        ProjectMember.is_lead == True
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="负责人不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lead, key, value)

    db.commit()
    db.refresh(lead)

    team_count = db.query(ProjectMember).filter(
        ProjectMember.lead_member_id == lead.id,
        ProjectMember.is_active == True
    ).count()

    return ProjectLeadResponse(
        id=lead.id,
        project_id=lead.project_id,
        user_id=lead.user_id,
        user=UserBrief.model_validate(lead.user) if lead.user else None,
        role_code=lead.role_code,
        role_type_id=lead.role_type_id,
        role_type=ProjectRoleTypeResponse.model_validate(lead.role_type) if lead.role_type else None,
        is_lead=True,
        allocation_pct=lead.allocation_pct,
        start_date=lead.start_date,
        end_date=lead.end_date,
        machine_id=lead.machine_id,
        remark=lead.remark,
        team_count=team_count,
        is_active=lead.is_active,
        created_at=lead.created_at,
        updated_at=lead.updated_at
    )


@router.delete("/projects/{project_id}/leads/{member_id}", response_model=MessageResponse, summary="移除项目负责人")
async def remove_project_lead(
    project_id: int,
    member_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """移除项目负责人"""
    lead = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
        ProjectMember.is_lead == True
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="负责人不存在")

    # 检查是否有团队成员
    team_count = db.query(ProjectMember).filter(
        ProjectMember.lead_member_id == member_id,
        ProjectMember.is_active == True
    ).count()

    if team_count > 0:
        # 先将团队成员的 lead_member_id 置空
        db.query(ProjectMember).filter(
            ProjectMember.lead_member_id == member_id
        ).update({"lead_member_id": None})

    # 软删除负责人
    lead.is_active = False
    db.commit()

    return MessageResponse(message=f"已移除负责人{', 其团队成员已解除关联' if team_count > 0 else ''}")


# ===========================
# 团队成员管理 API
# ===========================

@router.get("/projects/{project_id}/leads/{member_id}/team", response_model=TeamMemberListResponse, summary="获取团队成员")
async def get_team_members(
    project_id: int,
    member_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取负责人的团队成员列表"""
    # 检查负责人是否存在
    lead = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
        ProjectMember.is_lead == True
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="负责人不存在")

    # 获取团队成员
    members = db.query(ProjectMember).options(
        joinedload(ProjectMember.user)
    ).filter(
        ProjectMember.lead_member_id == member_id,
        ProjectMember.is_active == True
    ).all()

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
            created_at=m.created_at
        )
        for m in members
    ]

    return TeamMemberListResponse(items=items, total=len(items))


@router.post("/projects/{project_id}/leads/{member_id}/team", response_model=TeamMemberResponse, summary="添加团队成员")
async def add_team_member(
    project_id: int,
    member_id: int,
    data: TeamMemberCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """为负责人添加团队成员"""
    # 检查负责人是否存在
    lead = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
        ProjectMember.is_lead == True
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="负责人不存在")

    # 检查角色类型是否允许带团队
    if lead.role_type and not lead.role_type.can_have_team:
        raise HTTPException(status_code=400, detail="该角色不支持带团队")

    # 检查用户是否存在
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已是团队成员
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == data.user_id,
        ProjectMember.lead_member_id == member_id,
        ProjectMember.is_active == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该用户已是团队成员")

    # 创建团队成员
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
        created_by=current_user.id
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
        created_at=member.created_at
    )


@router.delete("/projects/{project_id}/leads/{lead_id}/team/{member_id}", response_model=MessageResponse, summary="移除团队成员")
async def remove_team_member(
    project_id: int,
    lead_id: int,
    member_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """从团队中移除成员"""
    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
        ProjectMember.lead_member_id == lead_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="团队成员不存在")

    # 软删除
    member.is_active = False
    member.lead_member_id = None
    db.commit()

    return MessageResponse(message="已移除团队成员")


# ===========================
# 项目角色概览 API
# ===========================

@router.get("/projects/{project_id}/role-overview", response_model=List[ProjectRoleOverviewResponse], summary="获取项目角色概览")
async def get_project_role_overview(
    project_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取项目角色概览（包含角色类型、配置、负责人信息）"""
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取所有启用的角色类型
    role_types = db.query(ProjectRoleType).filter(
        ProjectRoleType.is_active == True
    ).order_by(ProjectRoleType.sort_order).all()

    # 获取项目的角色配置
    configs = {
        c.role_type_id: c
        for c in db.query(ProjectRoleConfig).filter(
            ProjectRoleConfig.project_id == project_id
        ).all()
    }

    # 获取项目负责人
    leads = {
        l.role_type_id: l
        for l in db.query(ProjectMember).options(
            joinedload(ProjectMember.user),
            joinedload(ProjectMember.team_members)
        ).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_lead == True,
            ProjectMember.is_active == True
        ).all()
    }

    result = []
    for rt in role_types:
        config = configs.get(rt.id)
        lead = leads.get(rt.id)

        # 如果没有配置，使用默认值
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
                    created_at=m.created_at
                )
                for m in lead.team_members if m.is_active
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
                team_members=team_members
            )

        result.append(ProjectRoleOverviewResponse(
            role_type=ProjectRoleTypeResponse.model_validate(rt),
            config=ProjectRoleConfigResponse.model_validate(config) if config else None,
            lead=lead_response,
            is_enabled=is_enabled,
            is_required=is_required,
            has_lead=lead is not None
        ))

    return result

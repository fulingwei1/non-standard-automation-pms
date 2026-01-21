# -*- coding: utf-8 -*-
"""
项目角色配置管理 API

路由: /projects/{project_id}/roles/configs/
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models import Project, ProjectRoleConfig, ProjectRoleType
from app.models.user import User
from app.schemas.project_role import (
    ProjectRoleConfigBatchUpdate,
    ProjectRoleConfigListResponse,
    ProjectRoleConfigResponse,
)

router = APIRouter()


@router.get(
    "/configs", response_model=ProjectRoleConfigListResponse, summary="获取项目角色配置"
)
async def get_project_role_configs(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:read")),
):
    """获取项目的角色配置列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    configs = (
        db.query(ProjectRoleConfig)
        .options(joinedload(ProjectRoleConfig.role_type))
        .filter(ProjectRoleConfig.project_id == project_id)
        .all()
    )

    return ProjectRoleConfigListResponse(
        items=[ProjectRoleConfigResponse.model_validate(c) for c in configs],
        total=len(configs),
    )


@router.post(
    "/configs/init",
    response_model=ProjectRoleConfigListResponse,
    summary="初始化项目角色配置",
)
async def init_project_role_configs(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:create")),
):
    """从系统默认配置初始化项目角色配置"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    existing = (
        db.query(ProjectRoleConfig)
        .filter(ProjectRoleConfig.project_id == project_id)
        .count()
    )
    if existing > 0:
        raise HTTPException(status_code=400, detail="项目已初始化角色配置")

    role_types = (
        db.query(ProjectRoleType).filter(ProjectRoleType.is_active == True).all()
    )

    configs = []
    for rt in role_types:
        config = ProjectRoleConfig(
            project_id=project_id,
            role_type_id=rt.id,
            is_enabled=rt.is_required,
            is_required=rt.is_required,
            created_by=current_user.id,
        )
        db.add(config)
        configs.append(config)

    db.commit()

    for c in configs:
        db.refresh(c)

    return ProjectRoleConfigListResponse(
        items=[ProjectRoleConfigResponse.model_validate(c) for c in configs],
        total=len(configs),
    )


@router.put(
    "/configs",
    response_model=ProjectRoleConfigListResponse,
    summary="批量更新项目角色配置",
)
async def update_project_role_configs(
    data: ProjectRoleConfigBatchUpdate,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_role:update")),
):
    """批量更新项目角色配置"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    configs = []
    for config_data in data.configs:
        config = (
            db.query(ProjectRoleConfig)
            .filter(
                ProjectRoleConfig.project_id == project_id,
                ProjectRoleConfig.role_type_id == config_data.role_type_id,
            )
            .first()
        )

        if config:
            config.is_enabled = config_data.is_enabled
            config.is_required = config_data.is_required
            config.remark = config_data.remark
        else:
            config = ProjectRoleConfig(
                project_id=project_id,
                role_type_id=config_data.role_type_id,
                is_enabled=config_data.is_enabled,
                is_required=config_data.is_required,
                remark=config_data.remark,
                created_by=current_user.id,
            )
            db.add(config)

        configs.append(config)

    db.commit()

    for c in configs:
        db.refresh(c)

    return ProjectRoleConfigListResponse(
        items=[ProjectRoleConfigResponse.model_validate(c) for c in configs],
        total=len(configs),
    )

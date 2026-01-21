# -*- coding: utf-8 -*-
"""
项目阶段 CRUD 操作

路由: /projects/{project_id}/stages/
提供项目视角的阶段管理
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.stage_instance import ProjectStageInstance
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.stage_template import (
    InitializeProjectStagesRequest,
    ProjectProgressResponse,
    ProjectStageInstanceResponse,
)
from app.services.stage_instance import StageInstanceService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=List[ProjectStageInstanceResponse])
def list_project_stages(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目的所有阶段实例"""
    check_project_access_or_raise(db, current_user, project_id)

    stages = (
        db.query(ProjectStageInstance)
        .filter(ProjectStageInstance.project_id == project_id)
        .order_by(ProjectStageInstance.sequence)
        .all()
    )
    return stages


@router.get("/progress", response_model=ProjectProgressResponse)
def get_project_stages_progress(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目阶段进度概览"""
    check_project_access_or_raise(db, current_user, project_id)

    service = StageInstanceService(db)
    return service.get_project_progress(project_id)


@router.post("/initialize", response_model=MessageResponse)
def initialize_project_stages(
    init_in: InitializeProjectStagesRequest,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    初始化项目阶段

    根据模板为项目创建阶段和节点实例，支持调整配置：
    - skip_stages: 跳过某些阶段
    - skip_nodes: 跳过某些节点
    - stage_overrides: 调整阶段配置（工期、名称等）
    - node_overrides: 调整节点配置
    """
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限初始化该项目的阶段"
    )

    service = StageInstanceService(db)
    try:
        # 构建调整配置
        adjustments = {}
        if init_in.skip_stages:
            adjustments["skip_stages"] = init_in.skip_stages
        if init_in.skip_nodes:
            adjustments["skip_nodes"] = init_in.skip_nodes
        if init_in.stage_overrides:
            adjustments["stage_overrides"] = {
                k: v.model_dump(exclude_unset=True)
                for k, v in init_in.stage_overrides.items()
            }
        if init_in.node_overrides:
            adjustments["node_overrides"] = {
                k: v.model_dump(exclude_unset=True)
                for k, v in init_in.node_overrides.items()
            }

        stages = service.initialize_project_stages(
            project_id=project_id,
            template_id=init_in.template_id,
            start_date=init_in.start_date,
            adjustments=adjustments if adjustments else None,
        )
        db.commit()
        return MessageResponse(message=f"成功创建 {len(stages)} 个阶段")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/clear", response_model=MessageResponse)
def clear_project_stages(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """清除项目的所有阶段实例"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限清除该项目的阶段"
    )

    service = StageInstanceService(db)
    count = service.clear_project_stages(project_id)
    db.commit()
    return MessageResponse(message=f"已清除 {count} 个阶段")


@router.get("/{stage_id}", response_model=ProjectStageInstanceResponse)
def get_project_stage(
    project_id: int = Path(..., description="项目ID"),
    stage_id: int = Path(..., description="阶段ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取阶段详情"""
    check_project_access_or_raise(db, current_user, project_id)

    stage = (
        db.query(ProjectStageInstance)
        .filter(
            ProjectStageInstance.id == stage_id,
            ProjectStageInstance.project_id == project_id,
        )
        .first()
    )

    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")

    return stage

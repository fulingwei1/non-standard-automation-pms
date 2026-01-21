# -*- coding: utf-8 -*-
"""
项目阶段初始化 API

提供阶段初始化和清除功能
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.stage_template import InitializeProjectStagesRequest
from app.services.stage_instance import StageInstanceService

router = APIRouter()


@router.post("/{project_id}/stages/initialize", response_model=MessageResponse)
def initialize_project_stages(
    project_id: int,
    init_in: InitializeProjectStagesRequest,
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
        return {"message": f"成功创建 {len(stages)} 个阶段"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/stages/clear", response_model=MessageResponse)
def clear_project_stages(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """清除项目的所有阶段实例"""
    service = StageInstanceService(db)
    count = service.clear_project_stages(project_id)
    db.commit()
    return {"message": f"已清除 {count} 个阶段"}

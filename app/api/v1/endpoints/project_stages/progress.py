# -*- coding: utf-8 -*-
"""
项目阶段进度查询 API

提供项目进度概览和阶段详情查询
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.stage_template import (
    ProjectProgressResponse,
    ProjectStageInstanceDetail,
)
from app.services.stage_instance import StageInstanceService

router = APIRouter()


@router.get("/{project_id}/progress", response_model=ProjectProgressResponse)
def get_project_progress(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """获取项目阶段进度概览"""
    service = StageInstanceService(db)
    return service.get_project_progress(project_id)


@router.get("/stages/{stage_instance_id}", response_model=ProjectStageInstanceDetail)
def get_stage_detail(
    stage_instance_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """获取阶段详情（包含所有节点）"""
    service = StageInstanceService(db)
    detail = service.get_stage_detail(stage_instance_id)
    if not detail:
        raise HTTPException(status_code=404, detail="阶段实例不存在")
    return detail

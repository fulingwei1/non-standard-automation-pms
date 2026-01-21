# -*- coding: utf-8 -*-
"""
项目阶段操作 API

提供阶段的启动、完成、跳过、更新等操作
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.stage_instance import ProjectStageInstance
from app.models.user import User
from app.schemas.stage_template import (
    ProjectStageInstanceResponse,
    ProjectStageInstanceUpdate,
)
from app.services.stage_instance import StageInstanceService

router = APIRouter()


@router.post("/stages/{stage_instance_id}/start", response_model=ProjectStageInstanceResponse)
def start_stage(
    stage_instance_id: int,
    actual_start_date: Optional[date] = Query(None, description="实际开始日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """开始阶段"""
    service = StageInstanceService(db)
    try:
        stage = service.start_stage(stage_instance_id, actual_start_date)
        db.commit()
        return stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stages/{stage_instance_id}/complete", response_model=ProjectStageInstanceResponse)
def complete_stage(
    stage_instance_id: int,
    actual_end_date: Optional[date] = Query(None, description="实际结束日期"),
    auto_start_next: bool = Query(True, description="是否自动开始下一阶段"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """完成阶段"""
    service = StageInstanceService(db)
    try:
        stage, next_stage = service.complete_stage(
            stage_instance_id,
            actual_end_date,
            auto_start_next,
        )
        db.commit()
        return stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stages/{stage_instance_id}/skip", response_model=ProjectStageInstanceResponse)
def skip_stage(
    stage_instance_id: int,
    reason: Optional[str] = Query(None, description="跳过原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """跳过阶段"""
    service = StageInstanceService(db)
    try:
        stage = service.skip_stage(stage_instance_id, reason)
        db.commit()
        return stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/stages/{stage_instance_id}", response_model=ProjectStageInstanceResponse)
def update_stage_instance(
    stage_instance_id: int,
    update_in: ProjectStageInstanceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """更新阶段实例信息"""
    stage = db.query(ProjectStageInstance).filter(
        ProjectStageInstance.id == stage_instance_id
    ).first()

    if not stage:
        raise HTTPException(status_code=404, detail="阶段实例不存在")

    update_data = update_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stage, key, value)

    db.commit()
    db.refresh(stage)
    return stage

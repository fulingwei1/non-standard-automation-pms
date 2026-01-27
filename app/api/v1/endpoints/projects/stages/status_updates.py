# -*- coding: utf-8 -*-
"""
项目阶段状态更新 API

提供阶段状态更新和评审功能

使用统一状态更新服务重构
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.stage_instance import ProjectStageInstance
from app.models.user import User
from app.schemas.stage_template import (
    ProjectStageInstanceResponse,
    StageReviewRequest,
    UpdateStageStatusRequest,
)
from app.services.status_update_service import StatusUpdateService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.put("/{stage_instance_id}/status", response_model=ProjectStageInstanceResponse)
def update_stage_status(
    stage_instance_id: int,
    status_in: UpdateStageStatusRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    更新阶段状态

    使用统一状态更新服务，支持：
    - 状态值验证
    - 备注更新

    支持设置 DELAYED（延期）和 BLOCKED（受阻）状态。
    """
    stage = (
        db.query(ProjectStageInstance)
        .filter(ProjectStageInstance.id == stage_instance_id)
        .first()
    )

    if not stage:
        raise HTTPException(status_code=404, detail="阶段实例不存在")

    valid_statuses = [
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "DELAYED",
        "BLOCKED",
        "SKIPPED",
    ]

    # 更新前回调：更新备注
    def before_update_callback(entity, old_status, new_status, operator):
        if status_in.remark:
            entity.remark = status_in.remark

    # 使用统一状态更新服务
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=stage,
        new_status=status_in.status,
        operator=current_user,
        valid_statuses=valid_statuses,
        before_update_callback=before_update_callback,
        reason=status_in.remark,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "更新阶段状态失败",
        )

    return result.entity


@router.post("/{stage_instance_id}/review", response_model=ProjectStageInstanceResponse)
def submit_stage_review(
    stage_instance_id: int,
    review_in: StageReviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    提交阶段评审

    记录阶段的评审结果（通过/有条件通过/未通过）。
    """
    stage = (
        db.query(ProjectStageInstance)
        .filter(ProjectStageInstance.id == stage_instance_id)
        .first()
    )

    if not stage:
        raise HTTPException(status_code=404, detail="阶段实例不存在")

    valid_results = {"PASSED", "CONDITIONAL", "FAILED"}
    if review_in.review_result not in valid_results:
        raise HTTPException(
            status_code=400,
            detail=f"无效评审结果，支持的结果: {', '.join(valid_results)}",
        )

    stage.review_result = review_in.review_result
    stage.review_date = datetime.now()
    if review_in.review_notes:
        stage.review_notes = review_in.review_notes

    db.commit()
    db.refresh(stage)
    return stage

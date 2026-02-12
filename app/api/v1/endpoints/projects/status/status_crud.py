# -*- coding: utf-8 -*-
"""
项目状态 CRUD 端点

包含阶段更新、状态更新、健康度更新等单项操作
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import ProjectStatusLog
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.put("/{project_id}/stage", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    new_stage: str = Body(..., description="新阶段（S1-S9）"),
    reason: Optional[str] = Body(None, description="变更原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目阶段
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if new_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段编码。有效值：{', '.join(valid_stages)}"
        )

    old_stage = project.stage or 'S1'

    if old_stage == new_stage:
        return ResponseModel(
            code=200,
            message="阶段未变化",
            data={"project_id": project_id, "stage": new_stage}
        )

    project.stage = new_stage
    db.add(project)

    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=old_stage,
        new_stage=new_stage,
        old_status=project.status,
        new_status=project.status,
        old_health=project.health,
        new_health=project.health,
        change_type="STAGE_CHANGE",
        change_reason=reason or f"阶段变更：{old_stage} → {new_stage}",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.commit()

    return ResponseModel(
        code=200,
        message="阶段更新成功",
        data={
            "project_id": project_id,
            "old_stage": old_stage,
            "new_stage": new_stage,
        }
    )


@router.get("/{project_id}/status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目状态信息
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage,
            "status": project.status,
            "health": project.health,
            "progress_pct": project.progress_pct,
        }
    )


@router.put("/{project_id}/status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    new_status: str = Body(..., description="新状态（ST01-ST30）"),
    reason: Optional[str] = Body(None, description="变更原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目状态
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    valid_statuses = [f"ST{i:02d}" for i in range(1, 31)]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="无效的状态编码。有效值：ST01-ST30"
        )

    old_status = project.status

    if old_status == new_status:
        return ResponseModel(
            code=200,
            message="状态未变化",
            data={"project_id": project_id, "status": new_status}
        )

    project.status = new_status
    db.add(project)

    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=project.stage,
        new_stage=project.stage,
        old_status=old_status,
        new_status=new_status,
        old_health=project.health,
        new_health=project.health,
        change_type="STATUS_CHANGE",
        change_reason=reason or f"状态变更：{old_status} → {new_status}",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.commit()

    return ResponseModel(
        code=200,
        message="状态更新成功",
        data={
            "project_id": project_id,
            "old_status": old_status,
            "new_status": new_status,
        }
    )


@router.put("/{project_id}/health", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_health(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    new_health: str = Body(..., description="新健康度（H1-H4）"),
    reason: Optional[str] = Body(None, description="变更原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目健康度
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    valid_healths = ['H1', 'H2', 'H3', 'H4']
    if new_health not in valid_healths:
        raise HTTPException(
            status_code=400,
            detail=f"无效的健康度编码。有效值：{', '.join(valid_healths)}"
        )

    old_health = project.health or 'H1'

    if old_health == new_health:
        return ResponseModel(
            code=200,
            message="健康度未变化",
            data={"project_id": project_id, "health": new_health}
        )

    project.health = new_health
    db.add(project)

    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=project.stage,
        new_stage=project.stage,
        old_status=project.status,
        new_status=project.status,
        old_health=old_health,
        new_health=new_health,
        change_type="HEALTH_CHANGE",
        change_reason=reason or f"健康度变更：{old_health} → {new_health}",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.commit()

    return ResponseModel(
        code=200,
        message="健康度更新成功",
        data={
            "project_id": project_id,
            "old_health": old_health,
            "new_health": new_health,
        }
    )

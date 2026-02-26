# -*- coding: utf-8 -*-
"""
项目状态 CRUD 端点

包含阶段更新、状态更新、健康度更新等单项操作
已重构为使用通用 StatusUpdateService
"""

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import ProjectStatusLog
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.status_update_service import StatusUpdateService

router = APIRouter()


def _create_project_status_log(db, project, old_values, new_values, change_type, reason, user_id):
    """创建项目状态变更日志（内部辅助）"""
    from datetime import datetime
    log = ProjectStatusLog(
        project_id=project.id,
        old_stage=old_values.get("stage", project.stage),
        new_stage=new_values.get("stage", project.stage),
        old_status=old_values.get("status", project.status),
        new_status=new_values.get("status", project.status),
        old_health=old_values.get("health", project.health),
        new_health=new_values.get("health", project.health),
        change_type=change_type,
        change_reason=reason,
        changed_by=user_id,
        changed_at=datetime.now(),
    )
    db.add(log)


def _update_project_field(
    db: Session,
    current_user: User,
    project_id: int,
    field: str,
    new_value: str,
    valid_values: list,
    change_type: str,
    reason: Optional[str],
    label: str,
) -> ResponseModel:
    """通用项目字段更新（stage/status/health 共用逻辑）"""
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    service = StatusUpdateService(db)
    getattr(project, field) or valid_values[0]

    # 使用 StatusUpdateService 进行验证和更新
    def history_cb(entity, old_status, new_status, operator, reason_text):
        _create_project_status_log(
            db, project,
            {field: old_status},
            {field: new_status},
            change_type,
            reason_text or f"{label}变更：{old_status} → {new_status}",
            operator.id,
        )

    result = service.update_status(
        entity=project,
        new_status=new_value,
        operator=current_user,
        valid_statuses=valid_values,
        status_field=field,
        history_callback=history_cb,
        reason=reason,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail="; ".join(result.errors))

    if result.message == "状态未发生变化":
        return ResponseModel(
            code=200,
            message=f"{label}未变化",
            data={"project_id": project_id, field: new_value},
        )

    db.commit()

    return ResponseModel(
        code=200,
        message=f"{label}更新成功",
        data={
            "project_id": project_id,
            f"old_{field}": result.old_status,
            f"new_{field}": result.new_status,
        },
    )


@router.put("/{project_id}/stage", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    new_stage: str = Body(..., description="新阶段（S1-S9）"),
    reason: Optional[str] = Body(None, description="变更原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新项目阶段"""
    return _update_project_field(
        db, current_user, project_id,
        field="stage",
        new_value=new_stage,
        valid_values=['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9'],
        change_type="STAGE_CHANGE",
        reason=reason,
        label="阶段",
    )


@router.get("/{project_id}/status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目状态信息"""
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
        },
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
    """更新项目状态"""
    return _update_project_field(
        db, current_user, project_id,
        field="status",
        new_value=new_status,
        valid_values=[f"ST{i:02d}" for i in range(1, 31)],
        change_type="STATUS_CHANGE",
        reason=reason,
        label="状态",
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
    """更新项目健康度"""
    return _update_project_field(
        db, current_user, project_id,
        field="health",
        new_value=new_health,
        valid_values=['H1', 'H2', 'H3', 'H4'],
        change_type="HEALTH_CHANGE",
        reason=reason,
        label="健康度",
    )

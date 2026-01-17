# -*- coding: utf-8 -*-
"""
工程师进度管理 API 端点
包含：进度更新、任务完成
"""

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas import engineer as schemas
from app.services.progress_aggregation_service import (
    aggregate_task_progress,
    create_progress_log,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.put("/tasks/{task_id}/progress", response_model=schemas.ProgressUpdateResponse)
def update_task_progress(
    task_id: int,
    progress_data: schemas.ProgressUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    更新任务进度（自动触发项目/阶段进度聚合）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能更新分配给自己的任务")

    if task.status in ['COMPLETED', 'REJECTED', 'CANCELLED']:
        raise HTTPException(status_code=400, detail="任务已完成或已被拒绝，无法更新进度")

    if progress_data.progress < 0 or progress_data.progress > 100:
        raise HTTPException(status_code=400, detail="进度必须在0到100之间")

    # 更新进度
    old_progress = task.progress
    task.progress = progress_data.progress

    if progress_data.actual_hours is not None:
        task.actual_hours = progress_data.actual_hours

    # 状态自动转换
    if progress_data.progress > 0 and task.status == 'ACCEPTED':
        task.status = 'IN_PROGRESS'
        task.actual_start_date = date.today()

    if progress_data.progress == 100:
        task.status = 'COMPLETED'
        task.actual_end_date = date.today()

    task.updated_by = current_user.id
    task.updated_at = datetime.now()

    db.commit()

    # 创建进度日志
    if progress_data.progress_note:
        create_progress_log(
            db,
            task_id=task.id,
            progress=progress_data.progress,
            actual_hours=float(progress_data.actual_hours) if progress_data.actual_hours else None,
            note=progress_data.progress_note,
            updater_id=current_user.id
        )

    # 触发进度聚合
    aggregation_result = aggregate_task_progress(db, task.id)

    actual_hours_value = float(task.actual_hours) if task.actual_hours is not None else None

    return schemas.ProgressUpdateResponse(
        task_id=task.id,
        progress=task.progress,
        actual_hours=actual_hours_value,
        status=task.status,
        progress_note=progress_data.progress_note,
        project_progress_updated=aggregation_result['project_progress_updated'],
        stage_progress_updated=aggregation_result['stage_progress_updated']
    )


@router.put("/tasks/{task_id}/complete", response_model=schemas.TaskCompleteResponse)
def complete_task(
    task_id: int,
    complete_data: schemas.TaskCompleteRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    完成任务（含证明材料验证）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能完成自己的任务")

    from app.models.task_center import TaskCompletionProof
    proof_count = db.query(TaskCompletionProof).filter(
        TaskCompletionProof.task_id == task_id
    ).count()

    if not complete_data.skip_proof_validation and proof_count == 0:
        raise HTTPException(
            status_code=400,
            detail="需要上传至少一个完成证明"
        )

    # 更新任务
    task.status = 'COMPLETED'
    task.progress = 100
    task.actual_end_date = date.today()
    task.completion_note = complete_data.completion_note
    task.updated_by = current_user.id
    task.updated_at = datetime.now()
    completed_at = datetime.now()

    db.commit()

    # 触发进度聚合
    aggregation_result = aggregate_task_progress(db, task.id)

    # 发送通知
    from app.services.notification_service import NotificationType, notification_service
    try:
        # 通知项目经理任务已完成
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if project and project.pm_id:
            notification_service.send_task_completed_notification(
                db=db,
                task_owner_id=project.pm_id,
                task_name=task.title or f"任务#{task.id}",
                project_name=project.project_name or ""
            )
    except Exception as e:
        # 通知失败不影响主流程
        logger.warning("任务完成通知发送失败，不影响主流程", exc_info=True)

    return schemas.TaskCompleteResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        actual_end_date=task.actual_end_date,
        completion_note=task.completion_note,
        proof_count=proof_count,
        completed_at=completed_at,
        project_progress_updated=aggregation_result['project_progress_updated']
    )

# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 任务进度更新
包含：任务进度更新（级联更新里程碑和项目进度）
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.progress import ProgressLog, Task
from app.models.project import Project, ProjectMilestone
from app.models.user import User
from app.schemas.progress import TaskProgressUpdate, TaskResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.put("/tasks/{task_id}/progress", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    progress_in: TaskProgressUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新任务进度（级联更新里程碑和项目进度）
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    old_progress = task.progress_percent

    # 禁止进度回退（除非是管理员或项目经理）
    if progress_in.progress_percent < old_progress and not current_user.is_superuser:
        # 检查是否是项目经理
        is_pm = False
        if task.project_id:
            project = db.query(Project).filter(Project.id == task.project_id).first()
            if project and project.pm_id == current_user.id:
                is_pm = True

        if not is_pm:
            raise HTTPException(
                status_code=400,
                detail=f"不允许进度回退（{old_progress}% → {progress_in.progress_percent}%），请联系项目经理审批"
            )

    # 更新任务进度
    task.progress_percent = progress_in.progress_percent

    # 如果进度达到100%，自动设置为完成状态
    if progress_in.progress_percent >= 100:
        task.status = "DONE"
        if not task.actual_end:
            task.actual_end = date.today()

    # 如果进度大于0且状态为TODO，自动设置为进行中
    elif progress_in.progress_percent > 0 and task.status == "TODO":
        task.status = "IN_PROGRESS"
        if not task.actual_start:
            task.actual_start = date.today()

    db.add(task)

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=progress_in.progress_percent,
        update_note=progress_in.update_note or f"进度更新：{old_progress}% → {progress_in.progress_percent}%",
        updated_by=current_user.id
    )
    db.add(progress_log)

    # 级联更新里程碑进度
    if task.milestone_id:
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == task.milestone_id).first()
        if milestone:
            # 获取里程碑下的所有任务
            milestone_tasks = db.query(Task).filter(
                Task.milestone_id == task.milestone_id,
                Task.status != "CANCELLED"
            ).all()

            if milestone_tasks:
                # 按权重加权计算里程碑进度
                total_weight = sum(float(t.weight) for t in milestone_tasks)
                weighted_progress = sum(float(t.progress_percent) * float(t.weight) for t in milestone_tasks)
                milestone_progress = int(weighted_progress / total_weight) if total_weight > 0 else 0

                # 更新里程碑进度（如果里程碑有progress字段）
                if hasattr(milestone, 'progress'):
                    milestone.progress = milestone_progress
                    db.add(milestone)

                # 如果所有任务完成，检查里程碑完成条件（验收联动）
                all_done = all(t.status == "DONE" for t in milestone_tasks)
                if all_done and milestone.status != "COMPLETED":
                    # 检查验收和交付物要求
                    try:
                        from app.services.progress_integration_service import (
                            ProgressIntegrationService,
                        )
                        integration_service = ProgressIntegrationService(db)
                        can_complete, missing_items = integration_service.check_milestone_completion_requirements(milestone)

                        if can_complete:
                            milestone.status = "COMPLETED"
                            if not milestone.actual_date:
                                milestone.actual_date = date.today()
                            db.add(milestone)
                        else:
                            # 不满足完成条件，保持当前状态并记录原因
                            logger.warning(f"里程碑 {milestone.milestone_name} 不满足完成条件: {', '.join(missing_items)}")
                    except Exception as e:
                        # 检查失败时，默认允许完成（向后兼容）
                        logger.error(f"检查里程碑完成条件失败: {str(e)}", exc_info=True)
                        milestone.status = "COMPLETED"
                        if not milestone.actual_date:
                            milestone.actual_date = date.today()
                        db.add(milestone)

    # 级联更新项目进度（通过进度汇总服务自动更新，这里不重复计算）
    # 项目进度会在定时任务中自动计算

    db.commit()
    db.refresh(task)

    return task

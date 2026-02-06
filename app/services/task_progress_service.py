# -*- coding: utf-8 -*-
"""
任务进度更新服务

统一任务进度更新逻辑，供 engineers/progress 与 task_center/update 共用，
避免两处重复实现状态转换、进度校验与聚合。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.task_center import TaskUnified


def apply_task_progress_update(
    task: TaskUnified,
    progress: int,
    updater_id: int,
    *,
    actual_hours: Optional[Decimal] = None,
    reject_completed: bool = True,
    enforce_assignee: bool = True,
) -> None:
    """
    仅应用进度更新字段与状态转换，不负责数据库提交。

    用于单个与批量更新逻辑复用，避免重复实现。
    """
    if enforce_assignee and task.assignee_id != updater_id:
        raise ValueError("只能更新分配给自己的任务")

    if reject_completed and task.status in ("COMPLETED", "REJECTED", "CANCELLED"):
        raise ValueError("任务已完成或已被拒绝，无法更新进度")

    if progress < 0 or progress > 100:
        raise ValueError("进度必须在0到100之间")

    # 更新字段
    task.progress = progress
    if actual_hours is not None:
        task.actual_hours = actual_hours
    task.updated_by = updater_id
    task.updated_at = datetime.now()

    # 状态与日期
    if progress > 0 and task.status == "ACCEPTED":
        task.status = "IN_PROGRESS"
        if not task.actual_start_date:
            task.actual_start_date = date.today()

    if progress >= 100:
        task.status = "COMPLETED"
        task.actual_end_date = date.today()


def update_task_progress(
    db: Session,
    task_id: int,
    progress: int,
    updater_id: int,
    *,
    actual_hours: Optional[Decimal] = None,
    progress_note: Optional[str] = None,
    reject_completed: bool = True,
    create_progress_log: bool = True,
    run_aggregation: bool = True,
) -> Tuple[TaskUnified, Dict[str, Any]]:
    """
    更新任务进度（核心逻辑，两处 API 共用）。

    Args:
        db: 数据库会话
        task_id: 任务 ID
        progress: 进度百分比 0–100
        updater_id: 更新人用户 ID（用于权限与日志）
        actual_hours: 实际工时，可选
        progress_note: 进度说明，可选；当 create_progress_log 为 True 时会写入进度日志
        reject_completed: 若 True，任务状态为 COMPLETED/REJECTED/CANCELLED 时抛出 ValueError
        create_progress_log: 若 True 且 progress_note 有值，则调用 create_progress_log 写进度日志
        run_aggregation: 若 True，则调用 aggregate_task_progress 聚合到项目/阶段

    Returns:
        (更新后的 TaskUnified, 聚合结果 dict；未聚合时 dict 为空)

    Raises:
        ValueError: 任务不存在、无权限、状态不可更新、进度非法
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise ValueError("任务不存在")

    apply_task_progress_update(
        task,
        progress,
        updater_id,
        actual_hours=actual_hours,
        reject_completed=reject_completed,
        enforce_assignee=True,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    aggregation_result: Dict[str, Any] = {}

    if create_progress_log and progress_note:
        from app.services.progress_aggregation_service import create_progress_log as _create_log

        _create_log(
            db,
            task_id=task.id,
            progress=progress,
            actual_hours=float(actual_hours) if actual_hours is not None else None,
            note=progress_note,
            updater_id=updater_id,
        )

    if run_aggregation:
        from app.services.progress_aggregation_service import aggregate_task_progress

        aggregation_result = aggregate_task_progress(db, task.id)

    return task, aggregation_result

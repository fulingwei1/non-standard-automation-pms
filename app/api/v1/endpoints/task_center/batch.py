# -*- coding: utf-8 -*-
"""
批量操作 - 自动生成
从 task_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.notification import Notification
from app.models.project import Project
from app.models.task_center import (
    JobDutyTemplate,
    TaskComment,
    TaskOperationLog,
    TaskReminder,
    TaskUnified,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.task_center import (
    BatchOperationResponse,
    BatchOperationStatistics,
    BatchTaskOperation,
    TaskCommentCreate,
    TaskCommentResponse,
    TaskOverviewResponse,
    TaskProgressUpdate,
    TaskTransferRequest,
    TaskUnifiedCreate,
    TaskUnifiedListResponse,
    TaskUnifiedResponse,
    TaskUnifiedUpdate,
)
from app.services.sales_reminder import create_notification

router = APIRouter()


def generate_task_code(db: Session) -> str:
    """生成任务编号：TASK-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=TaskUnified,
        no_field='task_code',
        prefix='TASK',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def log_task_operation(
    db: Session,
    task_id: int,
    operation_type: str,
    operation_desc: str,
    operator_id: int,
    operator_name: str,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None
):
    """记录任务操作日志"""
    log = TaskOperationLog(
        task_id=task_id,
        operation_type=operation_type,
        operation_desc=operation_desc,
        operator_id=operator_id,
        operator_name=operator_name,
        old_value=old_value,
        new_value=new_value
    )
    db.add(log)
    db.commit()



from fastapi import APIRouter

router = APIRouter(
    prefix="/task-center/batch",
    tags=["batch"]
)

# 共 10 个路由

# ==================== 批量操作 ====================

@router.post("/batch/complete", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_complete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量完成任务
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "任务已完成"})
                continue

            task.status = "COMPLETED"
            task.progress = 100
            task.actual_end_date = datetime.now().date()
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_COMPLETE", f"批量完成任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/transfer", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_transfer_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    target_user_id: int = Body(..., description="目标用户ID"),
    transfer_reason: str = Body(..., description="转办原因"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量转办任务
    """
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "已完成的任务不能转办"})
                continue

            task.assignee_id = target_user_id
            task.assignee_name = target_user.real_name or target_user.username
            task.is_transferred = True
            task.transfer_from_id = current_user.id
            task.transfer_from_name = current_user.real_name or current_user.username
            task.transfer_reason = transfer_reason
            task.transfer_time = datetime.now()
            task.status = "PENDING"
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_TRANSFER",
                f"批量转办任务：{task.title} -> {target_user.real_name or target_user.username}",
                current_user.id, current_user.real_name or current_user.username
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/priority", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_set_priority(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    priority: str = Body(..., description="优先级：URGENT/HIGH/MEDIUM/LOW"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量设置优先级
    """
    if priority not in ["URGENT", "HIGH", "MEDIUM", "LOW"]:
        raise HTTPException(status_code=400, detail="无效的优先级")

    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            old_priority = task.priority
            task.priority = priority
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_SET_PRIORITY",
                f"批量设置优先级：{old_priority} -> {priority}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"priority": old_priority},
                new_value={"priority": priority}
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/progress", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_update_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    progress: int = Body(..., ge=0, le=100, description="进度百分比"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量更新进度
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            old_progress = task.progress
            task.progress = progress
            task.updated_by = current_user.id

            if progress >= 100 and task.status != "COMPLETED":
                task.status = "COMPLETED"
                task.actual_end_date = datetime.now().date()

            if progress > 0 and task.status == "ACCEPTED":
                task.status = "IN_PROGRESS"
                if not task.actual_start_date:
                    task.actual_start_date = datetime.now().date()

            log_task_operation(
                db, task.id, "BATCH_UPDATE_PROGRESS",
                f"批量更新进度：{old_progress}% -> {progress}%",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"progress": old_progress},
                new_value={"progress": progress}
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/delete", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_delete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量删除任务（仅个人任务）
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id,
        TaskUnified.task_type == "PERSONAL"  # 只能删除个人任务
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.task_type != "PERSONAL":
                failed_tasks.append({"task_id": task.id, "reason": "只能删除个人任务"})
                continue

            log_task_operation(
                db, task.id, "BATCH_DELETE", f"批量删除任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username
            )

            db.delete(task)
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/start", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_start_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量开始任务
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.status in ["IN_PROGRESS", "COMPLETED"]:
                failed_tasks.append({"task_id": task.id, "reason": "任务已开始或已完成"})
                continue

            old_status = task.status
            task.status = "IN_PROGRESS"
            if not task.actual_start_date:
                task.actual_start_date = datetime.now().date()
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_START", f"批量开始任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"status": old_status},
                new_value={"status": "IN_PROGRESS"}
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/pause", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_pause_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量暂停任务
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.status != "IN_PROGRESS":
                failed_tasks.append({"task_id": task.id, "reason": "只能暂停进行中的任务"})
                continue

            old_status = task.status
            task.status = "PAUSED"
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_PAUSE", f"批量暂停任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"status": old_status},
                new_value={"status": "PAUSED"}
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/tag", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_tag_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    tags: List[str] = Body(..., description="标签列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量打标签
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            old_tags = task.tags if task.tags else []
            # 合并标签（去重）
            new_tags = list(set((old_tags or []) + tags))
            task.tags = new_tags
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_TAG", f"批量打标签：{tags}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"tags": old_tags},
                new_value={"tags": new_tags}
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/urge", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_urge_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    urge_message: Optional[str] = Body(None, description="催办消息"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量催办任务（发送催办通知）
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids)
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if not task.assignee_id:
                failed_tasks.append({"task_id": task.id, "reason": "任务未分配负责人"})
                continue

            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "已完成的任务无需催办"})
                continue

            # 创建催办通知
            notification = Notification(
                user_id=task.assignee_id,
                notification_type="TASK_URGE",
                title=f"任务催办：{task.title}",
                content=urge_message or f"任务【{task.title}】需要尽快处理，请及时关注。",
                source_type="TASK",
                source_id=task.id,
                link_url=f"/task-center/tasks/{task.id}",
                priority="HIGH",
                extra_data={
                    "task_id": task.id,
                    "task_title": task.title,
                    "urge_by": current_user.real_name or current_user.username,
                    "urge_by_id": current_user.id
                }
            )
            db.add(notification)

            log_task_operation(
                db, task.id, "BATCH_URGE",
                f"批量催办任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.get("/batch/statistics", response_model=BatchOperationStatistics, status_code=status.HTTP_200_OK)
def get_batch_operation_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量操作统计（操作历史）
    """
    query = db.query(TaskOperationLog).filter(
        TaskOperationLog.operator_id == current_user.id,
        TaskOperationLog.operation_type.like("BATCH_%")
    )

    if start_date:
        start_date_str = start_date.strftime("%Y-%m-%d")
        query = query.filter(func.date(TaskOperationLog.operation_time) >= start_date_str)
    if end_date:
        end_date_str = end_date.strftime("%Y-%m-%d")
        query = query.filter(func.date(TaskOperationLog.operation_time) <= end_date_str)

    logs = query.order_by(desc(TaskOperationLog.operation_time)).all()

    # 按操作类型统计
    by_operation_type = {}
    for log in logs:
        op_type = log.operation_type.replace("BATCH_", "")
        by_operation_type[op_type] = by_operation_type.get(op_type, 0) + 1

    # 按日期统计
    by_date = {}
    for log in logs:
        date_str = log.operation_time.date().isoformat()
        by_date[date_str] = by_date.get(date_str, 0) + 1

    # 最近操作
    recent_operations = []
    for log in logs[:20]:  # 最近20条
        recent_operations.append({
            "operation_type": log.operation_type,
            "operation_desc": log.operation_desc,
            "operation_time": log.operation_time.isoformat(),
            "task_id": log.task_id
        })

    return BatchOperationStatistics(
        total_operations=len(logs),
        by_operation_type=by_operation_type,
        by_date=by_date,
        recent_operations=recent_operations
    )



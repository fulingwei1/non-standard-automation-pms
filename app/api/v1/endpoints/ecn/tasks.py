# -*- coding: utf-8 -*-
"""
ECN任务管理 API endpoints

包含：任务列表、创建任务、更新进度、完成任务
"""

import logging
from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.ecn import Ecn, EcnTask
from app.services.ecn_notification_service import (
    notify_task_assigned,
    notify_task_completed,
)
from app.services.ecn_auto_assign_service import auto_assign_task
from app.schemas.ecn import EcnTaskCreate, EcnTaskResponse
from .utils import get_user_display_name

router = APIRouter()


@router.get("/ecns/{ecn_id}/tasks", response_model=List[EcnTaskResponse], status_code=status.HTTP_200_OK)
def read_ecn_tasks(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN任务列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    tasks = db.query(EcnTask).filter(EcnTask.ecn_id == ecn_id).order_by(EcnTask.task_no, EcnTask.created_at).all()

    items = []
    for task in tasks:
        assignee_name = get_user_display_name(db, task.assignee_id)

        items.append(EcnTaskResponse(
            id=task.id,
            ecn_id=task.ecn_id,
            task_no=task.task_no,
            task_name=task.task_name,
            task_type=task.task_type,
            task_dept=task.task_dept,
            assignee_id=task.assignee_id,
            assignee_name=assignee_name,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            progress_pct=task.progress_pct or 0,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))

    return items


@router.post("/ecns/{ecn_id}/tasks", response_model=EcnTaskResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_task(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    task_in: EcnTaskCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分派ECN任务
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    if ecn.status not in ["APPROVED", "EXECUTING"]:
        raise HTTPException(status_code=400, detail="ECN当前不在执行阶段")

    # 验证负责人
    if task_in.assignee_id:
        assignee = db.query(User).filter(User.id == task_in.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="负责人不存在")

    # 获取最大任务序号
    max_order = db.query(EcnTask).filter(EcnTask.ecn_id == ecn_id).order_by(desc(EcnTask.task_no)).first()
    task_no = (max_order.task_no + 1) if max_order else 1

    task = EcnTask(
        ecn_id=ecn_id,
        task_no=task_no,
        task_name=task_in.task_name,
        task_type=task_in.task_type,
        task_dept=task_in.task_dept,
        task_description=task_in.task_description,
        assignee_id=task_in.assignee_id,
        planned_start=task_in.planned_start,
        planned_end=task_in.planned_end,
        status="PENDING",
        progress_pct=0
    )

    # 分配执行任务：优先使用手动指定，否则自动分配
    try:
        assignee_id = task_in.assignee_id

        # 如果手动指定了执行人员，验证用户
        if assignee_id:
            assignee = db.query(User).filter(
                User.id == assignee_id,
                User.department == task_in.task_dept,
                User.is_active == True
            ).first()

            if not assignee:
                assignee_id = None  # 用户不存在或不属于该部门，使用自动分配

        # 如果没有手动指定或手动指定无效，则自动分配
        if not assignee_id:
            assignee_id = auto_assign_task(db, ecn, task)

        # 设置执行人
        if assignee_id:
            task.assignee_id = assignee_id
    except Exception as e:
        logger.error(f"Failed to assign task: {e}")

    # 如果ECN状态是已审批，自动更新为执行中
    if ecn.status == "APPROVED":
        ecn.status = "EXECUTING"
        ecn.execution_start = datetime.now()
        ecn.current_step = "EXECUTION"
        db.add(ecn)

    db.add(task)
    db.commit()
    db.refresh(task)

    # 发送通知（任务分配）
    try:
        if task.assignee_id:
            notify_task_assigned(db, ecn, task, task.assignee_id)
    except Exception as e:
        logger.error(f"Failed to send task assigned notification: {e}")

    return _build_task_response(db, task)


@router.get("/ecn-tasks/{task_id}", response_model=EcnTaskResponse, status_code=status.HTTP_200_OK)
def read_ecn_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN任务详情
    """
    task = db.query(EcnTask).filter(EcnTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ECN任务不存在")

    return _build_task_response(db, task)


@router.put("/ecn-tasks/{task_id}/progress", response_model=EcnTaskResponse, status_code=status.HTTP_200_OK)
def update_ecn_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    progress: int = Query(..., ge=0, le=100, description="进度百分比"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新任务进度
    """
    task = db.query(EcnTask).filter(EcnTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ECN任务不存在")

    task.progress_pct = progress

    # 如果进度大于0且状态为待处理，自动设置为进行中
    if progress > 0 and task.status == "PENDING":
        task.status = "IN_PROGRESS"
        if not task.actual_start:
            task.actual_start = datetime.now().date()

    # 如果进度达到100%，自动设置为完成
    if progress >= 100:
        task.status = "COMPLETED"
        task.progress_pct = 100
        if not task.actual_end:
            task.actual_end = datetime.now().date()

    db.add(task)
    db.commit()
    db.refresh(task)

    return _build_task_response(db, task)


@router.put("/ecn-tasks/{task_id}/complete", response_model=EcnTaskResponse, status_code=status.HTTP_200_OK)
def complete_ecn_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成ECN任务
    """
    task = db.query(EcnTask).filter(EcnTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ECN任务不存在")

    task.status = "COMPLETED"
    task.progress_pct = 100
    if not task.actual_end:
        task.actual_end = datetime.now().date()
    if not task.actual_start:
        task.actual_start = task.planned_start or datetime.now().date()

    # 检查是否所有任务都已完成
    ecn = db.query(Ecn).filter(Ecn.id == task.ecn_id).first()
    if ecn:
        pending_tasks = db.query(EcnTask).filter(
            EcnTask.ecn_id == ecn.id,
            EcnTask.status != "COMPLETED"
        ).count()

        if pending_tasks == 0:
            # 所有任务都已完成，更新ECN状态
            ecn.status = "COMPLETED"
            ecn.execution_end = datetime.now()
            ecn.current_step = "COMPLETED"
            db.add(ecn)

    db.add(task)
    db.commit()
    db.refresh(task)

    # 发送通知（任务完成）
    try:
        ecn = db.query(Ecn).filter(Ecn.id == task.ecn_id).first()
        if ecn:
            notify_task_completed(db, ecn, task)
    except Exception as e:
        logger.error(f"Failed to send task completed notification: {e}")

    return _build_task_response(db, task)


def _build_task_response(db: Session, task: EcnTask) -> EcnTaskResponse:
    """构建任务响应"""
    assignee_name = get_user_display_name(db, task.assignee_id)

    return EcnTaskResponse(
        id=task.id,
        ecn_id=task.ecn_id,
        task_no=task.task_no,
        task_name=task.task_name,
        task_type=task.task_type,
        task_dept=task.task_dept,
        assignee_id=task.assignee_id,
        assignee_name=assignee_name,
        planned_start=task.planned_start,
        planned_end=task.planned_end,
        actual_start=task.actual_start,
        actual_end=task.actual_end,
        progress_pct=task.progress_pct or 0,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

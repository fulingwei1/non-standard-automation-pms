# -*- coding: utf-8 -*-
"""项目交付排产计划 API - 任务操作"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project_delivery import (
    ProjectDeliveryTaskCreate,
    ProjectDeliveryTaskResponse,
    ConflictDetectionResponse,
)
from app.services.project_delivery_service import get_project_delivery_service

router = APIRouter()

@router.post("/{schedule_id}/tasks", response_model=ProjectDeliveryTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(*, db: Session = Depends(deps.get_db), schedule_id: int, task_in: ProjectDeliveryTaskCreate, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """创建任务"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.create_task(schedule_id, task_in)

@router.get("/{schedule_id}/tasks", response_model=List[ProjectDeliveryTaskResponse])
def list_tasks(*, db: Session = Depends(deps.get_db), schedule_id: int, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """获取任务列表"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.get_tasks(schedule_id)

@router.get("/{schedule_id}/conflicts", response_model=ConflictDetectionResponse)
def detect_conflicts(*, db: Session = Depends(deps.get_db), schedule_id: int, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """检测冲突"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.detect_conflicts(schedule_id)

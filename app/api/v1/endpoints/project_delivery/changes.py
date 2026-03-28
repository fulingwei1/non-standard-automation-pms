# -*- coding: utf-8 -*-
"""项目交付排产计划 API - 变更管理操作"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project_delivery import (
    ProjectDeliveryChangeLogCreate,
    ProjectDeliveryChangeLogResponse,
)
from app.services.project_delivery_service import get_project_delivery_service

router = APIRouter()

@router.post("/{schedule_id}/changes", response_model=ProjectDeliveryChangeLogResponse, status_code=status.HTTP_201_CREATED)
def create_change_log(*, db: Session = Depends(deps.get_db), schedule_id: int, change_in: ProjectDeliveryChangeLogCreate, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """创建变更日志"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.create_change_log(schedule_id, change_in)

@router.get("/{schedule_id}/changes", response_model=List[ProjectDeliveryChangeLogResponse])
def list_change_logs(*, db: Session = Depends(deps.get_db), schedule_id: int, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """获取变更日志列表"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.get_change_logs(schedule_id)

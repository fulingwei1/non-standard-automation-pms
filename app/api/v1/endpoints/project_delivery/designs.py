# -*- coding: utf-8 -*-
"""项目交付排产计划 API - 机械设计任务操作"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project_delivery import (
    ProjectDeliveryMechanicalDesignCreate,
    ProjectDeliveryMechanicalDesignResponse,
)
from app.services.project_delivery_service import get_project_delivery_service

router = APIRouter()

@router.post("/{schedule_id}/mechanical-designs", response_model=ProjectDeliveryMechanicalDesignResponse, status_code=status.HTTP_201_CREATED)
def create_mechanical_design(*, db: Session = Depends(deps.get_db), schedule_id: int, design_in: ProjectDeliveryMechanicalDesignCreate, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """创建机械设计任务"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.create_mechanical_design(schedule_id, design_in)

@router.get("/{schedule_id}/mechanical-designs", response_model=List[ProjectDeliveryMechanicalDesignResponse])
def list_mechanical_designs(*, db: Session = Depends(deps.get_db), schedule_id: int, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """获取机械设计任务列表"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.get_mechanical_designs(schedule_id)

# -*- coding: utf-8 -*-
"""项目交付排产计划 API - 长周期采购操作"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project_delivery import (
    ProjectDeliveryLongCyclePurchaseCreate,
    ProjectDeliveryLongCyclePurchaseResponse,
)
from app.services.project_delivery_service import get_project_delivery_service

router = APIRouter()

@router.post("/{schedule_id}/long-cycle-purchases", response_model=ProjectDeliveryLongCyclePurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_long_cycle_purchase(*, db: Session = Depends(deps.get_db), schedule_id: int, purchase_in: ProjectDeliveryLongCyclePurchaseCreate, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """创建长周期采购"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.create_long_cycle_purchase(schedule_id, purchase_in)

@router.get("/{schedule_id}/long-cycle-purchases", response_model=List[ProjectDeliveryLongCyclePurchaseResponse])
def list_long_cycle_purchases(*, db: Session = Depends(deps.get_db), schedule_id: int, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """获取长周期采购列表"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.get_long_cycle_purchases(schedule_id)

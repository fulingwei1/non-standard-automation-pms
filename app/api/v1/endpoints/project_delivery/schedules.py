# -*- coding: utf-8 -*-
"""
项目交付排产计划 API - 主表操作
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project_delivery import (
    ProjectDeliveryScheduleCreate,
    ProjectDeliveryScheduleResponse,
    ProjectDeliveryScheduleUpdate,
    ProjectDeliveryScheduleListResponse,
)
from app.services.project_delivery_service import ProjectDeliveryService, get_project_delivery_service

router = APIRouter()


@router.post(
    "",
    response_model=ProjectDeliveryScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目交付排产计划"
)
def create_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_in: ProjectDeliveryScheduleCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目交付排产计划
    """
    
    service = get_project_delivery_service(db)
    
    schedule = service.create_schedule(
        schedule_in=schedule_in,
        initiator_id=current_user.id,
        initiator_name=current_user.username,
    )
    
    return schedule


@router.get(
    "",
    response_model=List[ProjectDeliveryScheduleResponse],
    summary="获取排产计划列表"
)
def list_schedules(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: Optional[int] = Query(None, description="商机 ID"),
    project_id: Optional[int] = Query(None, description="项目 ID"),
    status: Optional[str] = Query(None, description="状态"),
    usage_type: Optional[str] = Query(None, description="使用类型"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取排产计划列表
    """
    
    service = get_project_delivery_service(db)
    items, total = service.list_schedules(
        lead_id=lead_id,
        project_id=project_id,
        status=status,
        usage_type=usage_type,
        skip=skip,
        limit=limit,
    )
    
    return items


@router.get(
    "/{schedule_id}",
    response_model=ProjectDeliveryScheduleResponse,
    summary="获取排产计划详情"
)
def get_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取排产计划详情
    """
    
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    
    return schedule


@router.post(
    "/{schedule_id}/confirm",
    response_model=ProjectDeliveryScheduleResponse,
    summary="确认排产计划"
)
def confirm_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认排产计划（项目经理操作）
    """
    
    service = get_project_delivery_service(db)
    schedule = service.confirm_schedule(
        schedule_id=schedule_id,
        confirmed_by=current_user.id,
        confirmed_by_name=current_user.username,
    )
    
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    
    return schedule

# -*- coding: utf-8 -*-
"""项目交付排产计划 API - 甘特图数据"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project_delivery import GanttDataResponse
from app.services.project_delivery_service import get_project_delivery_service

router = APIRouter()

@router.get("/{schedule_id}/gantt", response_model=GanttDataResponse)
def get_gantt_data(*, db: Session = Depends(deps.get_db), schedule_id: int, current_user: User = Depends(security.get_current_active_user)) -> Any:
    """获取甘特图数据"""
    service = get_project_delivery_service(db)
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排产计划不存在")
    return service.get_gantt_data(schedule_id)

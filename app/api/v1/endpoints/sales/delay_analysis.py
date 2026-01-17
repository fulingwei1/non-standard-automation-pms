# -*- coding: utf-8 -*-
"""
延期深度分析 API endpoints
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.delay_root_cause_service import DelayRootCauseService

router = APIRouter()


@router.get("/analysis/delay/root-cause", response_model=ResponseModel)
def get_delay_root_cause(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """延期根因分析"""
    service = DelayRootCauseService(db)
    result = service.analyze_root_cause(
        start_date=start_date,
        end_date=end_date,
        project_id=project_id
    )
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/delay/impact", response_model=ResponseModel)
def get_delay_impact(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """延期影响分析"""
    service = DelayRootCauseService(db)
    result = service.analyze_impact(start_date=start_date, end_date=end_date)
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/delay/trends", response_model=ResponseModel)
def get_delay_trends(
    months: int = Query(12, ge=1, le=24, description="分析月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """延期趋势分析"""
    service = DelayRootCauseService(db)
    result = service.analyze_trends(months=months)
    return ResponseModel(code=200, message="分析成功", data=result)

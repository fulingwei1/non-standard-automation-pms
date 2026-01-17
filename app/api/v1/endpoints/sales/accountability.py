# -*- coding: utf-8 -*-
"""
深度归责分析 API endpoints
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.pipeline_accountability_service import PipelineAccountabilityService

router = APIRouter()


@router.get("/analysis/accountability/by-stage", response_model=ResponseModel)
def get_accountability_by_stage(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """按环节归责分析"""
    service = PipelineAccountabilityService(db)
    result = service.analyze_by_stage(start_date=start_date, end_date=end_date)
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/accountability/by-person", response_model=ResponseModel)
def get_accountability_by_person(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """按人员归责分析"""
    service = PipelineAccountabilityService(db)
    result = service.analyze_by_person(start_date=start_date, end_date=end_date)
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/accountability/by-department", response_model=ResponseModel)
def get_accountability_by_department(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """按部门归责分析"""
    service = PipelineAccountabilityService(db)
    result = service.analyze_by_department(start_date=start_date, end_date=end_date)
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/accountability/cost-impact", response_model=ResponseModel)
def get_accountability_cost_impact(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """责任成本分析"""
    service = PipelineAccountabilityService(db)
    result = service.analyze_cost_impact(start_date=start_date, end_date=end_date)
    return ResponseModel(code=200, message="分析成功", data=result)

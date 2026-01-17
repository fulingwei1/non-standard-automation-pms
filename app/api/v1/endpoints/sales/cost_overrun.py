# -*- coding: utf-8 -*-
"""
成本过高分析 API endpoints
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService

router = APIRouter()


@router.get("/analysis/cost-overrun/reasons", response_model=ResponseModel)
def get_cost_overrun_reasons(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """成本超支原因分析"""
    service = CostOverrunAnalysisService(db)
    result = service.analyze_reasons(
        start_date=start_date,
        end_date=end_date,
        project_id=project_id
    )
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/cost-overrun/accountability", response_model=ResponseModel)
def get_cost_overrun_accountability(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """成本超支归责"""
    service = CostOverrunAnalysisService(db)
    result = service.analyze_accountability(start_date=start_date, end_date=end_date)
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/cost-overrun/impact", response_model=ResponseModel)
def get_cost_overrun_impact(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """成本超支影响分析"""
    service = CostOverrunAnalysisService(db)
    result = service.analyze_impact(start_date=start_date, end_date=end_date)
    return ResponseModel(code=200, message="分析成功", data=result)

# -*- coding: utf-8 -*-
"""
多维度交叉分析 API endpoints
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
from app.services.delay_root_cause_service import DelayRootCauseService
from app.services.information_gap_analysis_service import InformationGapAnalysisService

router = APIRouter()


@router.get("/analysis/cross-dimension", response_model=ResponseModel)
def get_cross_dimension_analysis(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    dimensions: str = Query("all", description="分析维度：delay_cost/delay_info/cost_info/all"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """多维度交叉分析"""
    delay_service = DelayRootCauseService(db)
    cost_service = CostOverrunAnalysisService(db)
    info_service = InformationGapAnalysisService(db)

    result = {}

    if dimensions in ['delay_cost', 'all']:
        # 延期+成本交叉分析
        delay_analysis = delay_service.analyze_impact(start_date, end_date)
        cost_analysis = cost_service.analyze_reasons(start_date, end_date)
        result['delay_cost'] = {
            'delay_impact': delay_analysis,
            'cost_overrun': cost_analysis
        }

    if dimensions in ['delay_info', 'all']:
        # 延期+信息交叉分析
        delay_analysis = delay_service.analyze_root_cause(start_date, end_date)
        info_analysis = info_service.analyze_impact(start_date, end_date)
        result['delay_info'] = {
            'delay_reasons': delay_analysis,
            'info_quality': info_analysis
        }

    if dimensions in ['cost_info', 'all']:
        # 成本+信息交叉分析
        cost_analysis = cost_service.analyze_reasons(start_date, end_date)
        info_analysis = info_service.analyze_impact(start_date, end_date)
        result['cost_info'] = {
            'cost_overrun': cost_analysis,
            'info_quality': info_analysis
        }

    if dimensions == 'all':
        # 全维度综合分析
        result['comprehensive'] = {
            'delay': delay_service.analyze_root_cause(start_date, end_date),
            'cost': cost_service.analyze_reasons(start_date, end_date),
            'info': info_service.analyze_impact(start_date, end_date)
        }

    return ResponseModel(code=200, message="分析成功", data=result)

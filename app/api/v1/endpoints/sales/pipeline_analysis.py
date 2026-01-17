# -*- coding: utf-8 -*-
"""
全链条断链检测与分析 API endpoints
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService

router = APIRouter()


@router.get("/analysis/pipeline-breaks", response_model=ResponseModel)
def get_pipeline_breaks(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    pipeline_type: Optional[str] = Query(None, description="流程类型：LEAD/OPPORTUNITY/QUOTE/CONTRACT"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取断链分析"""
    service = PipelineBreakAnalysisService(db)
    result = service.analyze_pipeline_breaks(
        start_date=start_date,
        end_date=end_date,
        pipeline_type=pipeline_type
    )
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/break-reasons", response_model=ResponseModel)
def get_break_reasons(
    break_stage: Optional[str] = Query(None, description="断链环节"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取断链原因统计"""
    service = PipelineBreakAnalysisService(db)
    result = service.get_break_reasons(
        break_stage=break_stage,
        start_date=start_date,
        end_date=end_date
    )
    return ResponseModel(code=200, message="查询成功", data=result)


@router.get("/analysis/break-patterns", response_model=ResponseModel)
def get_break_patterns(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取断链模式分析"""
    service = PipelineBreakAnalysisService(db)
    result = service.get_break_patterns(
        start_date=start_date,
        end_date=end_date
    )
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/alerts/pipeline-break-warnings", response_model=ResponseModel)
def get_pipeline_break_warnings(
    days_ahead: int = Query(7, ge=1, le=30, description="提前预警天数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取断链预警列表"""
    service = PipelineBreakAnalysisService(db)
    warnings = service.get_break_warnings(days_ahead=days_ahead)
    return ResponseModel(code=200, message="查询成功", data={'warnings': warnings})

# -*- coding: utf-8 -*-
"""
信息把握不足分析 API endpoints
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.information_gap_analysis_service import InformationGapAnalysisService

router = APIRouter()


@router.get("/analysis/information-gap/missing", response_model=ResponseModel)
def get_information_gap_missing(
    entity_type: str = Query(..., description="实体类型：LEAD/OPPORTUNITY/QUOTE"),
    entity_id: Optional[int] = Query(None, description="实体ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """信息缺失分析"""
    service = InformationGapAnalysisService(db)
    try:
        result = service.analyze_missing(entity_type=entity_type, entity_id=entity_id)
        return ResponseModel(code=200, message="分析成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/information-gap/impact", response_model=ResponseModel)
def get_information_gap_impact(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """信息把握不足影响分析"""
    service = InformationGapAnalysisService(db)
    result = service.analyze_impact(start_date=start_date, end_date=end_date)
    return ResponseModel(code=200, message="分析成功", data=result)


@router.get("/analysis/information-gap/quality-score", response_model=ResponseModel)
def get_information_quality_score(
    entity_type: str = Query(..., description="实体类型：LEAD/OPPORTUNITY/QUOTE"),
    entity_id: int = Query(..., description="实体ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """信息质量评分"""
    service = InformationGapAnalysisService(db)
    try:
        result = service.get_quality_score(entity_type=entity_type, entity_id=entity_id)
        return ResponseModel(code=200, message="查询成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

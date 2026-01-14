# -*- coding: utf-8 -*-
"""
未中标深度分析 API endpoints
"""

from typing import Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.loss_deep_analysis_service import LossDeepAnalysisService

router = APIRouter()


@router.get("/analysis/loss-deep-analysis", response_model=ResponseModel)
def get_loss_deep_analysis(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    salesperson_id: Optional[int] = Query(None, description="销售人员ID"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取未中标深度分析
    """
    service = LossDeepAnalysisService(db)
    result = service.analyze_lost_projects(
        start_date=start_date,
        end_date=end_date,
        salesperson_id=salesperson_id,
        department_id=department_id
    )

    return ResponseModel(
        code=200,
        message="分析成功",
        data=result
    )


@router.get("/analysis/loss-by-stage", response_model=ResponseModel)
def get_loss_by_stage(
    stage: str = Query(..., description="投入阶段：requirement_only/design/detailed_design/quotation"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按投入阶段分析未中标情况
    """
    service = LossDeepAnalysisService(db)
    result = service.analyze_by_stage(
        stage=stage,
        start_date=start_date,
        end_date=end_date
    )

    return ResponseModel(
        code=200,
        message="分析成功",
        data=result
    )


@router.get("/analysis/loss-patterns", response_model=ResponseModel)
def get_loss_patterns(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    识别未中标模式
    """
    service = LossDeepAnalysisService(db)
    result = service.analyze_lost_projects(
        start_date=start_date,
        end_date=end_date
    )

    return ResponseModel(
        code=200,
        message="分析成功",
        data=result.get('pattern_analysis', {})
    )


@router.get("/analysis/loss-by-person", response_model=ResponseModel)
def get_loss_by_person(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按人员分析未中标情况
    """
    service = LossDeepAnalysisService(db)
    result = service.analyze_lost_projects(
        start_date=start_date,
        end_date=end_date
    )

    # 提取按人员统计的数据
    investment_analysis = result.get('investment_analysis', {})
    by_person = investment_analysis.get('by_person', [])[:limit]

    return ResponseModel(
        code=200,
        message="分析成功",
        data={
            'by_person': by_person,
            'summary': investment_analysis.get('summary', {})
        }
    )

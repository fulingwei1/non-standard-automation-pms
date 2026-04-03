# -*- coding: utf-8 -*-
"""
项目利润优化分析模块

路由: /projects/{project_id}/costs/
- GET /profit-optimization — 综合利润分析
- GET /margin-analysis — 毛利率实时分析
- GET /cost-optimization — 成本优化建议
- GET /quote-cost-variance — 报价与成本偏差
- GET /high-profit-patterns — 高利润项目特征（全局）
- GET /low-profit-root-cause — 低利润根因分析（全局）
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.profit_analysis_service import ProfitAnalysisService

router = APIRouter()


@router.get("/profit-optimization", response_model=ResponseModel)
def get_profit_optimization(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    target_margin: float = Query(25.0, description="目标毛利率（%）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    综合利润分析
    聚合毛利率、成本优化建议、报价偏差分析
    """
    service = ProfitAnalysisService(db)
    result = service.get_profit_analysis(project_id, target_margin)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return ResponseModel(code=200, message="success", data=result)


@router.get("/margin-analysis", response_model=ResponseModel)
def get_margin_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    target_margin: float = Query(25.0, description="目标毛利率（%）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    毛利率实时分析
    当前毛利、预计毛利、与目标对比
    """
    service = ProfitAnalysisService(db)
    result = service.get_margin_analysis(project_id, target_margin)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return ResponseModel(code=200, message="success", data=result)


@router.get("/cost-optimization", response_model=ResponseModel)
def get_cost_optimization(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    成本优化建议
    基于历史数据识别可优化的成本项
    """
    service = ProfitAnalysisService(db)
    result = service.get_cost_optimization(project_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return ResponseModel(code=200, message="success", data=result)


@router.get("/quote-cost-variance", response_model=ResponseModel)
def get_quote_cost_variance(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    报价与成本偏差分析
    分析报价预估 vs 实际成本的偏差
    """
    service = ProfitAnalysisService(db)
    result = service.get_quote_cost_variance(project_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return ResponseModel(code=200, message="success", data=result)


@router.get("/high-profit-patterns", response_model=ResponseModel)
def get_high_profit_patterns(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    min_margin: float = Query(30.0, description="高利润阈值（%）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    高利润项目特征分析
    分析高毛利项目的共同特征和成功模式
    """
    service = ProfitAnalysisService(db)
    result = service.get_high_profit_patterns(min_margin)
    return ResponseModel(code=200, message="success", data=result)


@router.get("/low-profit-root-cause", response_model=ResponseModel)
def get_low_profit_root_cause(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    max_margin: float = Query(10.0, description="低利润阈值（%）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    低利润项目根因分析
    分析低毛利项目的主要问题、预警信号和改进建议
    """
    service = ProfitAnalysisService(db)
    result = service.get_low_profit_root_cause(max_margin)
    return ResponseModel(code=200, message="success", data=result)

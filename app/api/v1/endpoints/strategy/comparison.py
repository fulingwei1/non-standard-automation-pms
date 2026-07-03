# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - 同比分析
"""

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.schemas.common import PageResponse
from app.schemas.strategy import (
    StrategyComparisonCreate,
    StrategyComparisonResponse,
)
from app.schemas.strategy.yoy_report import YoYReportResponse
from app.services import strategy as strategy_service

router = APIRouter()


def _json_list(value):
    if value in (None, ""):
        return None
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, list) else None


def _comparison_response(comparison) -> StrategyComparisonResponse:
    return StrategyComparisonResponse(
        id=comparison.id,
        current_strategy_id=comparison.current_strategy_id,
        previous_strategy_id=comparison.previous_strategy_id,
        current_year=comparison.current_year,
        previous_year=comparison.previous_year,
        generated_date=comparison.generated_date,
        generated_by=comparison.generated_by,
        current_health_score=comparison.current_health_score,
        previous_health_score=comparison.previous_health_score,
        health_change=comparison.health_change,
        current_financial_score=comparison.current_financial_score,
        previous_financial_score=comparison.previous_financial_score,
        financial_change=comparison.financial_change,
        current_customer_score=comparison.current_customer_score,
        previous_customer_score=comparison.previous_customer_score,
        customer_change=comparison.customer_change,
        current_internal_score=comparison.current_internal_score,
        previous_internal_score=comparison.previous_internal_score,
        internal_change=comparison.internal_change,
        current_learning_score=comparison.current_learning_score,
        previous_learning_score=comparison.previous_learning_score,
        learning_change=comparison.learning_change,
        kpi_completion_rate=comparison.kpi_completion_rate,
        previous_kpi_completion_rate=comparison.previous_kpi_completion_rate,
        kpi_completion_change=comparison.kpi_completion_change,
        work_completion_rate=comparison.work_completion_rate,
        previous_work_completion_rate=comparison.previous_work_completion_rate,
        work_completion_change=comparison.work_completion_change,
        summary=comparison.summary,
        highlights=_json_list(comparison.highlights),
        improvements=_json_list(comparison.improvements),
        recommendations=_json_list(comparison.recommendations),
        is_active=True if comparison.is_active is None else comparison.is_active,
        generator_name=comparison.generator.display_name if comparison.generator else None,
        current_strategy_name=(
            comparison.current_strategy.name if comparison.current_strategy else None
        ),
        previous_strategy_name=(
            comparison.previous_strategy.name if comparison.previous_strategy else None
        ),
        created_at=comparison.created_at,
        updated_at=comparison.updated_at,
    )


@router.post("", response_model=StrategyComparisonResponse, status_code=status.HTTP_201_CREATED)
def create_comparison(
    data: StrategyComparisonCreate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    创建战略对比记录
    """
    comparison = strategy_service.create_strategy_comparison(db, data, current_user.id)
    return _comparison_response(comparison)


@router.get("", response_model=PageResponse[StrategyComparisonResponse])
def list_comparisons(
    current_strategy_id: Optional[int] = Query(None, description="当前战略 ID 筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
):
    """
    获取战略对比记录列表
    """
    items, total = strategy_service.list_strategy_comparisons(
        db, current_strategy_id, pagination.offset, pagination.limit
    )

    responses = [_comparison_response(c) for c in items]

    return PageResponse(
        items=responses,
        total=total,
        skip=pagination.offset,
        limit=pagination.limit,
    )


@router.get("/yoy-report", response_model=YoYReportResponse)
def get_yoy_report(
    current_year: int = Query(..., description="当前年度"),
    previous_year: Optional[int] = Query(None, description="对比年度（默认为上一年）"),
    db: Session = Depends(deps.get_db),
):
    """
    生成同比报告
    """
    return strategy_service.generate_yoy_report(db, current_year, previous_year)


@router.get("/multi-year-trend", response_model=Dict[str, Any])
def get_multi_year_trend(
    years: int = Query(3, ge=1, le=10, description="年数"),
    db: Session = Depends(deps.get_db),
):
    """
    获取多年趋势数据
    """
    return strategy_service.get_multi_year_trend(db, years)


@router.get("/kpi-achievement", response_model=Dict[str, Any])
def get_kpi_achievement_comparison(
    current_year: int = Query(..., description="当前年度"),
    previous_year: Optional[int] = Query(None, description="对比年度"),
    db: Session = Depends(deps.get_db),
):
    """
    获取 KPI 达成率对比
    """
    return strategy_service.get_kpi_achievement_comparison(db, current_year, previous_year)


@router.get("/{comparison_id}", response_model=StrategyComparisonResponse)
def get_comparison(
    comparison_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取战略对比记录详情
    """
    comparison = strategy_service.get_strategy_comparison(db, comparison_id)
    if not comparison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对比记录不存在")

    return StrategyComparisonResponse.model_validate(comparison)


@router.delete("/{comparison_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comparison(
    comparison_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    删除战略对比记录（软删除）
    """
    success = strategy_service.delete_strategy_comparison(db, comparison_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对比记录不存在")
    return None

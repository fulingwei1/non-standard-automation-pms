# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - 同比分析
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.common import PageResponse
from app.schemas.strategy import (
    StrategyComparisonCreate,
    StrategyComparisonResponse,
    YoYReportResponse,
)
from app.services import strategy as strategy_service
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.post("", response_model=StrategyComparisonResponse, status_code=status.HTTP_201_CREATED)
def create_comparison(
    data: StrategyComparisonCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建战略对比记录
    """
    comparison = strategy_service.create_strategy_comparison(db, data, current_user.id)
    return StrategyComparisonResponse(
        id=comparison.id,
        base_strategy_id=comparison.base_strategy_id,
        compare_strategy_id=comparison.compare_strategy_id,
        comparison_type=comparison.comparison_type,
        base_year=comparison.base_year,
        compare_year=comparison.compare_year,
        summary=comparison.summary,
        created_by=comparison.created_by,
        is_active=comparison.is_active,
        created_at=comparison.created_at,
        updated_at=comparison.updated_at,
    )


@router.get("", response_model=PageResponse[StrategyComparisonResponse])
def list_comparisons(
    base_strategy_id: Optional[int] = Query(None, description="基准战略 ID 筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
):
    """
    获取战略对比记录列表
    """
    items, total = strategy_service.list_strategy_comparisons(
        db, base_strategy_id, skip, limit
    )

    responses = [
        StrategyComparisonResponse(
            id=c.id,
            base_strategy_id=c.base_strategy_id,
            compare_strategy_id=c.compare_strategy_id,
            comparison_type=c.comparison_type,
            base_year=c.base_year,
            compare_year=c.compare_year,
            summary=c.summary,
            created_by=c.created_by,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in items
    ]

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对比记录不存在"
        )

    return StrategyComparisonResponse(
        id=comparison.id,
        base_strategy_id=comparison.base_strategy_id,
        compare_strategy_id=comparison.compare_strategy_id,
        comparison_type=comparison.comparison_type,
        base_year=comparison.base_year,
        compare_year=comparison.compare_year,
        summary=comparison.summary,
        created_by=comparison.created_by,
        is_active=comparison.is_active,
        created_at=comparison.created_at,
        updated_at=comparison.updated_at,
    )


@router.delete("/{comparison_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comparison(
    comparison_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除战略对比记录（软删除）
    """
    success = strategy_service.delete_strategy_comparison(db, comparison_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对比记录不存在"
        )
    return None

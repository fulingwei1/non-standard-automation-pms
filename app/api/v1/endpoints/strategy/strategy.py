# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - Strategy CRUD
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.common import PageResponse
from app.schemas.strategy import (
    StrategyCreate,
    StrategyDetailResponse,
    StrategyMapResponse,
    StrategyPublishRequest,
    StrategyResponse,
    StrategyUpdate,
)
from app.services import strategy as strategy_service

router = APIRouter()


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy(
    data: StrategyCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建战略
    """
    # 检查编码是否重复
    existing = strategy_service.get_strategy_by_code(db, data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"战略编码 {data.code} 已存在"
        )

    # 检查年度是否重复
    existing_year = strategy_service.get_strategy_by_year(db, data.year)
    if existing_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{data.year} 年度战略已存在"
        )

    strategy = strategy_service.create_strategy(db, data, current_user.id)
    return strategy


@router.get("", response_model=PageResponse[StrategyResponse])
def list_strategies(
    year: Optional[int] = Query(None, description="年度筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
):
    """
    获取战略列表
    """
    items, total = strategy_service.list_strategies(
        db, year=year, status=status_filter, skip=skip, limit=limit
    )
    return PageResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/active", response_model=StrategyResponse)
def get_active_strategy(
    db: Session = Depends(deps.get_db),
):
    """
    获取当前生效的战略
    """
    strategy = strategy_service.get_active_strategy(db)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="当前没有生效的战略"
        )
    return strategy


@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
def get_strategy(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取战略详情
    """
    detail = strategy_service.get_strategy_detail(db, strategy_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战略不存在"
        )
    return detail


@router.get("/{strategy_id}/map", response_model=StrategyMapResponse)
def get_strategy_map(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取战略地图数据
    """
    map_data = strategy_service.get_strategy_map_data(db, strategy_id)
    if not map_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战略不存在"
        )
    return map_data


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy(
    strategy_id: int,
    data: StrategyUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新战略
    """
    strategy = strategy_service.update_strategy(db, strategy_id, data)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战略不存在"
        )
    return strategy


@router.post("/{strategy_id}/publish", response_model=StrategyResponse)
def publish_strategy(
    strategy_id: int,
    data: StrategyPublishRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    发布战略
    """
    strategy = strategy_service.publish_strategy(db, strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战略不存在"
        )
    return strategy


@router.post("/{strategy_id}/archive", response_model=StrategyResponse)
def archive_strategy(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    归档战略
    """
    strategy = strategy_service.archive_strategy(db, strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战略不存在"
        )
    return strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除战略（软删除）
    """
    success = strategy_service.delete_strategy(db, strategy_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战略不存在"
        )
    return None

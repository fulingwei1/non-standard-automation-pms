# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - CSF 关键成功要素
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.common import PageResponse
from app.schemas.strategy import (
    CSFBatchCreateRequest,
    CSFByDimensionResponse,
    CSFCreate,
    CSFDetailResponse,
    CSFResponse,
    CSFUpdate,
)
from app.services import strategy as strategy_service

router = APIRouter()


@router.post("", response_model=CSFResponse, status_code=status.HTTP_201_CREATED)
def create_csf(
    data: CSFCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建 CSF
    """
    # 验证战略是否存在
    strategy = strategy_service.get_strategy(db, data.strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的战略不存在"
        )

    csf = strategy_service.create_csf(db, data)
    return csf


@router.post("/batch", response_model=List[CSFResponse], status_code=status.HTTP_201_CREATED)
def batch_create_csfs(
    data: CSFBatchCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    批量创建 CSF
    """
    # 验证战略是否存在
    strategy = strategy_service.get_strategy(db, data.strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的战略不存在"
        )

    csfs = strategy_service.batch_create_csfs(db, data.strategy_id, data.items)
    return csfs


@router.get("", response_model=PageResponse[CSFResponse])
def list_csfs(
    strategy_id: int = Query(..., description="战略 ID"),
    dimension: Optional[str] = Query(None, description="BSC 维度筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
):
    """
    获取 CSF 列表
    """
    items, total = strategy_service.list_csfs(
        db, strategy_id=strategy_id, dimension=dimension, skip=skip, limit=limit
    )
    return PageResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/by-dimension", response_model=List[CSFByDimensionResponse])
def get_csfs_by_dimension(
    strategy_id: int = Query(..., description="战略 ID"),
    db: Session = Depends(deps.get_db),
):
    """
    按维度分组获取 CSF
    """
    return strategy_service.get_csfs_by_dimension(db, strategy_id)


@router.get("/{csf_id}", response_model=CSFDetailResponse)
def get_csf(
    csf_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取 CSF 详情
    """
    detail = strategy_service.get_csf_detail(db, csf_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSF 不存在"
        )
    return detail


@router.put("/{csf_id}", response_model=CSFResponse)
def update_csf(
    csf_id: int,
    data: CSFUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新 CSF
    """
    csf = strategy_service.update_csf(db, csf_id, data)
    if not csf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSF 不存在"
        )
    return csf


@router.delete("/{csf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_csf(
    csf_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除 CSF（软删除）
    """
    success = strategy_service.delete_csf(db, csf_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSF 不存在"
        )
    return None

# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - KPI 关键绩效指标
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.common import PageResponse
from app.schemas.strategy import (
    KPICollectRequest,
    KPICollectResponse,
    KPICreate,
    KPIDataSourceCreate,
    KPIDataSourceResponse,
    KPIDetailResponse,
    KPIHistoryResponse,
    KPIResponse,
    KPIUpdate,
    KPIValueUpdate,
    KPIWithHistoryResponse,
)
from app.services import strategy as strategy_service

router = APIRouter()


@router.post("", response_model=KPIResponse, status_code=status.HTTP_201_CREATED)
def create_kpi(
    data: KPICreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建 KPI
    """
    # 验证 CSF 是否存在
    csf = strategy_service.get_csf(db, data.csf_id)
    if not csf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的 CSF 不存在"
        )

    kpi = strategy_service.create_kpi(db, data)
    return kpi


@router.get("", response_model=PageResponse[KPIResponse])
def list_kpis(
    csf_id: Optional[int] = Query(None, description="CSF ID 筛选"),
    strategy_id: Optional[int] = Query(None, description="战略 ID 筛选"),
    ipooc_type: Optional[str] = Query(None, description="IPOOC 类型筛选"),
    data_source_type: Optional[str] = Query(None, description="数据源类型筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
):
    """
    获取 KPI 列表
    """
    items, total = strategy_service.list_kpis(
        db,
        csf_id=csf_id,
        strategy_id=strategy_id,
        ipooc_type=ipooc_type,
        data_source_type=data_source_type,
        skip=skip,
        limit=limit
    )
    return PageResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{kpi_id}", response_model=KPIDetailResponse)
def get_kpi(
    kpi_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取 KPI 详情
    """
    detail = strategy_service.get_kpi_detail(db, kpi_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI 不存在"
        )
    return detail


@router.get("/{kpi_id}/history", response_model=List[KPIHistoryResponse])
def get_kpi_history(
    kpi_id: int,
    limit: int = Query(12, ge=1, le=100, description="历史记录数量"),
    db: Session = Depends(deps.get_db),
):
    """
    获取 KPI 历史记录
    """
    kpi = strategy_service.get_kpi(db, kpi_id)
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI 不存在"
        )

    return strategy_service.get_kpi_history(db, kpi_id, limit)


@router.get("/{kpi_id}/with-history", response_model=KPIWithHistoryResponse)
def get_kpi_with_history(
    kpi_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取 KPI 详情及历史
    """
    result = strategy_service.get_kpi_with_history(db, kpi_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI 不存在"
        )
    return result


@router.put("/{kpi_id}", response_model=KPIResponse)
def update_kpi(
    kpi_id: int,
    data: KPIUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新 KPI
    """
    kpi = strategy_service.update_kpi(db, kpi_id, data)
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI 不存在"
        )
    return kpi


@router.post("/{kpi_id}/value", response_model=KPIResponse)
def update_kpi_value(
    kpi_id: int,
    data: KPIValueUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新 KPI 当前值
    """
    kpi = strategy_service.update_kpi_value(
        db, kpi_id, data.value, current_user.id, data.remark
    )
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI 不存在"
        )
    return kpi


@router.delete("/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kpi(
    kpi_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除 KPI（软删除）
    """
    success = strategy_service.delete_kpi(db, kpi_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI 不存在"
        )
    return None


# ============================================
# 数据采集
# ============================================

@router.post("/{kpi_id}/collect", response_model=KPIResponse)
def collect_kpi(
    kpi_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    采集单个 KPI 数据
    """
    kpi = strategy_service.auto_collect_kpi(db, kpi_id, current_user.id)
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KPI 采集失败，请检查数据源配置"
        )
    return kpi


@router.post("/batch-collect", response_model=KPICollectResponse)
def batch_collect_kpis(
    data: KPICollectRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    批量采集 KPI 数据
    """
    result = strategy_service.batch_collect_kpis(
        db,
        strategy_id=data.strategy_id,
        frequency=data.frequency
    )
    return KPICollectResponse(
        total=result["total"],
        success=result["success"],
        failed=result["failed"],
        failed_kpis=result["failed_kpis"],
        collected_at=result["collected_at"],
    )


@router.get("/collection-status/{strategy_id}", response_model=Dict[str, Any])
def get_collection_status(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取采集状态概览
    """
    return strategy_service.get_collection_status(db, strategy_id)


# ============================================
# 数据源管理
# ============================================

@router.post("/{kpi_id}/data-sources", response_model=KPIDataSourceResponse, status_code=status.HTTP_201_CREATED)
def create_data_source(
    kpi_id: int,
    data: KPIDataSourceCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建 KPI 数据源配置
    """
    kpi = strategy_service.get_kpi(db, kpi_id)
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI 不存在"
        )

    data.kpi_id = kpi_id
    source = strategy_service.create_kpi_data_source(db, data)
    return source


@router.get("/{kpi_id}/data-sources", response_model=List[KPIDataSourceResponse])
def get_data_sources(
    kpi_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取 KPI 数据源配置列表
    """
    kpi = strategy_service.get_kpi(db, kpi_id)
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI 不存在"
        )

    return strategy_service.get_kpi_data_sources(db, kpi_id)

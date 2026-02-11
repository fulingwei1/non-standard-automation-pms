# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - 年度重点工作
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.common import PageResponse
from app.schemas.strategy import (
    AnnualKeyWorkCreate,
    AnnualKeyWorkDetailResponse,
    AnnualKeyWorkProgressUpdate,
    AnnualKeyWorkResponse,
    AnnualKeyWorkUpdate,
    LinkProjectRequest,
    ProjectLinkItem,
    UnlinkProjectRequest,
)
from app.services import strategy as strategy_service
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.post("", response_model=AnnualKeyWorkResponse, status_code=status.HTTP_201_CREATED)
def create_annual_work(
    data: AnnualKeyWorkCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建年度重点工作
    """
    # 验证 CSF 是否存在
    csf = strategy_service.get_csf(db, data.csf_id)
    if not csf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的 CSF 不存在"
        )

    work = strategy_service.create_annual_work(db, data)
    return work


@router.get("", response_model=PageResponse[AnnualKeyWorkResponse])
def list_annual_works(
    csf_id: Optional[int] = Query(None, description="CSF ID 筛选"),
    strategy_id: Optional[int] = Query(None, description="战略 ID 筛选"),
    year: Optional[int] = Query(None, description="年度筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
):
    """
    获取年度重点工作列表
    """
    items, total = strategy_service.list_annual_works(
        db,
        csf_id=csf_id,
        strategy_id=strategy_id,
        year=year,
        status=status_filter,
        skip=pagination.offset,
        limit=pagination.limit
    )
    return PageResponse(
        items=items,
        total=total,
        skip=pagination.offset,
        limit=pagination.limit,
    )


@router.get("/stats/{strategy_id}", response_model=Dict[str, Any])
def get_annual_work_stats(
    strategy_id: int,
    year: Optional[int] = Query(None, description="年度"),
    db: Session = Depends(deps.get_db),
):
    """
    获取年度重点工作统计
    """
    return strategy_service.get_annual_work_stats(db, strategy_id, year)


@router.get("/{work_id}", response_model=AnnualKeyWorkDetailResponse)
def get_annual_work(
    work_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取年度重点工作详情
    """
    detail = strategy_service.get_annual_work_detail(db, work_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="年度重点工作不存在"
        )
    return detail


@router.put("/{work_id}", response_model=AnnualKeyWorkResponse)
def update_annual_work(
    work_id: int,
    data: AnnualKeyWorkUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新年度重点工作
    """
    work = strategy_service.update_annual_work(db, work_id, data)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="年度重点工作不存在"
        )
    return work


@router.post("/{work_id}/progress", response_model=AnnualKeyWorkResponse)
def update_progress(
    work_id: int,
    data: AnnualKeyWorkProgressUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新进度
    """
    work = strategy_service.update_progress(db, work_id, data)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="年度重点工作不存在"
        )
    return work


@router.delete("/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_annual_work(
    work_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除年度重点工作（软删除）
    """
    success = strategy_service.delete_annual_work(db, work_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="年度重点工作不存在"
        )
    return None


# ============================================
# 项目关联
# ============================================

@router.post("/{work_id}/link-project", response_model=Dict[str, Any])
def link_project(
    work_id: int,
    data: LinkProjectRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    关联项目
    """
    link = strategy_service.link_project(
        db, work_id, data.project_id, data.contribution_weight
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="年度重点工作不存在"
        )
    return {"message": "项目关联成功", "link_id": link.id}


@router.post("/{work_id}/unlink-project", status_code=status.HTTP_204_NO_CONTENT)
def unlink_project(
    work_id: int,
    data: UnlinkProjectRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    取消关联项目
    """
    success = strategy_service.unlink_project(db, work_id, data.project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关联关系不存在"
        )
    return None


@router.get("/{work_id}/linked-projects", response_model=List[ProjectLinkItem])
def get_linked_projects(
    work_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取关联的项目列表
    """
    work = strategy_service.get_annual_work(db, work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="年度重点工作不存在"
        )

    return strategy_service.get_linked_projects(db, work_id)


@router.post("/{work_id}/sync-progress", response_model=AnnualKeyWorkResponse)
def sync_progress_from_projects(
    work_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    从关联项目同步进度
    """
    work = strategy_service.sync_progress_from_projects(db, work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同步失败，可能没有关联项目或项目无进度数据"
        )
    return work

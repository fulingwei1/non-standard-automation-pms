# -*- coding: utf-8 -*-
"""
销售区域管理 API 端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.sales_team import (
    SalesRegionCreate,
    SalesRegionUpdate,
    SalesRegionResponse,
    SalesRegionAssignTeam,
)
from app.schemas.common import ResponseModel
from app.services.sales_team_service import SalesRegionService
from app.core.security import require_permission

router = APIRouter()


@router.post("", response_model=ResponseModel)
@require_permission("sales_region:create")
def create_region(
    *,
    db: Session = Depends(deps.get_db),
    region_in: SalesRegionCreate,
    current_user = Depends(deps.get_current_user),
):
    """创建销售区域"""
    region = SalesRegionService.create_region(db, region_in, current_user.id)
    return ResponseModel(code=200, message="创建成功", data=SalesRegionResponse.from_orm(region))


@router.get("", response_model=ResponseModel)
@require_permission("sales_region:view")
def get_regions(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user = Depends(deps.get_current_user),
):
    """获取销售区域列表"""
    regions = SalesRegionService.get_regions(
        db,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )
    return ResponseModel(
        code=200,
        message="查询成功",
        data=[SalesRegionResponse.from_orm(region) for region in regions]
    )


@router.get("/{region_id}", response_model=ResponseModel)
@require_permission("sales_region:view")
def get_region(
    region_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取销售区域详情"""
    region = SalesRegionService.get_region(db, region_id)
    if not region:
        return ResponseModel(code=404, message="区域不存在")
    return ResponseModel(code=200, message="查询成功", data=SalesRegionResponse.from_orm(region))


@router.put("/{region_id}", response_model=ResponseModel)
@require_permission("sales_region:update")
def update_region(
    region_id: int,
    region_in: SalesRegionUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """更新销售区域"""
    region = SalesRegionService.update_region(db, region_id, region_in)
    return ResponseModel(code=200, message="更新成功", data=SalesRegionResponse.from_orm(region))


@router.post("/{region_id}/assign-team", response_model=ResponseModel)
@require_permission("sales_region:update")
def assign_team(
    region_id: int,
    assign_data: SalesRegionAssignTeam,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """分配团队"""
    region = SalesRegionService.assign_team(
        db,
        region_id,
        assign_data.team_id,
        assign_data.leader_id
    )
    return ResponseModel(code=200, message="分配成功", data=SalesRegionResponse.from_orm(region))

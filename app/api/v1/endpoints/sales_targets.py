# -*- coding: utf-8 -*-
"""
销售目标管理 API 端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.sales_target import (
    SalesTargetV2Create,
    SalesTargetV2Update,
    SalesTargetV2Response,
    TargetBreakdownRequest,
    AutoBreakdownRequest,
)
from app.schemas.common import ResponseModel
from app.services.sales_target_service import SalesTargetService
from app.core.security import require_permission

router = APIRouter()


@router.post("", response_model=ResponseModel)
@require_permission("sales_target:create")
def create_target(
    *,
    db: Session = Depends(deps.get_db),
    target_in: SalesTargetV2Create,
    current_user = Depends(deps.get_current_user),
):
    """创建销售目标"""
    target = SalesTargetService.create_target(db, target_in, current_user.id)
    return ResponseModel(code=200, message="创建成功", data=SalesTargetV2Response.from_orm(target))


@router.get("", response_model=ResponseModel)
@require_permission("sales_target:view")
def get_targets(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    target_type: Optional[str] = None,
    target_period: Optional[str] = None,
    target_year: Optional[int] = None,
    target_month: Optional[int] = None,
    team_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user = Depends(deps.get_current_user),
):
    """获取销售目标列表"""
    targets = SalesTargetService.get_targets(
        db,
        skip=skip,
        limit=limit,
        target_type=target_type,
        target_period=target_period,
        target_year=target_year,
        target_month=target_month,
        team_id=team_id,
        user_id=user_id,
    )
    return ResponseModel(
        code=200,
        message="查询成功",
        data=[SalesTargetV2Response.from_orm(target) for target in targets]
    )


@router.get("/{target_id}", response_model=ResponseModel)
@require_permission("sales_target:view")
def get_target(
    target_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取销售目标详情"""
    target = SalesTargetService.get_target(db, target_id)
    if not target:
        return ResponseModel(code=404, message="目标不存在")
    return ResponseModel(code=200, message="查询成功", data=SalesTargetV2Response.from_orm(target))


@router.put("/{target_id}", response_model=ResponseModel)
@require_permission("sales_target:update")
def update_target(
    target_id: int,
    target_in: SalesTargetV2Update,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """更新销售目标"""
    target = SalesTargetService.update_target(db, target_id, target_in)
    return ResponseModel(code=200, message="更新成功", data=SalesTargetV2Response.from_orm(target))


@router.delete("/{target_id}", response_model=ResponseModel)
@require_permission("sales_target:delete")
def delete_target(
    target_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """删除销售目标"""
    SalesTargetService.delete_target(db, target_id)
    return ResponseModel(code=200, message="删除成功")


# ============= 目标分解 =============

@router.post("/{target_id}/breakdown", response_model=ResponseModel)
@require_permission("sales_target:update")
def breakdown_target(
    target_id: int,
    breakdown_data: TargetBreakdownRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """手动分解目标"""
    targets = SalesTargetService.breakdown_target(db, target_id, breakdown_data, current_user.id)
    return ResponseModel(
        code=200,
        message="分解成功",
        data={
            'parent_target_id': target_id,
            'breakdown_count': len(targets),
            'created_targets': [SalesTargetV2Response.from_orm(t) for t in targets]
        }
    )


@router.post("/{target_id}/auto-breakdown", response_model=ResponseModel)
@require_permission("sales_target:update")
def auto_breakdown_target(
    target_id: int,
    breakdown_data: AutoBreakdownRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """自动分解目标"""
    targets = SalesTargetService.auto_breakdown_target(db, target_id, breakdown_data, current_user.id)
    return ResponseModel(
        code=200,
        message="自动分解成功",
        data={
            'parent_target_id': target_id,
            'breakdown_count': len(targets),
            'created_targets': [SalesTargetV2Response.from_orm(t) for t in targets]
        }
    )


@router.get("/{target_id}/breakdown-tree", response_model=ResponseModel)
@require_permission("sales_target:view")
def get_breakdown_tree(
    target_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取目标分解树"""
    tree = SalesTargetService.get_breakdown_tree(db, target_id)
    return ResponseModel(code=200, message="查询成功", data=tree)


# ============= 统计分析 =============

@router.get("/stats/team-ranking", response_model=ResponseModel)
@require_permission("sales_target:view")
def get_team_ranking(
    target_year: int = Query(..., description="目标年份"),
    target_month: Optional[int] = Query(None, ge=1, le=12, description="目标月份"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取团队排名"""
    rankings = SalesTargetService.get_team_ranking(db, target_year, target_month)
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            'period': f"{target_year}-{target_month or '全年'}",
            'rankings': rankings
        }
    )


@router.get("/stats/personal-ranking", response_model=ResponseModel)
@require_permission("sales_target:view")
def get_personal_ranking(
    target_year: int = Query(..., description="目标年份"),
    target_month: Optional[int] = Query(None, ge=1, le=12, description="目标月份"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取个人排名"""
    rankings = SalesTargetService.get_personal_ranking(db, target_year, target_month)
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            'period': f"{target_year}-{target_month or '全年'}",
            'rankings': rankings
        }
    )


@router.get("/stats/completion-trend", response_model=ResponseModel)
@require_permission("sales_target:view")
def get_completion_trend(
    target_id: int = Query(..., description="目标ID"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取完成趋势"""
    trend = SalesTargetService.get_completion_trend(db, target_id)
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            'target_id': target_id,
            'trend_data': trend
        }
    )


@router.get("/stats/distribution", response_model=ResponseModel)
@require_permission("sales_target:view")
def get_completion_distribution(
    target_year: int = Query(..., description="目标年份"),
    target_month: Optional[int] = Query(None, ge=1, le=12, description="目标月份"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取完成率分布"""
    distribution = SalesTargetService.get_completion_distribution(db, target_year, target_month)
    return ResponseModel(code=200, message="查询成功", data=distribution)

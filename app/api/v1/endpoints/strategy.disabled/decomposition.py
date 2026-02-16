# -*- coding: utf-8 -*-
"""
战略管理 API 端点 - 目标分解
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.common import PageResponse
from app.schemas.strategy import (
    DecompositionTreeResponse,
    DepartmentObjectiveCreate,
    DepartmentObjectiveDetailResponse,
    DepartmentObjectiveResponse,
    DepartmentObjectiveUpdate,
    PersonalKPIBatchCreate,
    PersonalKPICreate,
    PersonalKPIManagerRatingRequest,
    PersonalKPIResponse,
    PersonalKPISelfRatingRequest,
    PersonalKPIUpdate,
    TraceToStrategyResponse,
)
from app.services import strategy as strategy_service
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


# ============================================
# 部门目标
# ============================================

@router.post("/department-objectives", response_model=DepartmentObjectiveResponse, status_code=status.HTTP_201_CREATED)
def create_department_objective(
    data: DepartmentObjectiveCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建部门目标
    """
    obj = strategy_service.create_department_objective(db, data)
    return obj


@router.get("/department-objectives", response_model=PageResponse[DepartmentObjectiveResponse])
def list_department_objectives(
    strategy_id: Optional[int] = Query(None, description="战略 ID 筛选"),
    department_id: Optional[int] = Query(None, description="部门 ID 筛选"),
    year: Optional[int] = Query(None, description="年度筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
):
    """
    获取部门目标列表
    """
    items, total = strategy_service.list_department_objectives(
        db,
        strategy_id=strategy_id,
        department_id=department_id,
        year=year,
        skip=pagination.offset,
        limit=pagination.limit
    )
    return PageResponse(
        items=items,
        total=total,
        skip=pagination.offset,
        limit=pagination.limit,
    )


@router.get("/department-objectives/{objective_id}", response_model=DepartmentObjectiveDetailResponse)
def get_department_objective(
    objective_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取部门目标详情
    """
    detail = strategy_service.get_department_objective_detail(db, objective_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门目标不存在"
        )
    return detail


@router.put("/department-objectives/{objective_id}", response_model=DepartmentObjectiveResponse)
def update_department_objective(
    objective_id: int,
    data: DepartmentObjectiveUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新部门目标
    """
    obj = strategy_service.update_department_objective(db, objective_id, data)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门目标不存在"
        )
    return obj


@router.delete("/department-objectives/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department_objective(
    objective_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除部门目标（软删除）
    """
    success = strategy_service.delete_department_objective(db, objective_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部门目标不存在"
        )
    return None


# ============================================
# 个人 KPI
# ============================================

@router.post("/personal-kpis", response_model=PersonalKPIResponse, status_code=status.HTTP_201_CREATED)
def create_personal_kpi(
    data: PersonalKPICreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    创建个人 KPI
    """
    kpi = strategy_service.create_personal_kpi(db, data)
    return kpi


@router.post("/personal-kpis/batch", response_model=List[PersonalKPIResponse], status_code=status.HTTP_201_CREATED)
def batch_create_personal_kpis(
    data: PersonalKPIBatchCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    批量创建个人 KPI
    """
    kpis = strategy_service.batch_create_personal_kpis(db, data.items)
    return kpis


@router.get("/personal-kpis", response_model=PageResponse[PersonalKPIResponse])
def list_personal_kpis(
    user_id: Optional[int] = Query(None, description="用户 ID 筛选"),
    dept_objective_id: Optional[int] = Query(None, description="部门目标 ID 筛选"),
    year: Optional[int] = Query(None, description="年度筛选"),
    period: Optional[str] = Query(None, description="周期筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
):
    """
    获取个人 KPI 列表
    """
    items, total = strategy_service.list_personal_kpis(
        db,
        user_id=user_id,
        dept_objective_id=dept_objective_id,
        year=year,
        period=period,
        skip=pagination.offset,
        limit=pagination.limit
    )
    return PageResponse(
        items=items,
        total=total,
        skip=pagination.offset,
        limit=pagination.limit,
    )


@router.get("/personal-kpis/my", response_model=PageResponse[PersonalKPIResponse])
def list_my_personal_kpis(
    year: Optional[int] = Query(None, description="年度筛选"),
    period: Optional[str] = Query(None, description="周期筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    获取我的个人 KPI 列表
    """
    items, total = strategy_service.list_personal_kpis(
        db,
        user_id=current_user.id,
        year=year,
        period=period,
        skip=pagination.offset,
        limit=pagination.limit
    )
    return PageResponse(
        items=items,
        total=total,
        skip=pagination.offset,
        limit=pagination.limit,
    )


@router.get("/personal-kpis/{kpi_id}", response_model=PersonalKPIResponse)
def get_personal_kpi(
    kpi_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取个人 KPI 详情
    """
    kpi = strategy_service.get_personal_kpi(db, kpi_id)
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人 KPI 不存在"
        )
    return kpi


@router.put("/personal-kpis/{kpi_id}", response_model=PersonalKPIResponse)
def update_personal_kpi(
    kpi_id: int,
    data: PersonalKPIUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    更新个人 KPI
    """
    kpi = strategy_service.update_personal_kpi(db, kpi_id, data)
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人 KPI 不存在"
        )
    return kpi


@router.post("/personal-kpis/{kpi_id}/self-rating", response_model=PersonalKPIResponse)
def self_rating(
    kpi_id: int,
    data: PersonalKPISelfRatingRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    员工自评
    """
    kpi = strategy_service.self_rating(
        db, kpi_id, data.actual_value, data.self_score, data.self_comment
    )
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人 KPI 不存在"
        )
    return kpi


@router.post("/personal-kpis/{kpi_id}/manager-rating", response_model=PersonalKPIResponse)
def manager_rating(
    kpi_id: int,
    data: PersonalKPIManagerRatingRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    主管评分
    """
    kpi = strategy_service.manager_rating(
        db, kpi_id, data.manager_score, data.manager_comment
    )
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人 KPI 不存在"
        )
    return kpi


@router.delete("/personal-kpis/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_personal_kpi(
    kpi_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    删除个人 KPI（软删除）
    """
    success = strategy_service.delete_personal_kpi(db, kpi_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人 KPI 不存在"
        )
    return None


# ============================================
# 分解追溯
# ============================================

@router.get("/tree/{strategy_id}", response_model=DecompositionTreeResponse)
def get_decomposition_tree(
    strategy_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取分解树
    """
    return strategy_service.get_decomposition_tree(db, strategy_id)


@router.get("/trace/{personal_kpi_id}", response_model=TraceToStrategyResponse)
def trace_to_strategy(
    personal_kpi_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    从个人 KPI 追溯到战略
    """
    result = strategy_service.trace_to_strategy(db, personal_kpi_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人 KPI 不存在"
        )
    return result


@router.get("/stats/{strategy_id}", response_model=Dict[str, Any])
def get_decomposition_stats(
    strategy_id: int,
    year: Optional[int] = Query(None, description="年度"),
    db: Session = Depends(deps.get_db),
):
    """
    获取分解统计
    """
    return strategy_service.get_decomposition_stats(db, strategy_id, year)

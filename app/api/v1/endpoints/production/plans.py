# -*- coding: utf-8 -*-
"""
生产管理模块 - 生产计划端点

包含：计划CRUD、提交、审批、发布
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.production import (
    ProductionPlanCreate,
    ProductionPlanResponse,
    ProductionPlanUpdate,
)
from app.services.production.plan_service import ProductionPlanService

router = APIRouter()


# ==================== 生产计划管理 ====================

@router.get("/production-plans", response_model=PaginatedResponse)
def read_production_plans(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    plan_type: Optional[str] = Query(None, description="计划类型筛选：MASTER/WORKSHOP"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产计划列表（主计划/车间计划）
    """
    service = ProductionPlanService(db)
    return service.list_plans(
        pagination=pagination,
        plan_type=plan_type,
        project_id=project_id,
        workshop_id=workshop_id,
        status=status,
    )


@router.post("/production-plans", response_model=ProductionPlanResponse)
def create_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: ProductionPlanCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建生产计划
    """
    service = ProductionPlanService(db)
    return service.create_plan(plan_in, current_user_id=current_user.id)


@router.get("/production-plans/{plan_id}", response_model=ProductionPlanResponse)
def read_production_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产计划详情
    """
    service = ProductionPlanService(db)
    return service.get_plan(plan_id)


@router.put("/production-plans/{plan_id}", response_model=ProductionPlanResponse)
def update_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    plan_in: ProductionPlanUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新生产计划
    """
    service = ProductionPlanService(db)
    return service.update_plan(plan_id, plan_in)


@router.put("/production-plans/{plan_id}/submit", response_model=ResponseModel)
def submit_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交计划审批
    """
    service = ProductionPlanService(db)
    return service.submit_plan(plan_id)


@router.put("/production-plans/{plan_id}/approve", response_model=ResponseModel)
def approve_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    approved: bool = Query(True, description="是否审批通过"),
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过生产计划
    """
    service = ProductionPlanService(db)
    return service.approve_plan(
        plan_id,
        approved=approved,
        approval_note=approval_note,
        current_user_id=current_user.id,
    )


@router.put("/production-plans/{plan_id}/publish", response_model=ResponseModel)
def publish_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计划发布
    """
    service = ProductionPlanService(db)
    return service.publish_plan(plan_id)

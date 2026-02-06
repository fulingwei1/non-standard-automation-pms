# -*- coding: utf-8 -*-
"""
组织/PMO 维度 API 模块

提供全局分析视角的数据访问：
- /analytics/projects/health - 项目健康度汇总
- /analytics/projects/progress - 跨项目进度对比
- /analytics/workload/overview - 全局工作量概览
- /analytics/costs/summary - 成本汇总
- /analytics/resource-conflicts - 资源冲突分析
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.project import ProjectAnalyticsService

from .resource_conflicts import router as resource_conflicts_router
from .skill_matrix import router as skill_matrix_router
from .workload import router as workload_router

router = APIRouter()

# 资源冲突分析路由
router.include_router(resource_conflicts_router, tags=["analytics-resource-conflicts"])

# 工作负载分析路由
router.include_router(workload_router, tags=["analytics-workload"])

# 技能矩阵分析路由
router.include_router(skill_matrix_router, tags=["analytics-skill-matrix"])


@router.get(
    "/projects/health",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_projects_health(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """项目健康度汇总"""
    service = ProjectAnalyticsService(db)
    data = service.get_projects_health_summary(current_user)
    return ResponseModel(data=data)


@router.get(
    "/projects/progress",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_projects_progress(
    limit: int = Query(50, ge=1, le=200, description="返回最近的项目数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """跨项目进度对比概览"""
    service = ProjectAnalyticsService(db)
    data = service.get_projects_progress_summary(current_user, limit=limit)
    return ResponseModel(data=data)


@router.get(
    "/workload/overview",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_workload_overview(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """全局工作量概览"""
    _ = current_user  # 仅用于鉴权
    service = ProjectAnalyticsService(db)
    data = service.get_workload_overview(start_date, end_date)
    return ResponseModel(data=data)


@router.get(
    "/costs/summary",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_costs_summary(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: str = Query("cost_type", description="分组字段"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """项目成本汇总"""
    service = ProjectAnalyticsService(db)
    data = service.get_costs_summary(current_user, start_date, end_date, group_by)
    return ResponseModel(data=data)

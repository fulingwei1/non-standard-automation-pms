# -*- coding: utf-8 -*-
"""
优化查询API示例

展示如何使用QueryOptimizer提升查询性能
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import deps
from app.services.database.query_optimizer import QueryOptimizer
from app.schemas.project import ProjectResponse
from app.schemas.response import Response

router = APIRouter()


@router.get("/projects/optimized", response_model=Response[List[ProjectResponse]])
def get_projects_optimized(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    status: Optional[str] = Query(None, description="项目状态"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
):
    """
    获取项目列表（优化版本）
    
    优化点：
    1. 使用joinedload避免N+1查询
    2. 预加载关联数据
    3. 添加索引提示
    4. 优化分页和排序
    """
    optimizer = QueryOptimizer(db)
    projects = optimizer.get_project_list_optimized(
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id
    )
    
    return Response.success(
        data=[ProjectResponse.from_orm(project) for project in projects],
        message="项目列表获取成功（优化版本）"
    )


@router.get("/projects/search/optimized", response_model=Response[List[ProjectResponse]])
def search_projects_optimized(
    db: Session = Depends(deps.get_db),
    keyword: str = Query(..., min_length=2, description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
):
    """
    项目搜索（优化版本）
    
    优化点：
    1. 优化LIKE查询模式
    2. 使用匹配度排序
    3. 限制搜索字段
    """
    optimizer = QueryOptimizer(db)
    projects = optimizer.search_projects_optimized(
        keyword=keyword,
        skip=skip,
        limit=limit
    )
    
    return Response.success(
        data=[ProjectResponse.from_orm(project) for project in projects],
        message="项目搜索完成（优化版本）"
    )


@router.get("/dashboard/{project_id}/optimized")
def get_project_dashboard_optimized(
    project_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取项目仪表板数据（优化版本）
    
    优化点：
    1. 单一查询获取所有数据
    2. 聚合统计减少数据传输
    3. 避免多次数据库往返
    """
    optimizer = QueryOptimizer(db)
    dashboard_data = optimizer.get_project_dashboard_data(project_id)
    
    return Response.success(
        data=dashboard_data,
        message="项目仪表板数据获取成功（优化版本）"
    )


@router.get("/alerts/statistics/optimized")
def get_alert_statistics_optimized(
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
):
    """
    获取告警统计数据（优化版本）
    
    优化点：
    1. 单个聚合查询
    2. 日期索引优化
    3. 减少数据传输量
    """
    optimizer = QueryOptimizer(db)
    stats = optimizer.get_alert_statistics_optimized(days=days)
    
    return Response.success(
        data=stats,
        message="告警统计数据获取成功（优化版本）"
    )


@router.get("/database/performance/analysis")
def analyze_database_performance(
    db: Session = Depends(deps.get_db),
):
    """
    数据库性能分析
    
    提供慢查询分析和优化建议
    """
    optimizer = QueryOptimizer(db)
    analysis = optimizer.explain_slow_queries()
    
    return Response.success(
        data=analysis,
        message="数据库性能分析完成"
    )
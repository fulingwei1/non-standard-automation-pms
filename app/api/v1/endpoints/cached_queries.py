# -*- coding: utf-8 -*-
"""
缓存优化查询API

展示如何使用Redis缓存提升API性能
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import deps
from app.services.database.query_optimizer import QueryOptimizer
from app.services.cache.business_cache import get_business_cache, invalidate_cache_on_change
from app.schemas.project import ProjectResponse
from app.schemas.response import Response

router = APIRouter()


@router.get("/projects/cached", response_model=Response[List[ProjectResponse]])
def get_projects_cached(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    status: Optional[str] = Query(None, description="项目状态"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
):
    """
    获取项目列表（缓存版本）
    
    性能优化：
    1. Redis缓存结果，避免重复查询
    2. 缓存时间：5分钟
    3. 数据变更时自动失效
    """
    business_cache = get_business_cache()
    
    # 尝试从缓存获取
    cached_projects = business_cache.get_project_list(skip, limit, status)
    if cached_projects:
        return Response.success(
            data=[ProjectResponse.from_orm(project) for project in cached_projects],
            message="项目列表获取成功（来自缓存）"
        )
    
    # 缓存未命中，从数据库查询
    optimizer = QueryOptimizer(db)
    projects = optimizer.get_project_list_optimized(
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id
    )
    
    # 缓存结果
    business_cache.set_project_list(projects, skip, limit, status)
    
    return Response.success(
        data=[ProjectResponse.from_orm(project) for project in projects],
        message="项目列表获取成功（来自数据库）"
    )


@router.get("/dashboard/{project_id}/cached")
def get_project_dashboard_cached(
    project_id: int,
    db: Session = Depends(deps.get_db),
):
    """
    获取项目仪表板数据（缓存版本）
    
    性能优化：
    1. 复杂数据聚合结果缓存
    2. 缓存时间：2分钟
    3. 项目数据变更时自动失效
    """
    business_cache = get_business_cache()
    
    # 尝试从缓存获取
    cached_dashboard = business_cache.get_project_dashboard(project_id)
    if cached_dashboard:
        return Response.success(
            data=cached_dashboard,
            message="项目仪表板数据获取成功（来自缓存）"
        )
    
    # 缓存未命中，从数据库查询
    optimizer = QueryOptimizer(db)
    dashboard_data = optimizer.get_project_dashboard_data(project_id)
    
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 缓存结果
    business_cache.set_project_dashboard(dashboard_data, project_id)
    
    return Response.success(
        data=dashboard_data,
        message="项目仪表板数据获取成功（来自数据库）"
    )


@router.get("/alerts/statistics/cached")
def get_alert_statistics_cached(
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
):
    """
    获取告警统计数据（缓存版本）
    
    性能优化：
    1. 统计数据缓存，避免重复计算
    2. 缓存时间：10分钟
    3. 告警数据变更时自动失效
    """
    business_cache = get_business_cache()
    
    # 尝试从缓存获取
    cached_stats = business_cache.get_alert_statistics(days)
    if cached_stats:
        return Response.success(
            data=cached_stats,
            message="告警统计数据获取成功（来自缓存）"
        )
    
    # 缓存未命中，从数据库查询
    optimizer = QueryOptimizer(db)
    stats = optimizer.get_alert_statistics_optimized(days=days)
    
    # 缓存结果
    business_cache.set_alert_statistics(stats, days)
    
    return Response.success(
        data=stats,
        message="告警统计数据获取成功（来自数据库）"
    )


@router.get("/projects/hot/cached")
def get_hot_projects_cached(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(deps.get_db),
):
    """
    获取热门项目（缓存版本）
    
    性能优化：
    1. 热门数据长期缓存
    2. 缓存时间：1小时
    3. 定时任务更新
    """
    business_cache = get_business_cache()
    
    # 尝试从缓存获取
    cached_hot_projects = business_cache.get_hot_projects(limit)
    if cached_hot_projects:
        return Response.success(
            data=[ProjectResponse.from_orm(project) for project in cached_hot_projects],
            message="热门项目获取成功（来自缓存）"
        )
    
    # 缓存未命中，查询热门项目
    # 这里应该是基于某种算法计算的热门项目
    optimizer = QueryOptimizer(db)
    projects = optimizer.get_project_list_optimized(limit=limit)
    
    # 缓存结果
    business_cache.set_hot_projects(projects, limit)
    
    return Response.success(
        data=[ProjectResponse.from_orm(project) for project in projects],
        message="热门项目获取成功（来自数据库）"
    )


@router.post("/cache/invalidate")
def invalidate_cache(
    cache_type: str = Query(..., description="缓存类型: project, user, alert, config"),
    object_id: Optional[int] = Query(None, description="对象ID"),
):
    """
    手动清除指定缓存
    
    通常在数据变更后调用
    """
    try:
        invalidate_cache_on_change(cache_type, object_id)
        return Response.success(
            message=f"缓存清除成功: {cache_type}{f':{object_id}' if object_id else ''}"
        )
    except Exception as e:
        return Response.error(
            message=f"缓存清除失败: {str(e)}"
        )


@router.get("/cache/stats")
def get_cache_statistics():
    """
    获取缓存统计信息
    """
    business_cache = get_business_cache()
    stats = business_cache.get_cache_stats()
    
    return Response.success(
        data=stats,
        message="缓存统计信息获取成功"
    )


@router.post("/cache/clear")
def clear_all_cache():
    """
    清除所有缓存
    
    警告：此操作会清除所有缓存数据
    """
    try:
        from app.services.cache.redis_cache import CacheManager
        CacheManager.clear_all_cache()
        return Response.success(message="所有缓存已清除")
    except Exception as e:
        return Response.error(message=f"清除缓存失败: {str(e)}")


@router.get("/search/projects/cached")
def search_projects_cached(
    db: Session = Depends(deps.get_db),
    keyword: str = Query(..., min_length=2, description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
):
    """
    项目搜索（缓存版本）
    
    性能优化：
    1. 搜索结果缓存
    2. 缓存时间：3分钟
    3. 相同搜索词复用结果
    """
    business_cache = get_business_cache()
    
    # 构建过滤条件
    filters = {"skip": skip, "limit": limit}
    
    # 尝试从缓存获取
    cached_results = business_cache.get_search_results("project", keyword, filters)
    if cached_results:
        return Response.success(
            data=[ProjectResponse.from_orm(project) for project in cached_results],
            message="项目搜索完成（来自缓存）"
        )
    
    # 缓存未命中，执行搜索
    optimizer = QueryOptimizer(db)
    projects = optimizer.search_projects_optimized(keyword, skip, limit)
    
    # 缓存搜索结果
    business_cache.set_search_results(projects, "project", keyword, filters)
    
    return Response.success(
        data=[ProjectResponse.from_orm(project) for project in projects],
        message="项目搜索完成（来自数据库）"
    )
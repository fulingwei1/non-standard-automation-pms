# -*- coding: utf-8 -*-
"""
统计服务使用示例
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query

from app.common.statistics.base import BaseStatisticsService
from app.common.statistics.dashboard import BaseDashboardService
from app.models.projects import Project

router = APIRouter()


# ========== 示例1: 使用统计服务基类 ==========

class ProjectStatisticsService(BaseStatisticsService):
    """项目统计服务"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)


# ========== 示例2: 使用Dashboard服务 ==========

class ProjectDashboardService(BaseDashboardService):
    """项目Dashboard服务"""
    
    def __init__(self, db: AsyncSession):
        stats = BaseStatisticsService(Project, db)
        super().__init__(stats, db)
    
    async def get_overview(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取项目概览（自定义）"""
        # 调用基类方法
        base_overview = await super().get_overview(filters)
        
        # 添加项目特定的统计
        # 例如：按阶段统计、按健康度统计等
        by_stage = await self.stats.count_by_field("stage", filters=filters)
        by_health = await self.stats.count_by_field("health", filters=filters)
        
        return {
            **base_overview,
            "by_stage": by_stage,
            "by_health": by_health
        }


# ========== 示例3: API端点使用 ==========

@router.get("/statistics/overview")
async def get_project_statistics(
    filters: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取项目统计概览"""
    service = ProjectStatisticsService(db)
    
    # 获取总数
    total = await service.count_total(filters=filters)
    
    # 按状态统计
    by_status = await service.count_by_status(filters=filters)
    
    # 按阶段统计
    by_stage = await service.count_by_field("stage", filters=filters)
    
    # 获取趋势
    trends = await service.get_trend("created_at", days=30, filters=filters)
    
    return {
        "total": total,
        "by_status": by_status,
        "by_stage": by_stage,
        "trends": trends
    }


@router.get("/dashboard")
async def get_project_dashboard(
    filters: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取项目Dashboard数据"""
    dashboard = ProjectDashboardService(db)
    return await dashboard.get_dashboard_data(filters=filters)


@router.get("/statistics/distribution")
async def get_distribution(
    field: str = Query(..., description="统计字段"),
    filters: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取分布数据"""
    service = ProjectStatisticsService(db)
    return await service.get_distribution(field, filters=filters)


@router.get("/statistics/trends")
async def get_trends(
    date_field: str = Query("created_at", description="日期字段"),
    days: int = Query(30, description="统计天数"),
    filters: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取趋势数据"""
    service = ProjectStatisticsService(db)
    return await service.get_trend(date_field, days=days, filters=filters)


@router.get("/statistics/summary")
async def get_summary(
    numeric_fields: Optional[str] = Query(None, description="数值字段（逗号分隔）"),
    date_field: Optional[str] = Query(None, description="日期字段"),
    filters: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取汇总统计"""
    service = ProjectStatisticsService(db)
    
    numeric_fields_list = numeric_fields.split(",") if numeric_fields else None
    
    return await service.get_summary_stats(
        numeric_fields=numeric_fields_list,
        date_field=date_field,
        filters=filters
    )

# -*- coding: utf-8 -*-
"""
Dashboard服务基类
统一所有Dashboard的实现模式
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.statistics.base import BaseStatisticsService


class BaseDashboardService:
    """Dashboard服务基类"""
    
    def __init__(
        self,
        statistics_service: BaseStatisticsService,
        db: AsyncSession
    ):
        """
        Args:
            statistics_service: 统计服务实例
            db: 数据库会话
        """
        self.stats = statistics_service
        self.db = db
    
    async def get_overview(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取概览数据
        
        子类应该重写此方法以实现特定的概览逻辑
        
        Returns:
            {
                "total": 总数,
                "active": 活跃数,
                "pending": 待处理数,
                "completed": 完成数,
                ...
            }
        """
        total = await self.stats.count_total(filters=filters)
        
        # 尝试获取状态分布
        by_status = {}
        try:
            by_status = await self.stats.count_by_status(filters=filters)
        except (ValueError, AttributeError):
            pass
        
        return {
            "total": total,
            "by_status": by_status
        }
    
    async def get_trends(
        self,
        date_field: str = "created_at",
        days: int = 30,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取趋势数据
        
        Args:
            date_field: 日期字段
            days: 统计天数
            filters: 筛选条件
        
        Returns:
            [{"date": "2026-01-01", "count": 10}, ...]
        """
        return await self.stats.get_trend(
            date_field=date_field,
            period="day",
            days=days,
            filters=filters
        )
    
    async def get_distribution(
        self,
        field: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取分布数据
        
        Args:
            field: 字段名
            filters: 筛选条件
        
        Returns:
            {
                "distribution": {值: 数量},
                "total": 总数,
                "percentages": {值: 百分比}
            }
        """
        return await self.stats.get_distribution(field, filters)
    
    async def get_summary(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取汇总数据
        
        子类应该重写此方法以实现特定的汇总逻辑
        
        Returns:
            汇总数据字典
        """
        return await self.stats.get_summary_stats(filters=filters)
    
    async def get_dashboard_data(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取完整的Dashboard数据
        
        子类可以重写此方法以自定义Dashboard结构
        
        Returns:
            {
                "overview": 概览数据,
                "trends": 趋势数据,
                "distribution": 分布数据,
                "summary": 汇总数据
            }
        """
        return {
            "overview": await self.get_overview(filters),
            "trends": await self.get_trends(filters=filters),
            "summary": await self.get_summary(filters)
        }
